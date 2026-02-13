from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.paginator import Paginator

from apps.accounts.models import Member, MemberChild
from apps.common.models import CodeValue, Setting
from apps.courses.models import Stadium, Lecture, LectureSelDay, Promotion, PromotionMember
from .models import Enrollment, EnrollmentCourse, EnrollmentBill, WaitStudent


# ──────────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────────

def _get_start_month():
    """21일 이후면 익월, 아니면 당월"""
    now = timezone.localtime()
    year, month = now.year, now.month
    if now.day > 21:
        month += 1
        if month > 12:
            year += 1
            month = 1
    return year, month


def _calc_end_dt(syear, smonth, lec_period):
    """시작년월 + 기간으로 종료년월 계산"""
    end_month = smonth + lec_period - 1
    end_year = syear
    while end_month > 12:
        end_month -= 12
        end_year += 1
    return end_year, end_month


def _get_active_promotion(child_id, use_mode):
    """자녀별 활성 프로모션 중 최대 할인 조회"""
    now = timezone.localtime()
    from django.db import models as db_models
    promo_ids = list(PromotionMember.objects.filter(
        child_id=child_id
    ).values_list('coupon_uid', flat=True))

    if not promo_ids:
        return None

    return Promotion.objects.filter(
        uid__in=promo_ids,
        is_use='T',
        use_mode=use_mode,
        start_date__lte=now,
    ).filter(
        db_models.Q(end_date__gte=now) | db_models.Q(end_date__isnull=True)
    ).order_by('-discount').first()


# ──────────────────────────────────────────────
# Step 1: 자녀선택 → 권역 → 구장 → 강좌 → 시작일
# ──────────────────────────────────────────────

@login_required
def apply_step1_view(request):
    """입단신청 Step 1"""
    children = MemberChild.objects.filter(parent=request.user)
    children_data = []
    for child in children:
        # 활성 수강 건수
        join_cnt = Enrollment.objects.filter(
            child=child, del_chk='N',
            lecture_stats__in=['LY', 'LP', 'PN'],
        ).count()
        # 종료/정지 이력
        end_chk = 1 if child.course_state in ('PAU', 'END', 'CAN') else 0
        children_data.append({
            'child': child,
            'join_cnt': join_cnt,
            'end_chk': end_chk,
        })

    # 권역 코드 목록
    locals_list = CodeValue.objects.filter(
        group__grpcode='LOCD', del_chk='N'
    ).order_by('code_desc', 'code_order')

    syear, smonth = _get_start_month()
    sym = f'{syear}{smonth:02d}'

    setting = Setting.objects.first()
    join_price = setting.join_price if setting else 0

    return render(request, 'enrollment/apply_step1.html', {
        'children_data': children_data,
        'locals_list': locals_list,
        'syear': syear,
        'smonth': f'{smonth:02d}',
        'sym': sym,
        'join_price': join_price,
        'menu': 'apply',
    })


@login_required
def ajax_load_stadiums(request):
    """AJAX: 권역별 구장 목록"""
    local_code = request.GET.get('local_code', '')
    if not local_code:
        return HttpResponse('<p>권역을 선택하세요.</p>')

    stadiums = Stadium.objects.filter(
        local_code=int(local_code), use_gbn='Y'
    ).exclude(
        sta_code__in=[4, 17, 20, 35]
    ).order_by('order_seq', 'sta_name')

    return render(request, 'enrollment/fragments/stadium_list.html', {
        'stadiums': stadiums,
    })


@login_required
def ajax_load_lectures(request):
    """AJAX: 구장별 강좌 목록 + 정원/대기 계산"""
    local_code = request.GET.get('local_code', '')
    sta_code = request.GET.get('sta_code', '')
    lecture_dt = request.GET.get('lecture_dt', '')

    if not all([local_code, sta_code, lecture_dt]):
        return HttpResponse('<p>구장을 선택하세요.</p>')

    syear = int(lecture_dt[:4])
    smonth = int(lecture_dt[4:6])

    class_groups = Lecture.objects.filter(
        use_gbn='Y', stadium__sta_code=int(sta_code)
    ).values_list('class_gbn', flat=True).distinct().order_by('class_gbn')

    result_groups = []
    for class_gbn in class_groups:
        lectures = Lecture.objects.filter(
            use_gbn='Y', stadium__sta_code=int(sta_code), class_gbn=class_gbn
        ).order_by('lecture_day', 'lecture_time', 'lec_age')

        lecture_list = []
        for lec in lectures:
            cur_cnt = EnrollmentCourse.objects.filter(
                lecture_code=lec.lecture_code,
                course_stats__in=['LY', 'LP', 'PN'],
                course_ym__year=syear, course_ym__month=smonth,
                bill_code='1001',
            ).count()
            wait_cnt = WaitStudent.objects.filter(
                lecture_code=lec.lecture_code,
                trans_gbn='N', del_chk='N',
            ).count()
            available = lec.stu_cnt - cur_cnt
            if available > 0:
                jud = 1  # 신청가능
            elif wait_cnt <= 2:
                jud = 2  # 대기가능
            else:
                jud = 3  # 신청불가

            lecture_list.append({
                'lecture': lec,
                'cur_cnt': cur_cnt,
                'jud': jud,
            })

        if lecture_list:
            result_groups.append({
                'class_gbn': class_gbn,
                'lectures': lecture_list,
            })

    return render(request, 'enrollment/fragments/lecture_list.html', {
        'result_groups': result_groups,
    })


