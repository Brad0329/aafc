import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.models import MemberChild
from apps.courses.models import Lecture, LectureSelDay
from apps.enrollment.models import Enrollment, EnrollmentCourse, EnrollmentBill
from apps.notifications import sms_events
from . import toss
from .models import PaymentKCP, PaymentFail, PaymentToss


@csrf_exempt
@login_required
def kcp_return_view(request):
    """KCP 결제 결과 콜백 처리 (※ Toss 전환으로 비활성 - URL 미연결, 코드 보존)"""
    if request.method != 'POST':
        return redirect('enrollment:apply_step1')

    res_cd = request.POST.get('res_cd', '')
    res_msg = request.POST.get('res_msg', '')

    data = request.session.get('enrollment_data')
    if not data:
        return render(request, 'payments/payment_fail.html', {
            'res_msg': '세션이 만료되었습니다. 다시 신청해주세요.',
        })

    if res_cd == '0000':
        # 결제 성공
        try:
            kcp_pay_method = request.POST.get('use_pay_method', '100000000000')
            pay_method = 'R' if kcp_pay_method.startswith('0100') else 'CARD'
            enrollment = _create_enrollment(request, data, pay_method)
            _create_payment_log(request, data, enrollment)
            # 세션 정리
            del request.session['enrollment_data']
            return render(request, 'payments/payment_success.html', {
                'enrollment': enrollment,
            })
        except Exception as e:
            # 입단 생성 실패 시 실패 로그
            _create_fail_log(request, data, res_cd='SYS_ERR', res_msg=str(e))
            return render(request, 'payments/payment_fail.html', {
                'res_msg': f'처리 중 오류가 발생하였습니다: {e}',
            })
    else:
        # 결제 실패
        _create_fail_log(request, data, res_cd=res_cd, res_msg=res_msg)
        return render(request, 'payments/payment_fail.html', {
            'res_msg': res_msg or '결제에 실패하였습니다.',
        })


