import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Value, IntegerField, F
from django.db.models.functions import Coalesce
from .models import OfficeUser, OfficeLoginHistory
from .decorators import office_login_required, office_permission_required
from apps.notifications.models import OfficeNotification, SMSLog
from apps.common.models import CodeGroup, CodeValue
from apps.points.models import PointConfig, PointHistory
from apps.courses.models import Coach
from apps.accounts.models import Member, MemberChild, OutMember
from apps.enrollment.models import Enrollment, EnrollmentCourse


def login_view(request):
    """관리자 로그인"""
    if request.session.get('office_user'):
        return redirect('office_main')

    error = ''
    if request.method == 'POST':
        login_id = request.POST.get('login_id', '').strip()
        login_pwd = request.POST.get('login_pwd', '').strip()

        if not login_id or not login_pwd:
            error = '아이디와 비밀번호를 입력해주세요.'
        else:
            try:
                user = OfficeUser.objects.get(office_id=login_id, del_chk='N')
                # SHA256 해시 비교
                hashed = hashlib.sha256(login_pwd.encode('utf-8')).hexdigest()
                if user.office_pwd == hashed:
                    # 세션에 관리자 정보 저장
                    request.session['office_user'] = {
                        'office_code': user.office_code,
                        'office_id': user.office_id,
                        'office_name': user.office_name,
                        'power_level': user.power_level or '',
                        'coach_code': user.coach_code or '',
                    }
                    # 로그인 이력
                    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
                    if not ip:
                        ip = request.META.get('REMOTE_ADDR', '')
                    OfficeLoginHistory.objects.create(
                        office_id=user.office_id,
                        login_ip=ip,
                    )
                    return redirect('office_main')
                else:
                    error = '비밀번호가 일치하지 않습니다.'
            except OfficeUser.DoesNotExist:
                error = '존재하지 않는 관리자 아이디입니다.'

    return render(request, 'ba_office/login.html', {'error': error})


def logout_view(request):
    """관리자 로그아웃"""
    if 'office_user' in request.session:
        del request.session['office_user']
    return redirect('office_login')


@office_login_required
def main_view(request):
    """관리자 메인 대시보드"""
    notices = OfficeNotification.objects.filter(del_chk='N').order_by('-no_seq')
    return render(request, 'ba_office/main.html', {
        'notices': notices,
    })


# ============================================================
# 시스템관리 > 관리자 관리
# ============================================================

@office_login_required
@office_permission_required('A')
def ofuser_list(request):
    """관리자 목록"""
    users = OfficeUser.objects.filter(del_chk='N').order_by('office_name')
    return render(request, 'ba_office/manage/ofuser_list.html', {
        'users': users,
    })


@office_login_required
@office_permission_required('A')
def ofuser_write(request):
    """관리자 등록"""
    coaches = Coach.objects.filter(use_gbn='Y').order_by('coach_name')

    if request.method == 'POST':
        office_name = request.POST.get('office_name', '').strip()
        office_realname = request.POST.get('office_realname', '').strip()
        office_id = request.POST.get('office_id', '').strip()
        office_pwd = request.POST.get('office_pwd', '').strip()
        office_pwd_con = request.POST.get('office_pwd_con', '').strip()
        office_part = request.POST.get('office_part', '').strip()
        office_mail = request.POST.get('office_mail', '').strip()
        office_hp = request.POST.get('office_hp', '').strip()
        office_auth_list = request.POST.getlist('office_auth')
        use_auth = request.POST.get('use_auth', 'W')
        coach_code = request.POST.get('coach_code', '').strip()

        error = ''
        if not office_name:
            error = '표시명을 입력해주세요.'
        elif not office_id or len(office_id) < 6:
            error = '아이디는 6자 이상 입력해주세요.'
        elif not office_pwd or len(office_pwd) < 10:
            error = '비밀번호는 10자 이상 입력해주세요.'
        elif office_pwd != office_pwd_con:
            error = '비밀번호가 일치하지 않습니다.'
        elif office_id == office_pwd:
            error = '아이디와 비밀번호는 같을 수 없습니다.'
        elif not office_hp:
            error = '연락처를 입력해주세요.'
        elif not office_auth_list:
            error = '메뉴 권한을 1개 이상 선택해주세요.'
        elif OfficeUser.objects.filter(office_id=office_id).exists():
            error = '이미 사용 중인 아이디입니다.'
        elif coach_code and OfficeUser.objects.filter(coach_code=coach_code, del_chk='N').exists():
            error = '이미 등록된 코치코드입니다.'

        if error:
            return render(request, 'ba_office/manage/ofuser_write.html', {
                'error': error,
                'coaches': coaches,
                'form_data': request.POST,
            })

        power_level = ','.join(office_auth_list)
        hashed_pwd = hashlib.sha256(office_pwd.encode('utf-8')).hexdigest()

        OfficeUser.objects.create(
            office_name=office_name,
            office_realname=office_realname,
            office_id=office_id,
            office_pwd=hashed_pwd,
            office_part=office_part,
            office_mail=office_mail,
            office_hp=office_hp,
            power_level=power_level,
            use_auth=use_auth,
            coach_code=coach_code,
            del_chk='N',
            insert_dt=timezone.now(),
        )
        return redirect('office_ofuser_list')

    return render(request, 'ba_office/manage/ofuser_write.html', {
        'coaches': coaches,
    })