@login_required
def ajax_course_days(request):
    """AJAX: 강좌별 수업 시작일 목록"""
    lecture_codes = request.GET.get('lecture_codes', '')
    lecture_dt = request.GET.get('lecture_dt', '')

    if not lecture_codes or not lecture_dt:
        return HttpResponse('')

    syear = int(lecture_dt[:4])
    smonth = int(lecture_dt[4:6])

    codes = [c.strip() for c in lecture_codes.split(',') if c.strip()]
    day_data = []
    for code in codes:
        try:
            lec = Lecture.objects.get(lecture_code=int(code), use_gbn='Y')
        except Lecture.DoesNotExist:
            continue
        days = list(LectureSelDay.objects.filter(
            lecture_code=int(code), syear=syear, smonth=smonth
        ).order_by('sday').values_list('sday', flat=True))
        day_data.append({
            'lecture_code': code,
            'lecture_title': lec.lecture_title,
            'days': days,
        })

    return render(request, 'enrollment/fragments/course_days.html', {
        'day_data': day_data,
    })


@login_required
def ajax_recommend_check(request):
    """AJAX: 추천인 아이디 확인"""
    check_id = request.GET.get('check_id', '')
    if not check_id or check_id == request.user.username:
        return JsonResponse({'valid': False, 'msg': '유효하지 않은 아이디입니다.'})
    exists = Member.objects.filter(username=check_id).exists()
    return JsonResponse({
        'valid': exists,
        'msg': '확인되었습니다.' if exists else '존재하지 않는 아이디입니다.',
    })