@transaction.atomic
def _create_enrollment(request, data, pay_method='CARD'):
    """입단 레코드 + 청구내역 + 수강과정 생성 (트랜잭션). pay_method: 'CARD'/'R'/'VACCT'"""
    now = timezone.localtime()
    user = request.user

    child_id = data['child_id']
    sta_code = data['sta_code']
    lec_cycle = data['lec_cycle']
    lec_period = data['lec_period']
    syear = data['syear']
    smonth = data['smonth']
    lecture_codes = data['lecture_codes']
    start_days = data['start_days']
    recommend_id = data.get('recommend_id', '')
    end_chk = data.get('end_chk', 0)
    join_price = data.get('join_price', 0)
    payment_price = data.get('payment_price', 0)
    total_lecture_price = data.get('total_lecture_price', 0)

    # 할인
    eq_discount = data.get('eq_discount', 0)
    tu_discount = data.get('tu_discount', 0)
    py_discount = data.get('py_discount', 0)
    o2_discount = data.get('o2_discount', 0)

    # 종료년월 계산
    end_month = smonth + lec_period - 1
    end_year = syear
    while end_month > 12:
        end_month -= 12
        end_year += 1
    start_dt = f'{syear}{smonth:02d}'
    end_dt = f'{end_year}{end_month:02d}'

    # 신청구분 결정
    apply_gubun = 'RE' if end_chk > 0 else 'NEW'

    # 1. Enrollment 생성
    enrollment = Enrollment.objects.create(
        member=user,
        child_id=child_id,
        pay_stats='PY',
        pay_method=pay_method,
        pay_price=payment_price,
        pay_dt=now,
        lecture_stats='LY',
        lec_cycle=lec_cycle,
        lec_period=lec_period,
        start_dt=start_dt,
        end_dt=end_dt,
        apply_gubun=apply_gubun,
        source_gubun='01',
        recommend_id=recommend_id,
        discount1_id=data.get('discount1_id', ''),
        discount1_price=eq_discount,
        discount2_id=data.get('discount2_id', ''),
        discount2_price=tu_discount * lec_period * lec_cycle,
        discount3_id=data.get('discount3_id', ''),
        discount3_price=py_discount,
        discount6_id=data.get('discount6_id', ''),
        discount6_price=o2_discount,
        del_chk='N',
        insert_id=user.username,
    )

    # 2. EnrollmentBill 생성
    # 2-1. 수업료 (1001)
    EnrollmentBill.objects.create(
        enrollment=enrollment,
        bill_code='1001',
        bill_desc='수업료',
        bill_amt=total_lecture_price,
        pay_stats='PY',
        insert_id=user.username,
    )

    # 2-2. 교육용품비 (2001)
    if join_price > 0:
        EnrollmentBill.objects.create(
            enrollment=enrollment,
            bill_code='2001',
            bill_desc='교육용품비',
            bill_amt=join_price,
            pay_stats='PY',
            insert_id=user.username,
        )

    # 2-3. 교육용품 할인 (2002)
    if eq_discount > 0:
        EnrollmentBill.objects.create(
            enrollment=enrollment,
            bill_code='2002',
            bill_desc='교육용품할인',
            bill_amt=-eq_discount,
            pay_stats='PY',
            insert_id=user.username,
        )

    # 2-4. 수강료 할인 (1003)
    total_tu_discount = tu_discount * lec_period * lec_cycle
    if total_tu_discount > 0:
        EnrollmentBill.objects.create(
            enrollment=enrollment,
            bill_code='1003',
            bill_desc='수강료할인',
            bill_amt=-total_tu_discount,
            pay_stats='PY',
            insert_id=user.username,
        )

    # 2-5. 결제금액 할인 (1003 계열)
    if py_discount > 0:
        EnrollmentBill.objects.create(
            enrollment=enrollment,
            bill_code='1003',
            bill_desc='결제금액할인',
            bill_amt=-py_discount,
            pay_stats='PY',
            insert_id=user.username,
        )

    # 2-6. 다회할인 (1004)
    if o2_discount > 0:
        EnrollmentBill.objects.create(
            enrollment=enrollment,
            bill_code='1004',
            bill_desc=f'주{lec_cycle}회 할인',
            bill_amt=-o2_discount,
            pay_stats='PY',
            insert_id=user.username,
        )

    # 3. EnrollmentCourse 생성 (월별 × 강좌별)
    for code in lecture_codes:
        try:
            lec = Lecture.objects.get(lecture_code=int(code), use_gbn='Y')
        except Lecture.DoesNotExist:
            continue

        sday = int(start_days.get(code, 1) or 1)

        for offset in range(lec_period):
            m = smonth + offset
            y = syear
            while m > 12:
                m -= 12
                y += 1

            # 해당 월 수업 횟수 및 금액
            if offset == 0:
                count = LectureSelDay.objects.filter(
                    lecture_code=int(code), syear=y, smonth=m, sday__gte=sday
                ).count()
            else:
                count = LectureSelDay.objects.filter(
                    lecture_code=int(code), syear=y, smonth=m
                ).count()

            course_amt = lec.lec_price * count

            # 시작일 (첫 달만 실제 시작일)
            if offset == 0:
                start_ymd = datetime.date(y, m, sday)
            else:
                start_ymd = datetime.date(y, m, 1)

            EnrollmentCourse.objects.create(
                enrollment=enrollment,
                bill_code='1001',
                course_ym=datetime.date(y, m, 1),
                course_ym_amt=course_amt,
                lecture_code=int(code),
                start_ymd=start_ymd,
                course_stats='LY',
            )

    # 4. MemberChild 수강상태 업데이트
    MemberChild.objects.filter(child_id=child_id).update(course_state='ING')

    return enrollment


def _create_payment_log(request, data, enrollment):
    """KCP 결제 성공 로그 생성"""
    PaymentKCP.objects.create(
        req_tx=request.POST.get('req_tx', 'pay'),
        use_pay_method=request.POST.get('use_pay_method', ''),
        bsucc='true',
        res_cd=request.POST.get('res_cd', '0000'),
        res_msg=request.POST.get('res_msg', ''),
        amount=data.get('payment_price', 0),
        ordr_idxx=data.get('order_idxx', ''),
        tno=request.POST.get('tno', ''),
        good_mny=data.get('payment_price', 0),
        good_name=data.get('good_name', ''),
        buyr_name=request.user.name,
        buyr_tel1=request.user.phone,
        buyr_mail=request.user.email,
        app_time=request.POST.get('app_time', ''),
        card_cd=request.POST.get('card_cd', ''),
        card_name=request.POST.get('card_name', ''),
        app_no=request.POST.get('app_no', ''),
        noinf=request.POST.get('noinf', ''),
        quota=request.POST.get('quota', ''),
        bank_name=request.POST.get('bank_name', ''),
        bank_code=request.POST.get('bank_code', ''),
        depositor=request.POST.get('depositor', ''),
        account=request.POST.get('account', ''),
        va_date=request.POST.get('va_date', ''),
        pay_seq=enrollment.id,
        member_num=request.user.username,
        pg_gbn='KCP',
    )