@office_login_required
@office_permission_required('A')
def ofuser_modify(request, pk):
    """관리자 수정"""
    user = get_object_or_404(OfficeUser, office_code=pk, del_chk='N')
    coaches = Coach.objects.filter(use_gbn='Y').order_by('coach_name')

    if request.method == 'POST':
        office_name = request.POST.get('office_name', '').strip()
        office_realname = request.POST.get('office_realname', '').strip()
        office_pwd = request.POST.get('office_pwd', '').strip()
        office_pwd_con = request.POST.get('office_pwd_con', '').strip()
        pwd_chk = request.POST.get('pwd_chk', '')
        office_part = request.POST.get('office_part', '').strip()
        office_mail = request.POST.get('office_mail', '').strip()
        office_hp = request.POST.get('office_hp', '').strip()
        office_auth_list = request.POST.getlist('office_auth')
        use_auth = request.POST.get('use_auth', 'W')
        coach_code = request.POST.get('coach_code', '').strip()

        error = ''
        if not office_name:
            error = '표시명을 입력해주세요.'
        elif not office_hp:
            error = '연락처를 입력해주세요.'
        elif not office_auth_list:
            error = '메뉴 권한을 1개 이상 선택해주세요.'
        elif pwd_chk == 'on':
            if not office_pwd or len(office_pwd) < 10:
                error = '비밀번호는 10자 이상 입력해주세요.'
            elif office_pwd != office_pwd_con:
                error = '비밀번호가 일치하지 않습니다.'
            elif user.office_id == office_pwd:
                error = '아이디와 비밀번호는 같을 수 없습니다.'
        if not error and coach_code:
            dup = OfficeUser.objects.filter(coach_code=coach_code, del_chk='N').exclude(office_code=pk)
            if dup.exists():
                error = '이미 등록된 코치코드입니다.'

        if error:
            return render(request, 'ba_office/manage/ofuser_modify.html', {
                'error': error,
                'user': user,
                'coaches': coaches,
                'form_data': request.POST,
            })

        user.office_name = office_name
        user.office_realname = office_realname
        user.office_part = office_part
        user.office_mail = office_mail
        user.office_hp = office_hp
        user.power_level = ','.join(office_auth_list)
        user.use_auth = use_auth
        user.coach_code = coach_code

        if pwd_chk == 'on' and office_pwd:
            user.office_pwd = hashlib.sha256(office_pwd.encode('utf-8')).hexdigest()

        user.save()
        return redirect('office_ofuser_list')

    return render(request, 'ba_office/manage/ofuser_modify.html', {
        'user': user,
        'coaches': coaches,
    })


@office_login_required
@office_permission_required('A')
def ofuser_del(request, pk):
    """관리자 삭제 (소프트 삭제)"""
    if request.method == 'POST':
        user = get_object_or_404(OfficeUser, office_code=pk)
        user.del_chk = 'Y'
        user.save()
    return redirect('office_ofuser_list')


@office_login_required
@office_permission_required('A')
def ofuser_idcheck(request):
    """관리자 아이디 중복 체크 (AJAX)"""
    office_id = request.GET.get('office_id', '').strip()
    exists = OfficeUser.objects.filter(office_id=office_id).exists()
    return JsonResponse({'exists': exists})


# ============================================================
# 시스템관리 > 코드 관리
# ============================================================

@office_login_required
@office_permission_required('A')
def code_list(request):
    """코드 그룹 목록"""
    groups = CodeGroup.objects.filter(del_chk='N').order_by('grpcode')
    selected = request.GET.get('grpcode', '')
    return render(request, 'ba_office/manage/code_list.html', {
        'groups': groups,
        'selected': selected,
    })


@office_login_required
@office_permission_required('A')
def code_sub_list(request):
    """서브 코드 목록 (iframe용)"""
    grpcode = request.GET.get('grpcode', '')
    grpcode_name = request.GET.get('grpcode_name', '')
    codes = []
    if grpcode:
        codes = CodeValue.objects.filter(group_id=grpcode, del_chk='N').order_by('code_order')
    return render(request, 'ba_office/manage/code_sub_list.html', {
        'grpcode': grpcode,
        'grpcode_name': grpcode_name,
        'codes': codes,
    })


@office_login_required
@office_permission_required('A')
def codegroup_write(request):
    """코드 그룹 등록"""
    if request.method == 'POST':
        grpcode = request.POST.get('grpcode', '').strip().upper()
        grpcode_name = request.POST.get('grpcode_name', '').strip()
        office_user = request.session.get('office_user', {})

        error = ''
        if not grpcode or len(grpcode) != 4:
            error = '그룹코드는 영문 대문자 4자리로 입력해주세요.'
        elif not grpcode.isalpha():
            error = '그룹코드는 영문 대문자만 가능합니다.'
        elif not grpcode_name:
            error = '그룹명을 입력해주세요.'
        elif CodeGroup.objects.filter(grpcode=grpcode).exists():
            error = '이미 존재하는 그룹코드입니다.'

        if error:
            return render(request, 'ba_office/manage/codegroup_write.html', {
                'error': error,
                'form_data': request.POST,
            })

        CodeGroup.objects.create(
            grpcode=grpcode,
            grpcode_name=grpcode_name,
            del_chk='N',
            insert_dt=timezone.now(),
            insert_id=office_user.get('office_id', ''),
        )
        return redirect('office_code_list')

    return render(request, 'ba_office/manage/codegroup_write.html')


@office_login_required
@office_permission_required('A')
def codegroup_modify(request, pk):
    """코드 그룹 수정"""
    group = get_object_or_404(CodeGroup, grpcode=pk, del_chk='N')

    if request.method == 'POST':
        grpcode_name = request.POST.get('grpcode_name', '').strip()

        if not grpcode_name:
            return render(request, 'ba_office/manage/codegroup_modify.html', {
                'error': '그룹명을 입력해주세요.',
                'group': group,
            })

        group.grpcode_name = grpcode_name
        group.save()
        return redirect('office_code_list')

    return render(request, 'ba_office/manage/codegroup_modify.html', {
        'group': group,
    })