@login_required
def ajax_waitlist_add(request):
    """AJAX: 대기자 등록"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'msg': '잘못된 요청입니다.'})

    local_code = int(request.POST.get('local_code', 0))
    sta_code = int(request.POST.get('sta_code', 0))
    lecture_code = int(request.POST.get('lecture_code', 0))
    child_id = request.POST.get('child_id', '')
    child_name = request.POST.get('child_name', '')

    exists = WaitStudent.objects.filter(
        del_chk='N', lecture_code=lecture_code,
        member_id=request.user.username, child_id=child_id,
    ).exists()
    if exists:
        return JsonResponse({'success': False, 'msg': '이미 대기 등록하신 강좌입니다.'})

    wait_num = WaitStudent.objects.filter(
        del_chk='N', trans_gbn='N', lecture_code=lecture_code,
    ).count() + 1

    WaitStudent.objects.create(
        local_code=local_code, sta_code=sta_code,
        lecture_code=lecture_code,
        member_id=request.user.username,
        member_name=request.user.name,
        child_id=child_id, child_name=child_name,
        wait_seq=wait_num,
        insert_id=request.user.username,
    )
    return JsonResponse({'success': True, 'msg': f'대기 {wait_num}번으로 등록되었습니다.'})


# ──────────────────────────────────────────────
# Step 2: 프로모션/할인 확인
# ──────────────────────────────────────────────

@login_required
def apply_step2_view(request):
    """입단신청 Step 2: 선택 확인 + 프로모션"""
    if request.method != 'POST':
        return redirect('enrollment:apply_step1')

    child_id = request.POST.get('sel_child', '')
    local_code = int(request.POST.get('rad_local_code', 0))
    sta_code = int(request.POST.get('rad_sta_code', 0))
    lec_cycle = int(request.POST.get('lec_cycle', 1))
    lec_period = int(request.POST.get('lec_period', 3))
    sym = request.POST.get('sym', '')
    lecture_codes = request.POST.getlist('cbList')
    recommend_id = request.POST.get('recommend_id', '')

    # 시작일 수집
    start_days = {}
    for code in lecture_codes:
        sday = request.POST.get(f'cbDaylist_{code}', '')
        start_days[code] = sday

    child = MemberChild.objects.filter(child_id=child_id, parent=request.user).first()
    if not child:
        return redirect('enrollment:apply_step1')

    end_chk = 1 if child.course_state in ('PAU', 'END', 'CAN') else 0

    syear = int(sym[:4])
    smonth = int(sym[4:6])

    # 강좌별 수업 횟수 및 금액 계산
    lecture_details = []
    total_lecture_price = 0

    for code in lecture_codes:
        try:
            lec = Lecture.objects.get(lecture_code=int(code), use_gbn='Y')
        except Lecture.DoesNotExist:
            continue

        sday = int(start_days.get(code, 1) or 1)

        total_count = 0
        for offset in range(lec_period):
            m = smonth + offset
            y = syear
            while m > 12:
                m -= 12
                y += 1
            if offset == 0:
                count = LectureSelDay.objects.filter(
                    lecture_code=int(code), syear=y, smonth=m, sday__gte=sday
                ).count()
            else:
                count = LectureSelDay.objects.filter(
                    lecture_code=int(code), syear=y, smonth=m
                ).count()
            total_count += count

        price = lec.lec_price * total_count
        total_lecture_price += price

        lecture_details.append({
            'code': code,
            'title': lec.lecture_title,
            'day_display': lec.get_day_display(),
            'time': lec.lecture_time,
            'lec_price': lec.lec_price,
            'count': total_count,
            'total_price': price,
            'start_day': sday,
        })

    setting = Setting.objects.first()
    join_price = 0 if end_chk > 0 else (setting.join_price if setting else 0)

    # 세션 저장
    request.session['enrollment_data'] = {
        'child_id': child_id,
        'local_code': local_code,
        'sta_code': sta_code,
        'lec_cycle': lec_cycle,
        'lec_period': lec_period,
        'sym': sym,
        'syear': syear,
        'smonth': smonth,
        'lecture_codes': lecture_codes,
        'start_days': start_days,
        'recommend_id': recommend_id,
        'end_chk': end_chk,
        'join_price': join_price,
        'total_lecture_price': total_lecture_price,
    }

    # 표시용 이름
    local_name = CodeValue.objects.filter(
        group__grpcode='LOCD', subcode=local_code
    ).values_list('code_name', flat=True).first() or ''
    sta = Stadium.objects.filter(sta_code=sta_code).first()
    sta_name = sta.sta_name if sta else ''

    return render(request, 'enrollment/apply_step2.html', {
        'child': child,
        'local_name': local_name,
        'sta_name': sta_name,
        'sta_code': sta_code,
        'lecture_details': lecture_details,
        'lec_cycle': lec_cycle,
        'lec_period': lec_period,
        'sym': sym,
        'join_price': join_price,
        'end_chk': end_chk,
        'total_lecture_price': total_lecture_price,
        'recommend_id': recommend_id,
        'menu': 'apply',
    })


@login_required
def ajax_load_promotions(request):
    """AJAX: 프로모션/할인 목록"""
    child_id = request.GET.get('child_id', '')
    end_chk = int(request.GET.get('end_chk', 0))
    lec_cycle = int(request.GET.get('lec_cycle', 1))
    lec_period = int(request.GET.get('lec_period', 3))
    lecture_codes = request.GET.get('lecture_codes', '')

    discounts = {}

    # 1. 교육용품비 할인
    if end_chk > 0:
        discounts['eq'] = {'title': '재입단시 교육용품비 면제', 'amount': 0, 'id': ''}
    else:
        promo = _get_active_promotion(child_id, use_mode=1)
        discounts['eq'] = {
            'title': promo.title if promo else '해당내역이 없습니다.',
            'amount': promo.discount if promo else 0,
            'id': str(promo.uid) if promo else '',
        }

    # 2. 수강료 할인
    promo = _get_active_promotion(child_id, use_mode=2)
    discounts['tu'] = {
        'title': promo.title if promo else '해당내역이 없습니다.',
        'amount': promo.discount if promo else 0,
        'id': str(promo.uid) if promo else '',
    }

    # 3. 결제금액 할인
    promo = _get_active_promotion(child_id, use_mode=3)
    discounts['py'] = {
        'title': promo.title if promo else '해당내역이 없습니다.',
        'amount': promo.discount if promo else 0,
        'id': str(promo.uid) if promo else '',
    }

    # 4. 3개월 선납 할인
    discounts['py3'] = {'title': '해당내역이 없습니다.', 'amount': 0, 'id': ''}

    # 5. 피추천 할인
    discounts['rd'] = {'title': '해당내역이 없습니다.', 'amount': 0, 'id': ''}

    # 6. 2회이상 수업 할인
    discounts['o2'] = {'title': '해당내역이 없습니다.', 'amount': 0, 'id': ''}
    if lecture_codes and lec_cycle >= 2:
        codes = [int(c.strip()) for c in lecture_codes.split(',') if c.strip()]
        dc_values = Lecture.objects.filter(lecture_code__in=codes)
        if lec_cycle == 2:
            dc = min((l.dc_2 for l in dc_values if l.dc_2 > 0), default=0)
        elif lec_cycle >= 3:
            dc = min((l.dc_3 for l in dc_values if l.dc_3 > 0), default=0)
        else:
            dc = 0
        if dc > 0:
            discounts['o2'] = {
                'title': f'주{lec_cycle}회 할인',
                'amount': dc * lec_period,
                'id': 'auto_dc',
            }

    return render(request, 'enrollment/fragments/promotion_list.html', {
        'discounts': discounts,
        'end_chk': end_chk,
    })


# ──────────────────────────────────────────────
# Step 3: 결제 확인
# ──────────────────────────────────────────────

@login_required
def apply_step3_view(request):
    """입단신청 Step 3: 결제 확인"""
    if request.method != 'POST':
        return redirect('enrollment:apply_step1')

    data = request.session.get('enrollment_data')
    if not data:
        return redirect('enrollment:apply_step1')

    # 할인 값 수집
    eq_discount = int(request.POST.get('EQ_Discount', 0) or 0)
    tu_discount = int(request.POST.get('Tu_Discount', 0) or 0)
    py_discount = int(request.POST.get('PY_Discount', 0) or 0)
    py3_discount = int(request.POST.get('PY3_Discount', 0) or 0)
    rd_discount = int(request.POST.get('RD_Discount', 0) or 0)
    o2_discount = int(request.POST.get('O2_Discount', 0) or 0)

    # 할인 ID 수집
    eq_discount_id = request.POST.get('EQ_Discount_id', '')
    tu_discount_id = request.POST.get('Tu_Discount_id', '')
    py_discount_id = request.POST.get('PY_Discount_id', '')
    o2_discount_id = request.POST.get('O2_Discount_id', '')

    data['eq_discount'] = eq_discount
    data['tu_discount'] = tu_discount
    data['py_discount'] = py_discount
    data['py3_discount'] = py3_discount
    data['rd_discount'] = rd_discount
    data['o2_discount'] = o2_discount
    data['discount1_id'] = eq_discount_id
    data['discount2_id'] = tu_discount_id
    data['discount3_id'] = py_discount_id
    data['discount6_id'] = o2_discount_id
    request.session['enrollment_data'] = data

    total_lecture_price = data['total_lecture_price']
    join_price = data['join_price']
    lec_cycle = data['lec_cycle']
    lec_period = data['lec_period']

    total_discount = (
        eq_discount +
        (tu_discount * lec_period * lec_cycle) +
        py_discount + py3_discount + rd_discount + o2_discount
    )
    payment_price = max(total_lecture_price + join_price - total_discount, 0)

    # KCP 설정
    sta_code = data['sta_code']
    now = timezone.localtime()
    order_idxx = now.strftime('%Y%m%d%H%M%S') + request.user.username + '1' + data['child_id']

    sta = Stadium.objects.filter(sta_code=sta_code).first()
    sta_name = sta.sta_name if sta else ''
    child = MemberChild.objects.filter(child_id=data['child_id']).first()
    good_name = f"{sta_name}^{request.user.name}^{child.name if child else ''}^[입단신청]"

    data['payment_price'] = payment_price
    data['order_idxx'] = order_idxx
    data['good_name'] = good_name
    data['total_discount'] = total_discount
    request.session['enrollment_data'] = data

    allow_installment = payment_price >= 50000

    # KCP 가맹점 코드
    if sta_code == 32:
        kcp_site_cd = 'AJVBN'
    else:
        kcp_site_cd = 'A8BDH'

    return render(request, 'enrollment/apply_step3.html', {
        'data': data,
        'payment_price': payment_price,
        'total_lecture_price': total_lecture_price,
        'join_price': join_price,
        'total_discount': total_discount,
        'eq_discount': eq_discount,
        'tu_discount': tu_discount * lec_period * lec_cycle,
        'py_discount': py_discount,
        'o2_discount': o2_discount,
        'order_idxx': order_idxx,
        'good_name': good_name,
        'sta_name': sta_name,
        'child': child,
        'kcp_site_cd': kcp_site_cd,
        'allow_installment': allow_installment,
        'user': request.user,
        'menu': 'apply',
    })


# ──────────────────────────────────────────────
# 결제내역 (마이페이지)
# ──────────────────────────────────────────────

@login_required
def payment_history_view(request):
    """결제내역 조회"""
    enrollments = Enrollment.objects.filter(
        member=request.user, del_chk='N',
    ).select_related('child').order_by('-id')

    paginator = Paginator(enrollments, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'enrollment/payment_history.html', {
        'page_obj': page_obj,
        'menu': 'payment_history',
    })