def _create_fail_log(request, data, res_cd='', res_msg=''):
    """결제 실패 로그 생성"""
    PaymentFail.objects.create(
        req_tx=request.POST.get('req_tx', 'pay'),
        use_pay_method=request.POST.get('use_pay_method', ''),
        res_cd=res_cd,
        res_msg=res_msg,
        amount=data.get('payment_price', 0),
        ordr_idxx=data.get('order_idxx', ''),
        good_name=data.get('good_name', ''),
        buyr_name=request.user.name if request.user.is_authenticated else '',
        member_num=request.user.username if request.user.is_authenticated else '',
    )


# ──────────────────────────────────────────────────────────────
# Toss Payments (수강신청)
# ──────────────────────────────────────────────────────────────

@login_required
def toss_enrollment_success(request):
    """Toss 수강신청 결제 성공 콜백 (GET 리다이렉트 → 승인 confirm → 입단 생성)"""
    payment_key = request.GET.get('paymentKey', '')
    order_id = request.GET.get('orderId', '')
    amount = request.GET.get('amount', '')

    data = request.session.get('enrollment_data')
    if not data:
        return render(request, 'payments/payment_fail.html', {
            'res_msg': '세션이 만료되었습니다. 다시 신청해주세요.',
        })

    expected_order = data.get('order_idxx', '')
    expected_amount = int(data.get('payment_price', 0) or 0)

    # 위변조 방지: orderId / amount 를 서버 보관값과 대조 (정수 비교)
    try:
        amount_int = int(amount)
    except (ValueError, TypeError):
        amount_int = -1
    if order_id != expected_order or amount_int != expected_amount:
        _create_fail_log(request, data, res_cd='AMOUNT_MISMATCH', res_msg='주문정보 불일치')
        return render(request, 'payments/payment_fail.html', {
            'res_msg': '주문 정보가 일치하지 않습니다. 다시 시도해주세요.',
        })

    # 멱등성: 이미 승인된 주문이면 중복 처리 방지
    existing = PaymentToss.objects.filter(order_id=order_id).first()
    if existing:
        request.session.pop('enrollment_data', None)
        enrollment = Enrollment.objects.filter(id=existing.pay_seq).first()
        return render(request, 'payments/payment_success.html', {'enrollment': enrollment})

    # Toss 승인 확정
    http_code, confirm_json = toss.confirm(payment_key, order_id, expected_amount)
    if http_code != 200:
        _create_fail_log(request, data,
                         res_cd=confirm_json.get('code', 'CONFIRM_FAIL'),
                         res_msg=confirm_json.get('message', '결제 승인 실패'))
        return render(request, 'payments/payment_fail.html', {
            'res_msg': confirm_json.get('message', '결제 승인에 실패하였습니다.'),
        })

    # 승인 상태/금액 최종 검증 (가상계좌 미입금 등 미완결 결제 방어)
    if confirm_json.get('status') != 'DONE' or int(confirm_json.get('totalAmount', 0) or 0) != expected_amount:
        _create_fail_log(request, data,
                         res_cd=confirm_json.get('status', 'NOT_DONE'),
                         res_msg='결제가 완료되지 않았습니다.')
        return render(request, 'payments/payment_fail.html', {
            'res_msg': '결제가 정상적으로 완료되지 않았습니다.',
        })

    pay_method, use_pay_method = toss.method_to_codes(confirm_json.get('method', ''))

    try:
        with transaction.atomic():
            # 멱등 마커 선점 (order_id unique) — 동시/중복 콜백 시 이중 입단 방지
            log, created = PaymentToss.objects.get_or_create(
                order_id=order_id,
                defaults={
                    'good_name': data.get('good_name', ''),
                    'pay_seq': 0,
                    'member_num': request.user.username,
                    'buyr_name': request.user.name,
                    'pg_gbn': 'TOSS',
                    **toss.build_log_kwargs(confirm_json, http_code, use_pay_method),
                },
            )
            if not created:
                enrollment = Enrollment.objects.filter(id=log.pay_seq).first()
                request.session.pop('enrollment_data', None)
                return render(request, 'payments/payment_success.html', {'enrollment': enrollment})

            enrollment = _create_enrollment(request, data, pay_method)
            log.pay_seq = enrollment.id
            log.save(update_fields=['pay_seq'])
    except Exception as e:
        # 승인됐으나 처리 실패 → Toss 보상 취소 (결제-입단 불일치 방지)
        toss.cancel(payment_key, '입단 처리 실패로 자동 취소')
        _create_fail_log(request, data, res_cd='SYS_ERR', res_msg=str(e))
        return render(request, 'payments/payment_fail.html', {
            'res_msg': f'처리 중 오류로 결제가 취소되었습니다: {e}',
        })

    request.session.pop('enrollment_data', None)
    # [자동SMS] 결제완료 회원 LMS + 신규입단 코치 알림 (원본 ex_proc/apply_proc)
    sms_events.enrollment_paid(enrollment)
    return render(request, 'payments/payment_success.html', {'enrollment': enrollment})