@office_login_required
@office_permission_required('A')
def codegroup_del(request, pk):
    """코드 그룹 삭제 (소프트 삭제)"""
    if request.method == 'POST':
        group = get_object_or_404(CodeGroup, grpcode=pk)
        group.del_chk = 'Y'
        group.save()
        # 하위 코드도 삭제
        CodeValue.objects.filter(group_id=pk).update(del_chk='Y')
    return redirect('office_code_list')


@office_login_required
@office_permission_required('A')
def codesub_write(request):
    """서브 코드 등록"""
    grpcode = request.GET.get('grpcode', '') or request.POST.get('grpcode', '')
    grpcode_name = request.GET.get('grpcode_name', '') or request.POST.get('grpcode_name', '')

    if request.method == 'POST':
        code_name = request.POST.get('code_name', '').strip()
        code_desc = request.POST.get('code_desc', '').strip()
        code_order = request.POST.get('code_order', '0').strip()
        office_user = request.session.get('office_user', {})

        error = ''
        if not code_name:
            error = '코드명을 입력해주세요.'
        elif not code_order.isdigit():
            error = '정렬순서는 숫자만 입력해주세요.'

        if error:
            return render(request, 'ba_office/manage/codesub_write.html', {
                'error': error,
                'grpcode': grpcode,
                'grpcode_name': grpcode_name,
                'form_data': request.POST,
            })

        # 다음 subcode 계산
        max_sub = CodeValue.objects.filter(group_id=grpcode).order_by('-subcode').first()
        next_subcode = (max_sub.subcode + 1) if max_sub else 1

        CodeValue.objects.create(
            subcode=next_subcode,
            group_id=grpcode,
            code_name=code_name,
            code_desc=code_desc,
            code_order=int(code_order),
            del_chk='N',
            insert_dt=timezone.now(),
            insert_id=office_user.get('office_id', ''),
        )
        return redirect(f'/ba_office/manage/code/sub/?grpcode={grpcode}&grpcode_name={grpcode_name}')

    return render(request, 'ba_office/manage/codesub_write.html', {
        'grpcode': grpcode,
        'grpcode_name': grpcode_name,
    })


@office_login_required
@office_permission_required('A')
def codesub_modify(request, grpcode, subcode):
    """서브 코드 수정"""
    code = get_object_or_404(CodeValue, group_id=grpcode, subcode=subcode, del_chk='N')
    grpcode_name = request.GET.get('grpcode_name', '') or request.POST.get('grpcode_name', '')
    if not grpcode_name:
        grpcode_name = code.group.grpcode_name if code.group else ''

    if request.method == 'POST':
        code_name = request.POST.get('code_name', '').strip()
        code_desc = request.POST.get('code_desc', '').strip()
        code_order = request.POST.get('code_order', '0').strip()

        error = ''
        if not code_name:
            error = '코드명을 입력해주세요.'
        elif not code_order.isdigit():
            error = '정렬순서는 숫자만 입력해주세요.'

        if error:
            return render(request, 'ba_office/manage/codesub_modify.html', {
                'error': error,
                'code': code,
                'grpcode': grpcode,
                'grpcode_name': grpcode_name,
            })

        code.code_name = code_name
        code.code_desc = code_desc
        code.code_order = int(code_order)
        code.save()
        return redirect(f'/ba_office/manage/code/sub/?grpcode={grpcode}&grpcode_name={grpcode_name}')

    return render(request, 'ba_office/manage/codesub_modify.html', {
        'code': code,
        'grpcode': grpcode,
        'grpcode_name': grpcode_name,
    })


@office_login_required
@office_permission_required('A')
def codesub_del(request):
    """서브 코드 삭제 (소프트 삭제)"""
    if request.method == 'POST':
        grpcode = request.POST.get('grpcode', '')
        subcode = request.POST.get('subcode', '')
        grpcode_name = request.POST.get('grpcode_name', '')
        if grpcode and subcode:
            CodeValue.objects.filter(group_id=grpcode, subcode=int(subcode)).update(del_chk='Y')
        return redirect(f'/ba_office/manage/code/sub/?grpcode={grpcode}&grpcode_name={grpcode_name}')
    return redirect('office_code_list')


# ============================================================
# 시스템관리 > 포인트 설정
# ============================================================

@office_login_required
@office_permission_required('A')
def point_setup(request):
    """포인트 설정"""
    if request.method == 'POST':
        configs = PointConfig.objects.all().order_by('point_seq')
        for config in configs:
            use_yn = request.POST.get(f'use_yn_{config.point_seq}', config.use_yn)
            save_point = request.POST.get(f'save_point_{config.point_seq}', '')
            limit_point = request.POST.get(f'limit_point_{config.point_seq}', '')

            config.use_yn = use_yn
            if save_point != '':
                config.save_point = int(save_point)
            if limit_point != '':
                config.limit_point = int(limit_point)
            config.save()

        return redirect('office_point_setup')

    configs = PointConfig.objects.all().order_by('point_seq')
    return render(request, 'ba_office/manage/point_setup.html', {
        'configs': configs,
    })


# ============================================================
# 시스템관리 > 관리자 알림
# ============================================================

@office_login_required
@office_permission_required('A')
def office_alim_list(request):
    """관리자 알림 목록"""
    notices = OfficeNotification.objects.filter(del_chk='N').order_by('-no_seq')
    return render(request, 'ba_office/manage/office_alim_list.html', {
        'notices': notices,
    })


