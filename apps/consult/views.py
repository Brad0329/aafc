from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from .models import Consult, ConsultAnswer, ConsultFree, ConsultRegion
from apps.courses.models import Stadium
from apps.common.models import CodeValue


def consult_form(request):
    """상담 신청"""
    # 상담유형 코드 조회
    consult_categories = CodeValue.objects.filter(
        group__grpcode='CONT', del_chk='N'
    ).order_by('code_order')

    if request.method == 'POST':
        consult_name = request.POST.get('consult_name', '').strip()
        ctel1 = request.POST.get('ctel1', '')
        ctel2 = request.POST.get('ctel2', '')
        ctel3 = request.POST.get('ctel3', '')
        stu_name = request.POST.get('stu_name', '').strip()
        stu_sex = request.POST.get('stu_sex', 'M')
        stu_age = request.POST.get('stu_age', '0')
        consult_title = request.POST.get('consult_title', '').strip()
        consult_content = request.POST.get('consult_content', '').strip()
        sta_code = request.POST.get('sta_code', '')
        consult_category = request.POST.get('consult_category', '0')

        consult_tel = f'{ctel1}-{ctel2}-{ctel3}'

        # 회원 정보
        member_id = ''
        member_name = ''
        consult_gbn = 'guest'
        if request.user.is_authenticated:
            member_id = request.user.username
            member_name = getattr(request.user, 'name', request.user.username)
            consult_gbn = 'old'

        # 상담 생성
        consult = Consult.objects.create(
            member_id=member_id,
            member_name=member_name,
            consult_name=consult_name,
            consult_tel=consult_tel,
            consult_gbn=consult_gbn,
            consult_title=consult_title,
            consult_content=consult_content,
            consult_dt=timezone.now(),
            sta_code=str(sta_code),
            stu_name=stu_name,
            stu_sex=stu_sex,
            stu_age=int(stu_age) if stu_age.isdigit() else 0,
            line_code=33,
        )

        # 초기 답변 레코드 생성
        ConsultAnswer.objects.create(
            consult=consult,
            consult_category=int(consult_category) if str(consult_category).isdigit() else 0,
            stat_code=76,
        )

        return render(request, 'consult/consult_done.html', {
            'message': '상담이 접수되었습니다. 담당자가 개별 연락 예정입니다.'
        })

    context = {
        'consult_categories': consult_categories,
    }
    return render(request, 'consult/consult.html', context)


def consult_free_form(request):
    """무료체험 신청"""
    regions = ConsultRegion.objects.filter(del_chk='N', reg_gbn='L').order_by('reg_name')

    if request.method == 'POST':
        jname = request.POST.get('jname', '').strip()
        jphone1 = request.POST.get('jphone1', '010')
        jphone2 = request.POST.get('jphone2', '')
        jphone3 = request.POST.get('jphone3', '')
        jlocal = request.POST.get('jlocal', '')
        consult_gbn = request.POST.get('consult_gbn', 'B1')

        ConsultFree.objects.create(
            jname=jname,
            jphone1=jphone1,
            jphone2=jphone2,
            jphone3=jphone3,
            jlocal=jlocal,
            j_date=timezone.now(),
            consult_gbn=consult_gbn,
        )

        return render(request, 'consult/consult_done.html', {
            'message': '무료수업체험 신청이 완료되었습니다. 담당자가 개별 연락 예정입니다.'
        })

    context = {
        'regions': regions,
    }
    return render(request, 'consult/cfree.html', context)


def ajax_search_stadium(request):
    """구장 검색 (AJAX)"""
    stxt = request.GET.get('stxt', '').strip()
    if not stxt:
        return render(request, 'consult/fragments/stadium_search_result.html', {'stadiums': []})

    stadiums = Stadium.objects.filter(
        Q(sta_address__icontains=stxt) | Q(sta_name__icontains=stxt),
        use_gbn='Y'
    ).order_by('order_seq', 'sta_name')

    return render(request, 'consult/fragments/stadium_search_result.html', {'stadiums': stadiums})