@login_required
def toss_enrollment_fail(request):
    """Toss 수강신청 결제 실패/취소 콜백 (GET)"""
    code = request.GET.get('code', '')
    message = request.GET.get('message', '')
    data = request.session.get('enrollment_data')
    if data:
        _create_fail_log(request, data, res_cd=code, res_msg=message)
    return render(request, 'payments/payment_fail.html', {
        'res_msg': message or '결제가 취소되었습니다.',
    })


# ============================================================
# 수강료 결제 (마이페이지) — 원본 mypage payment_new.asp
#   회원의 결제대기(PP) 입단을 Toss로 결제 → 확정(PY/LY).
#   원본과 동일하게 가장 오래된 PP 입단 1건씩 결제.
# ============================================================
@login_required
def tuition_payment(request):
    """수강료 결제 화면 — 결제대기 입단 1건 + Toss 결제."""
    member = request.user
    enr = (Enrollment.objects.filter(member_id=member.username, pay_stats='PP')
           .exclude(lecture_stats='LN').order_by('id').first())

    ctx = {'login_ex': 'N'}
    if enr:
        bills = list(EnrollmentBill.objects.filter(enrollment=enr, pay_stats='PP'))
        join_price = sum(b.bill_amt for b in bills if b.bill_code.startswith('2'))
        lec_price = sum(b.bill_amt for b in bills if b.bill_code.startswith('1'))
        pay_price = join_price + lec_price

        child = MemberChild.objects.filter(child_id=enr.child_id).first()
        child_name = child.name if child else enr.child_id

        courses = list(EnrollmentCourse.objects.filter(enrollment=enr, bill_code='1001')
                       .order_by('lecture_code', '-course_ym'))
        lec_codes = set(c.lecture_code for c in courses)
        lec_map = {l.lecture_code: l for l in
                   Lecture.objects.filter(lecture_code__in=lec_codes).select_related('stadium')}
        course_rows, sta_code = [], 0
        for c in courses:
            l = lec_map.get(c.lecture_code)
            if not l:
                continue
            if l.stadium:
                sta_code = l.stadium.sta_code
            cnt = 0
            if c.start_ymd:
                cnt = LectureSelDay.objects.filter(
                    lecture_code=c.lecture_code, syear=c.start_ymd.year,
                    smonth=c.start_ymd.month, sday__gte=c.start_ymd.day,
                ).count()
            course_rows.append({
                'course_ym': c.course_ym.strftime('%Y-%m') if c.course_ym else '',
                'sta_name': (l.stadium.sta_nickname or l.stadium.sta_name) if l.stadium else '',
                'lecture_title': l.lecture_title,
                'cnt': cnt,
            })

        shuttle = next((b for b in bills if b.bill_code == '1009'), None)
        order_id = timezone.localtime().strftime('%Y%m%d') + str(enr.id).zfill(8)
        order_name = f'[{enr.id}] 수강료결제 ({child_name})'
        request.session['tuition_pay'] = {
            'enrollment_id': enr.id, 'order_id': order_id, 'amount': pay_price,
        }
        ctx.update({
            'login_ex': 'Y', 'enrollment': enr, 'child_name': child_name,
            'join_price': join_price, 'lec_price': lec_price, 'pay_price': pay_price,
            'course_rows': course_rows, 'sta_code': sta_code,
            'shuttle_desc': shuttle.bill_desc if shuttle else '',
            'order_id': order_id, 'order_name': order_name,
            'toss_client_key': settings.TOSS_CLIENT_KEY,
        })
    return render(request, 'accounts/mypage_payment.html', ctx)