@office_login_required
@office_permission_required('A')
def office_alim_write(request):
    """관리자 알림 등록"""
    if request.method == 'POST':
        atitle = request.POST.get('atitle', '').strip()
        acontent = request.POST.get('acontent', '').strip()
        office_user = request.session.get('office_user', {})

        error = ''
        if not atitle:
            error = '제목을 입력해주세요.'
        elif not acontent:
            error = '내용을 입력해주세요.'

        if error:
            return render(request, 'ba_office/manage/office_alim_write.html', {
                'error': error,
                'form_data': request.POST,
            })

        # 다음 no_seq
        max_seq = OfficeNotification.objects.order_by('-no_seq').first()
        next_seq = (max_seq.no_seq + 1) if max_seq else 1

        OfficeNotification.objects.create(
            no_seq=next_seq,
            atitle=atitle,
            acontent=acontent,
            del_chk='N',
            reg_dt=timezone.now(),
            reg_id=office_user.get('office_id', ''),
        )
        return redirect('office_alim_list')

    return render(request, 'ba_office/manage/office_alim_write.html')


@office_login_required
@office_permission_required('A')
def office_alim_modify(request, pk):
    """관리자 알림 수정"""
    notice = get_object_or_404(OfficeNotification, no_seq=pk, del_chk='N')

    if request.method == 'POST':
        atitle = request.POST.get('atitle', '').strip()
        acontent = request.POST.get('acontent', '').strip()

        error = ''
        if not atitle:
            error = '제목을 입력해주세요.'
        elif not acontent:
            error = '내용을 입력해주세요.'

        if error:
            return render(request, 'ba_office/manage/office_alim_modify.html', {
                'error': error,
                'notice': notice,
            })

        notice.atitle = atitle
        notice.acontent = acontent
        notice.save()
        return redirect('office_alim_list')

    return render(request, 'ba_office/manage/office_alim_modify.html', {
        'notice': notice,
    })


@office_login_required
@office_permission_required('A')
def office_alim_del(request, pk):
    """관리자 알림 삭제 (소프트 삭제)"""
    if request.method == 'POST':
        notice = get_object_or_404(OfficeNotification, no_seq=pk)
        notice.del_chk = 'Y'
        notice.save()
    return redirect('office_alim_list')


# ============================================================
# 회원관리 > 회원정보
# ============================================================

@office_login_required
@office_permission_required('M')
def member_list(request):
    """회원 목록"""
    sch_name = request.GET.get('sch_member_name', '').strip()
    sch_id = request.GET.get('sch_member_id', '').strip()
    sch_status = request.GET.get('sch_member_status', '')
    page = request.GET.get('page', '1')

    qs = Member.objects.filter(is_superuser=False)
    if sch_name:
        qs = qs.filter(name__icontains=sch_name)
    if sch_id:
        qs = qs.filter(username__icontains=sch_id)
    if sch_status:
        qs = qs.filter(status=sch_status)

    # 포인트, 자녀수 어노테이션
    qs = qs.annotate(
        add_point=Coalesce(
            Sum('point_histories__app_point', filter=Q(point_histories__app_gbn='S')),
            Value(0), output_field=IntegerField()
        ),
        min_point=Coalesce(
            Sum('point_histories__app_point', filter=Q(point_histories__app_gbn='U')),
            Value(0), output_field=IntegerField()
        ),
        child_count=Count('children', distinct=True),
    ).order_by('-insert_dt', '-id')
    # point = add_point - min_point (뷰에서 계산)

    paginator = Paginator(qs, 20)
    members = paginator.get_page(page)

    return render(request, 'ba_office/lfmember/member_list.html', {
        'members': members,
        'sch_member_name': sch_name,
        'sch_member_id': sch_id,
        'sch_member_status': sch_status,
        'total_count': paginator.count,
    })


