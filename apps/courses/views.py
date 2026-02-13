from collections import OrderedDict
from django.shortcuts import render, get_object_or_404
from apps.common.models import CodeValue
from .models import Stadium, Coach, StadiumCoach, Lecture


def _get_local_name_map():
    """권역 코드 → 권역명 매핑"""
    return dict(
        CodeValue.objects.filter(
            group_id='LOCD', del_chk='N'
        ).values_list('subcode', 'code_name')
    )


def stadium_list_view(request):
    """구장안내 페이지"""
    stadiums = Stadium.objects.filter(use_gbn='Y').order_by('order_seq', 'sta_name')
    local_names = _get_local_name_map()

    stadium_list = []
    for s in stadiums:
        stadium_list.append({
            'sta_code': s.sta_code,
            'sta_name': s.sta_name,
            'sta_phone': s.sta_phone,
            'local_name': local_names.get(s.local_code, ''),
        })

    return render(request, 'courses/stadium_list.html', {
        'stadiums': stadium_list,
        'menu': 'stadium',
    })


def stadium_detail_view(request, sta_code):
    """구장 상세 (AJAX partial)"""
    stadium = get_object_or_404(Stadium, sta_code=sta_code, use_gbn='Y')

    # 관련 강좌 (사용 중인 것만)
    lectures = Lecture.objects.filter(
        stadium=stadium, use_gbn='Y'
    ).order_by('class_gbn', 'lecture_day', 'lecture_time')

    # class_gbn별 그룹핑
    lecture_groups = OrderedDict()
    for lec in lectures:
        key = lec.class_gbn or '기타'
        if key not in lecture_groups:
            lecture_groups[key] = []
        lecture_groups[key].append({
            'day': lec.get_day_display(),
            'time': lec.lecture_time,
            'age': lec.lec_age,
            'capacity': lec.stu_cnt,
        })

    # 담당 코치
    coach_images = []
    sta_coaches = StadiumCoach.objects.filter(
        stadium=stadium
    ).select_related('coach')
    for sc in sta_coaches:
        if sc.coach.coach_s_img:
            coach_images.append(sc.coach.coach_s_img)

    return render(request, 'courses/stadium_detail_fragment.html', {
        'stadium': stadium,
        'lecture_groups': lecture_groups,
        'coach_images': coach_images,
    })


def coach_list_view(request):
    """코칭스태프 페이지"""
    coaches = Coach.objects.filter(use_gbn='Y').order_by('order_seq', 'coach_name')
    return render(request, 'courses/coach_list.html', {
        'coaches': coaches,
        'menu': 'coach',
    })


def program_view(request):
    """교육 프로그램 페이지"""
    return render(request, 'courses/program.html', {
        'menu': 'program',
    })


def greeting_view(request):
    """운영진 인사말 페이지"""
    return render(request, 'courses/greeting.html', {
        'menu': 'greeting',
    })


def emblem_view(request):
    """엠블럼 & BI소개 페이지"""
    return render(request, 'courses/emblem.html', {
        'menu': 'emblem',
    })


def waytocome_view(request):
    """찾아오시는 길 페이지"""
    return render(request, 'courses/waytocome.html', {
        'menu': 'waytocome',
    })