@login_required
def tuition_payment_success(request):
    """수강료 결제 성공 콜백 — Toss 승인 확정 → 입단 PY/LY 확정."""
    payment_key = request.GET.get('paymentKey', '')
    order_id = request.GET.get('orderId', '')
    amount = request.GET.get('amount', '')

    data = request.session.get('tuition_pay')
    if not data:
        return render(request, 'payments/payment_fail.html',
                      {'res_msg': '세션이 만료되었습니다. 다시 시도해주세요.'})

    expected_order = data.get('order_id', '')
    expected_amount = int(data.get('amount', 0) or 0)
    try:
        amount_int = int(amount)
    except (ValueError, TypeError):
        amount_int = -1
    if order_id != expected_order or amount_int != expected_amount:
        return render(request, 'payments/payment_fail.html',
                      {'res_msg': '주문 정보가 일치하지 않습니다. 다시 시도해주세요.'})

    # 멱등성: 이미 처리된 주문
    if PaymentToss.objects.filter(order_id=order_id).exists():
        request.session.pop('tuition_pay', None)
        enr = Enrollment.objects.filter(id=data['enrollment_id']).first()
        return render(request, 'payments/payment_success.html', {'enrollment': enr})

    http_code, confirm_json = toss.confirm(payment_key, order_id, expected_amount)
    if http_code != 200:
        return render(request, 'payments/payment_fail.html',
                      {'res_msg': confirm_json.get('message', '결제 승인에 실패하였습니다.')})
    if confirm_json.get('status') != 'DONE' or int(confirm_json.get('totalAmount', 0) or 0) != expected_amount:
        return render(request, 'payments/payment_fail.html',
                      {'res_msg': '결제가 정상적으로 완료되지 않았습니다.'})

    pay_method, use_pay_method = toss.method_to_codes(confirm_json.get('method', ''))
    try:
        with transaction.atomic():
            log, created = PaymentToss.objects.get_or_create(
                order_id=order_id,
                defaults={
                    'good_name': data.get('order_name', '수강료결제'),
                    'pay_seq': data['enrollment_id'],
                    'member_num': request.user.username,
                    'buyr_name': request.user.name,
                    'pg_gbn': 'TOSS',
                    **toss.build_log_kwargs(confirm_json, http_code, use_pay_method),
                },
            )
            if not created:
                request.session.pop('tuition_pay', None)
                enr = Enrollment.objects.filter(id=data['enrollment_id']).first()
                return render(request, 'payments/payment_success.html', {'enrollment': enr})

            enr = Enrollment.objects.filter(
                id=data['enrollment_id'], member_id=request.user.username, pay_stats='PP'
            ).first()
            if not enr:
                raise ValueError('결제 대상 입단정보가 없습니다.')
            # 확정 처리: 결제완료(PY)·수강확정(LY)
            enr.pay_stats = 'PY'
            enr.lecture_stats = 'LY'
            enr.pay_method = pay_method
            enr.pay_dt = timezone.now()
            enr.save(update_fields=['pay_stats', 'lecture_stats', 'pay_method', 'pay_dt'])
            EnrollmentBill.objects.filter(enrollment=enr, pay_stats='PP').update(pay_stats='PY')
            EnrollmentCourse.objects.filter(enrollment=enr).update(course_stats='LY')
    except Exception as e:
        # 승인됐으나 처리 실패 → Toss 보상 취소
        toss.cancel(payment_key, '수강료결제 처리 실패로 자동 취소')
        return render(request, 'payments/payment_fail.html',
                      {'res_msg': f'처리 중 오류로 결제가 취소되었습니다: {e}'})

    request.session.pop('tuition_pay', None)
    # [자동SMS] 수강료결제 완료 회원 LMS (원본 ex_proc). 신규입단 아님 → 코치알림 없음
    sms_events.enrollment_paid(enr, pay_price=expected_amount, notify_coach=False)
    return render(request, 'payments/payment_success.html', {'enrollment': enr})


@login_required
def tuition_payment_fail(request):
    """수강료 결제 실패/취소 콜백."""
    request.session.pop('tuition_pay', None)
    msg = request.GET.get('message', '') or '결제가 취소되었습니다.'
    return render(request, 'payments/payment_fail.html', {'res_msg': msg})