@office_login_required
@office_permission_required('M')
def member_list_excel(request):
    """회원 목록 엑셀 다운로드"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    sch_name = request.GET.get('sch_member_name', '').strip()
    sch_id = request.GET.get('sch_member_id', '').strip()
    sch_status = request.GET.get('sch_member_status', '')

    qs = Member.objects.filter(is_superuser=False)
    if sch_name:
        qs = qs.filter(name__icontains=sch_name)
    if sch_id:
        qs = qs.filter(username__icontains=sch_id)
    if sch_status:
        qs = qs.filter(status=sch_status)

    qs = qs.annotate(
        add_point=Coalesce(
            Sum('point_histories__app_point', filter=Q(point_histories__app_gbn='S')),
            Value(0), output_field=IntegerField()
        ),
        min_point=Coalesce(
            Sum('point_histories__app_point', filter=Q(point_histories__app_gbn='U')),
            Value(0), output_field=IntegerField()
        ),
        child_count=Count('children'),
    ).order_by('-insert_dt', '-id')[:10000]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '회원목록'

    header_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    headers = ['순번', '이름', '아이디', 'Point', '연락처', '등록자녀', '메일수신', 'SMS수신', '가입일', '상태']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border

    for i, m in enumerate(qs, 1):
        point = m.add_point - m.min_point
        status_map = {'N': '정상', 'S': '중지', 'O': '탈퇴'}
        row = [i, m.name, m.username, point, m.phone, m.child_count,
               m.mail_consent, m.sms_consent,
               m.insert_dt.strftime('%Y-%m-%d') if m.insert_dt else '',
               status_map.get(m.status, m.status)]
        for col, val in enumerate(row, 1):
            cell = ws.cell(row=i + 1, column=col, value=val)
            cell.border = thin_border

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=member_list.xlsx'
    wb.save(response)
    return response


@office_login_required
@office_permission_required('M')
def member_write(request):
    """회원 등록"""
    if request.method == 'POST':
        member_name = request.POST.get('member_name', '').strip()
        member_id = request.POST.get('member_id', '').strip()
        member_pwd = request.POST.get('member_pwd', '').strip()
        member_pwd_con = request.POST.get('member_pwd_con', '').strip()
        mhtel1 = request.POST.get('mhtel1', '').strip()
        mhtel2 = request.POST.get('mhtel2', '').strip()
        mhtel3 = request.POST.get('mhtel3', '').strip()
        mtel1 = request.POST.get('mtel1', '').strip()
        mtel2 = request.POST.get('mtel2', '').strip()
        mtel3 = request.POST.get('mtel3', '').strip()
        member_mail = request.POST.get('member_mail', '').strip()
        zipcode = request.POST.get('zipcode', '').strip()
        address1 = request.POST.get('address1', '').strip()
        address2 = request.POST.get('address2', '').strip()
        smsyn = request.POST.get('smsyn', 'Y')
        mailyn = request.POST.get('mailyn', 'Y')
        member_status = request.POST.get('member_status', 'N')

        error = ''
        if not member_name:
            error = '이름을 입력해주세요.'
        elif not member_id or len(member_id) < 6:
            error = '아이디는 6자 이상 입력해주세요.'
        elif not member_pwd or len(member_pwd) < 8:
            error = '비밀번호는 8자 이상 입력해주세요.'
        elif member_pwd != member_pwd_con:
            error = '비밀번호가 일치하지 않습니다.'
        elif member_id == member_pwd:
            error = '아이디와 비밀번호는 같을 수 없습니다.'
        elif not mhtel1 or not mhtel2 or not mhtel3:
            error = '휴대전화를 입력해주세요.'
        elif Member.objects.filter(username=member_id).exists():
            error = '이미 사용 중인 아이디입니다.'

        if error:
            return render(request, 'ba_office/lfmember/member_write.html', {
                'error': error, 'form_data': request.POST,
            })

        phone = f'{mhtel1}-{mhtel2}-{mhtel3}' if mhtel1 else ''
        tel = f'{mtel1}-{mtel2}-{mtel3}' if mtel1 and mtel2 else ''

        member = Member.objects.create_user(
            username=member_id,
            password=member_pwd,
            name=member_name,
            phone=phone,
            tel=tel,
            email=member_mail,
            zipcode=zipcode,
            address1=address1,
            address2=address2,
            sms_consent=smsyn,
            mail_consent=mailyn,
            status=member_status,
            insert_dt=timezone.now(),
        )

        # 자녀 등록
        child_cnt = int(request.POST.get('child_cnt', '1'))
        for i in range(1, child_cnt + 1):
            c_name = request.POST.get(f'child_name_{i}', '').strip()
            c_id = request.POST.get(f'child_id_{i}', '').strip()
            c_pwd = request.POST.get(f'child_pwd_{i}', '').strip()
            c_birth = request.POST.get(f'child_birth_{i}', '').strip()
            c_school = request.POST.get(f'sch_name_{i}', '').strip()
            c_grade = request.POST.get(f'sch_grade_{i}', '').strip()
            c_height = request.POST.get(f'child_height_{i}', '').strip()
            c_weight = request.POST.get(f'child_weight_{i}', '').strip()
            c_size = request.POST.get(f'child_size_{i}', '').strip()
            c_tel1 = request.POST.get(f'chtel1_{i}', '').strip()
            c_tel2 = request.POST.get(f'chtel2_{i}', '').strip()
            c_tel3 = request.POST.get(f'chtel3_{i}', '').strip()
            c_sex = request.POST.get(f'child_sexgbn_{i}', '').strip()

            if c_name and c_id:
                c_phone = f'{c_tel1}-{c_tel2}-{c_tel3}' if c_tel1 and c_tel2 else ''
                MemberChild.objects.create(
                    parent=member,
                    name=c_name,
                    child_id=c_id,
                    child_pwd=hashlib.sha256(c_pwd.encode('utf-8')).hexdigest() if c_pwd else '',
                    birth=c_birth,
                    school=c_school,
                    grade=c_grade,
                    height=c_height,
                    weight=c_weight,
                    size=c_size,
                    phone=c_phone,
                    gender=c_sex,
                    status='N',
                    course_state='CAN',
                    insert_dt=timezone.now(),
                )

        return redirect('office_member_list')

    return render(request, 'ba_office/lfmember/member_write.html')


@office_login_required
@office_permission_required('M')
def member_modify(request, member_id):
    """회원 수정"""
    member = get_object_or_404(Member, username=member_id)

    if request.method == 'POST':
        member_pwd = request.POST.get('member_pwd', '').strip()
        member_pwd_con = request.POST.get('member_pwd_con', '').strip()
        pwd_chk = request.POST.get('pwd_chk', '')
        mhtel1 = request.POST.get('mhtel1', '').strip()
        mhtel2 = request.POST.get('mhtel2', '').strip()
        mhtel3 = request.POST.get('mhtel3', '').strip()
        mtel1 = request.POST.get('mtel1', '').strip()
        mtel2 = request.POST.get('mtel2', '').strip()
        mtel3 = request.POST.get('mtel3', '').strip()
        member_mail = request.POST.get('member_mail', '').strip()
        zipcode = request.POST.get('zipcode', '').strip()
        address1 = request.POST.get('address1', '').strip()
        address2 = request.POST.get('address2', '').strip()
        smsyn = request.POST.get('smsyn', 'Y')
        mailyn = request.POST.get('mailyn', 'Y')
        member_status = request.POST.get('member_status', 'N')

        error = ''
        if not mhtel1 or not mhtel2 or not mhtel3:
            error = '휴대전화를 입력해주세요.'
        elif pwd_chk == 'on':
            if not member_pwd or len(member_pwd) < 8:
                error = '비밀번호는 8자 이상 입력해주세요.'
            elif member_pwd != member_pwd_con:
                error = '비밀번호가 일치하지 않습니다.'

        if error:
            return render(request, 'ba_office/lfmember/member_modify.html', {
                'error': error, 'member': member, 'form_data': request.POST,
            })

        member.phone = f'{mhtel1}-{mhtel2}-{mhtel3}' if mhtel1 else ''
        member.tel = f'{mtel1}-{mtel2}-{mtel3}' if mtel1 and mtel2 else ''
        member.email = member_mail
        member.zipcode = zipcode
        member.address1 = address1
        member.address2 = address2
        member.sms_consent = smsyn
        member.mail_consent = mailyn
        member.status = member_status

        if pwd_chk == 'on' and member_pwd:
            member.set_password(member_pwd)

        member.save()
        return redirect('office_member_list')

    # 전화번호 분리
    phone_parts = member.phone.split('-') if member.phone else ['', '', '']
    tel_parts = member.tel.split('-') if member.tel else ['', '', '']
    while len(phone_parts) < 3:
        phone_parts.append('')
    while len(tel_parts) < 3:
        tel_parts.append('')

    return render(request, 'ba_office/lfmember/member_modify.html', {
        'member': member,
        'mhtel1': phone_parts[0], 'mhtel2': phone_parts[1], 'mhtel3': phone_parts[2],
        'mtel1': tel_parts[0], 'mtel2': tel_parts[1], 'mtel3': tel_parts[2],
    })


@office_login_required
@office_permission_required('M')
def member_idcheck(request):
    """회원 아이디 중복 체크 (AJAX)"""
    member_id = request.GET.get('member_id', '').strip()
    exists = Member.objects.filter(username=member_id).exists()
    return JsonResponse({'exists': exists})


@office_login_required
@office_permission_required('M')
def member_childadd(request, member_id):
    """자녀 추가"""
    member = get_object_or_404(Member, username=member_id)

    if request.method == 'POST':
        c_name = request.POST.get('child_name', '').strip()
        c_id = request.POST.get('child_id', '').strip()
        c_pwd = request.POST.get('child_pwd', '').strip()
        c_pwd_con = request.POST.get('child_pwd_con', '').strip()
        c_birth = request.POST.get('child_birth', '').strip()
        c_school = request.POST.get('sch_name', '').strip()
        c_grade = request.POST.get('sch_grade', '').strip()
        c_height = request.POST.get('child_height', '').strip()
        c_weight = request.POST.get('child_weight', '').strip()
        c_size = request.POST.get('child_size', '').strip()
        c_tel1 = request.POST.get('chtel1', '').strip()
        c_tel2 = request.POST.get('chtel2', '').strip()
        c_tel3 = request.POST.get('chtel3', '').strip()
        c_sex = request.POST.get('child_sexgbn', '').strip()

        error = ''
        if not c_name:
            error = '자녀 이름을 입력해주세요.'
        elif not c_id or len(c_id) < 6:
            error = '자녀 아이디는 6자 이상 입력해주세요.'
        elif not c_pwd or len(c_pwd) < 8:
            error = '비밀번호는 8자 이상 입력해주세요.'
        elif c_pwd != c_pwd_con:
            error = '비밀번호가 일치하지 않습니다.'
        elif MemberChild.objects.filter(child_id=c_id).exists():
            error = '이미 사용 중인 자녀 아이디입니다.'

        if error:
            return render(request, 'ba_office/lfmember/member_childadd.html', {
                'error': error, 'member': member, 'form_data': request.POST,
            })

        c_phone = f'{c_tel1}-{c_tel2}-{c_tel3}' if c_tel1 and c_tel2 else ''
        MemberChild.objects.create(
            parent=member,
            name=c_name,
            child_id=c_id,
            child_pwd=hashlib.sha256(c_pwd.encode('utf-8')).hexdigest(),
            birth=c_birth,
            school=c_school,
            grade=c_grade,
            height=c_height,
            weight=c_weight,
            size=c_size,
            phone=c_phone,
            gender=c_sex,
            status='N',
            course_state='CAN',
            insert_dt=timezone.now(),
        )
        return redirect('office_member_list')

    return render(request, 'ba_office/lfmember/member_childadd.html', {
        'member': member,
    })


# ============================================================
# 회원관리 > 자녀정보
# ============================================================

@office_login_required
@office_permission_required('M')
def child_list(request):
    """자녀 목록"""
    status = request.GET.get('status', '')
    skey = request.GET.get('skey', '')
    sword = request.GET.get('sword', '').strip()
    sch_member_id = request.GET.get('sch_member_id', '').strip()
    page = request.GET.get('page', '1')

    qs = MemberChild.objects.select_related('parent').all()

    if sch_member_id:
        qs = qs.filter(parent__username=sch_member_id)
    if status:
        qs = qs.filter(status=status)
    if skey and sword:
        if skey == 'child_name':
            qs = qs.filter(name__icontains=sword)
        elif skey == 'child_id':
            qs = qs.filter(child_id__icontains=sword)
        elif skey == 'm.member_id':
            qs = qs.filter(parent__username__icontains=sword)
        elif skey == 'member_name':
            qs = qs.filter(parent__name__icontains=sword)
        elif skey == 'card_num':
            qs = qs.filter(card_num__icontains=sword)

    qs = qs.order_by('-insert_dt', '-id')

    paginator = Paginator(qs, 15)
    children = paginator.get_page(page)

    return render(request, 'ba_office/lfmember/child_list.html', {
        'children': children,
        'status': status,
        'skey': skey,
        'sword': sword,
        'sch_member_id': sch_member_id,
        'total_count': paginator.count,
    })


@office_login_required
@office_permission_required('M')
def child_modify(request, child_id):
    """자녀 수정"""
    child = get_object_or_404(MemberChild, child_id=child_id)

    if request.method == 'POST':
        child_name = request.POST.get('child_name', '').strip()
        child_birth = request.POST.get('child_birth', '').strip()
        sch_name = request.POST.get('sch_name', '').strip()
        sch_grade = request.POST.get('sch_grade', '').strip()
        child_pwd = request.POST.get('child_pwd', '').strip()
        child_pwd_con = request.POST.get('child_pwd_con', '').strip()
        pwd_chk = request.POST.get('pwd_chk', '')
        child_height = request.POST.get('child_height', '').strip()
        child_weight = request.POST.get('child_weight', '').strip()
        child_size = request.POST.get('child_size', '').strip()
        chtel1 = request.POST.get('chtel1', '').strip()
        chtel2 = request.POST.get('chtel2', '').strip()
        chtel3 = request.POST.get('chtel3', '').strip()
        child_sexgbn = request.POST.get('child_sexgbn', '').strip()
        child_status = request.POST.get('child_status', 'N')
        course_state = request.POST.get('course_state', 'CAN')
        card_num = request.POST.get('card_num', '').strip()

        error = ''
        if not child_name:
            error = '이름을 입력해주세요.'
        elif pwd_chk == 'on':
            if not child_pwd or len(child_pwd) < 8:
                error = '비밀번호는 8자 이상 입력해주세요.'
            elif child_pwd != child_pwd_con:
                error = '비밀번호가 일치하지 않습니다.'

        if error:
            return render(request, 'ba_office/lfmember/child_modify.html', {
                'error': error, 'child': child, 'form_data': request.POST,
            })

        child.name = child_name
        child.birth = child_birth
        child.school = sch_name
        child.grade = sch_grade
        child.height = child_height
        child.weight = child_weight
        child.size = child_size
        child.phone = f'{chtel1}-{chtel2}-{chtel3}' if chtel1 and chtel2 else ''
        child.gender = child_sexgbn
        child.status = child_status
        child.course_state = course_state
        child.card_num = card_num

        if pwd_chk == 'on' and child_pwd:
            child.child_pwd = hashlib.sha256(child_pwd.encode('utf-8')).hexdigest()

        child.save()
        return redirect('office_child_list')

    phone_parts = child.phone.split('-') if child.phone else ['', '', '']
    while len(phone_parts) < 3:
        phone_parts.append('')

    return render(request, 'ba_office/lfmember/child_modify.html', {
        'child': child,
        'chtel1': phone_parts[0], 'chtel2': phone_parts[1], 'chtel3': phone_parts[2],
    })


@office_login_required
@office_permission_required('M')
def child_detail(request, child_id):
    """자녀 상세 - 수강 이력"""
    child = get_object_or_404(MemberChild.objects.select_related('parent'), child_id=child_id)

    from apps.courses.models import Lecture, Stadium
    enrollments = Enrollment.objects.filter(child_id=child_id, del_chk='N').order_by('-id')

    # 수강과정 정보 매핑
    enrollment_data = []
    for enroll in enrollments:
        courses = EnrollmentCourse.objects.filter(enrollment=enroll).order_by('course_ym')
        for course in courses:
            lecture = Lecture.objects.filter(lecture_code=course.lecture_code).first()
            sta = Stadium.objects.filter(sta_code=lecture.stadium_id).first() if lecture else None
            enrollment_data.append({
                'enroll': enroll,
                'course': course,
                'lecture': lecture,
                'stadium': sta,
            })

    return render(request, 'ba_office/lfmember/child_detail.html', {
        'child': child,
        'enrollment_data': enrollment_data,
    })


# ============================================================
# 회원관리 > 회원통계
# ============================================================

@office_login_required
@office_permission_required('M')
def member_stat(request):
    """회원 가입 통계 (일별)"""
    import datetime
    syear = request.GET.get('syear', str(timezone.now().year))
    try:
        year = int(syear)
    except ValueError:
        year = timezone.now().year

    # 월/일별 가입수 집계
    from django.db.models.functions import ExtractMonth, ExtractDay
    parent_stats = (
        Member.objects.filter(
            is_superuser=False, status='N',
            insert_dt__year=year
        )
        .annotate(month=ExtractMonth('insert_dt'), day=ExtractDay('insert_dt'))
        .values('month', 'day')
        .annotate(cnt=Count('id'))
    )

    child_stats = (
        MemberChild.objects.filter(
            status='N',
            insert_dt__year=year
        )
        .annotate(month=ExtractMonth('insert_dt'), day=ExtractDay('insert_dt'))
        .values('month', 'day')
        .annotate(cnt=Count('id'))
    )

    # 데이터 구조화: stat_data[day][month] = {'p': 0, 'c': 0}
    stat_data = {}
    for d in range(1, 32):
        stat_data[d] = {}
        for m in range(1, 13):
            stat_data[d][m] = {'p': 0, 'c': 0}

    for s in parent_stats:
        stat_data[s['day']][s['month']]['p'] = s['cnt']
    for s in child_stats:
        stat_data[s['day']][s['month']]['c'] = s['cnt']

    # 월별 합계
    month_totals = []
    for m in range(1, 13):
        p_total = sum(stat_data[d][m]['p'] for d in range(1, 32))
        c_total = sum(stat_data[d][m]['c'] for d in range(1, 32))
        month_totals.append({'p': p_total, 'c': c_total})

    # 행 데이터를 리스트로 변환 (템플릿에서 쉽게 접근)
    rows = []
    for d in range(1, 32):
        row = {'day': d, 'months': []}
        day_total_p = 0
        day_total_c = 0
        for m in range(1, 13):
            row['months'].append(stat_data[d][m])
            day_total_p += stat_data[d][m]['p']
            day_total_c += stat_data[d][m]['c']
        row['total'] = {'p': day_total_p, 'c': day_total_c}
        rows.append(row)

    # 연도 목록 (2019 ~ 현재)
    current_year = timezone.now().year
    years = list(range(2019, current_year + 1))

    # 전체 합계
    grand_total_p = sum(mt['p'] for mt in month_totals)
    grand_total_c = sum(mt['c'] for mt in month_totals)

    return render(request, 'ba_office/lfmember/member_stat.html', {
        'rows': rows,
        'month_totals': month_totals,
        'grand_total': {'p': grand_total_p, 'c': grand_total_c},
        'syear': year,
        'years': years,
    })


# ============================================================
# 회원관리 > SMS/LMS
# ============================================================

@office_login_required
@office_permission_required('M')
def sms_send(request):
    """SMS/LMS 발송 폼"""
    coaches = Coach.objects.filter(use_gbn='Y').order_by('coach_name')
    return render(request, 'ba_office/lfmember/sms_send.html', {
        'coaches': coaches,
    })


# ============================================================
# 회원관리 > SMS/LMS 내역
# ============================================================

@office_login_required
@office_permission_required('M')
def sms_send_list(request):
    """SMS 발송 내역"""
    page = request.GET.get('page', '1')
    sch_sdate = request.GET.get('sch_sdate', '')
    sch_edate = request.GET.get('sch_edate', '')

    qs = SMSLog.objects.all().order_by('-date_client_req')
    if sch_sdate:
        qs = qs.filter(date_client_req__date__gte=sch_sdate)
    if sch_edate:
        qs = qs.filter(date_client_req__date__lte=sch_edate)

    paginator = Paginator(qs, 40)
    logs = paginator.get_page(page)

    return render(request, 'ba_office/lfmember/sms_send_list.html', {
        'logs': logs,
        'sch_sdate': sch_sdate,
        'sch_edate': sch_edate,
        'total_count': paginator.count,
    })


# ============================================================
# 회원관리 > 회원포인트내역
# ============================================================

@office_login_required
@office_permission_required('M')
def memberpoint_list(request):
    """회원 포인트 내역"""
    page = request.GET.get('page', '1')
    sch_startdt = request.GET.get('sch_startdt', '')
    sch_enddt = request.GET.get('sch_enddt', '')
    sch_app_gbn = request.GET.get('sch_app_gbn', '')
    sch_txt = request.GET.get('sch_txt', '')
    sch_val = request.GET.get('sch_val', '').strip()
    sch_desc_gbn = request.GET.get('sch_desc_gbn', '')

    qs = PointHistory.objects.all().order_by('-insert_dt', '-id')
    if sch_startdt:
        qs = qs.filter(point_dt__gte=sch_startdt.replace('-', ''))
    if sch_enddt:
        qs = qs.filter(point_dt__lte=sch_enddt.replace('-', ''))
    if sch_app_gbn:
        qs = qs.filter(app_gbn=sch_app_gbn)
    if sch_txt and sch_val:
        if sch_txt == 'member_id':
            qs = qs.filter(member_id__icontains=sch_val)
        elif sch_txt == 'member_name':
            qs = qs.filter(member_name__icontains=sch_val)
    if sch_desc_gbn:
        qs = qs.filter(point_desc__icontains=sch_desc_gbn)

    paginator = Paginator(qs, 20)
    histories = paginator.get_page(page)

    return render(request, 'ba_office/lfmember/memberpoint_list.html', {
        'histories': histories,
        'sch_startdt': sch_startdt,
        'sch_enddt': sch_enddt,
        'sch_app_gbn': sch_app_gbn,
        'sch_txt': sch_txt,
        'sch_val': sch_val,
        'sch_desc_gbn': sch_desc_gbn,
        'total_count': paginator.count,
    })


@office_login_required
@office_permission_required('M')
def memberpoint_write(request):
    """포인트 수동 등록"""
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '').strip()
        app_gbn = request.POST.get('app_gbn', 'S')
        app_point = request.POST.get('app_point', '0').strip()
        point_desc = request.POST.get('point_desc', '').strip()
        office_user = request.session.get('office_user', {})

        error = ''
        if not member_id:
            error = '회원 아이디를 입력해주세요.'
        elif not Member.objects.filter(username=member_id).exists():
            error = '존재하지 않는 회원 아이디입니다.'
        elif not app_point or not app_point.isdigit() or int(app_point) <= 0:
            error = '포인트를 올바르게 입력해주세요.'
        elif not point_desc:
            error = '내용을 입력해주세요.'

        if error:
            return render(request, 'ba_office/lfmember/memberpoint_write.html', {
                'error': error, 'form_data': request.POST,
            })

        member = Member.objects.get(username=member_id)
        now = timezone.now()
        PointHistory.objects.create(
            point_dt=now.strftime('%Y%m%d'),
            member=member,
            member_name=member.name,
            app_gbn=app_gbn,
            app_point=int(app_point),
            point_desc=point_desc,
            desc_detail='관리자 직권',
            insert_dt=now,
            insert_id=office_user.get('office_id', ''),
        )
        return redirect('office_memberpoint_list')

    return render(request, 'ba_office/lfmember/memberpoint_write.html')


@office_login_required
@office_permission_required('M')
def memberpoint_del(request, pk):
    """포인트 삭제"""
    if request.method == 'POST':
        history = get_object_or_404(PointHistory, pk=pk)
        history.delete()
    return redirect('office_memberpoint_list')


# ============================================================
# 회원관리 > 탈퇴회원리스트
# ============================================================

@office_login_required
@office_permission_required('M')
def secession_list(request):
    """탈퇴회원 목록"""
    sch_name = request.GET.get('sch_member_name', '').strip()
    sch_id = request.GET.get('sch_member_id', '').strip()
    page = request.GET.get('page', '1')

    qs = OutMember.objects.all().order_by('-out_dt')
    if sch_name:
        qs = qs.filter(member_name__icontains=sch_name)
    if sch_id:
        qs = qs.filter(member_id__icontains=sch_id)

    paginator = Paginator(qs, 20)
    members = paginator.get_page(page)

    return render(request, 'ba_office/lfmember/secession_list.html', {
        'members': members,
        'sch_member_name': sch_name,
        'sch_member_id': sch_id,
        'total_count': paginator.count,
    })
