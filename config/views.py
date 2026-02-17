from datetime import date, timedelta

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.board.models import Board, Popup
from apps.consult.models import ConsultFree, ConsultRegion


def main_view(request):
    """메인 페이지"""
    today = date.today().strftime('%Y-%m-%d')
    three_days_ago = (date.today() - timedelta(days=3)).strftime('%Y-%m-%d')

    def get_board_posts(gbn):
        return Board.objects.filter(
            b_gbn=gbn, del_chk='N'
        ).annotate(
            comment_count=Count('comments', filter=Q(comments__del_chk='N'))
        ).order_by('-b_ref', 'b_level', '-b_seq')[:5]

    # 상담 지역 목록
    regions = ConsultRegion.objects.filter(
        del_chk='N', reg_gbn='L'
    ).order_by('reg_name')

    # 활성 팝업
    popups = Popup.objects.filter(
        pop_yn='Y',
        pop_begin_date__lte=today,
        pop_end_date__gte=today,
    )

    context = {
        'notices': get_board_posts('Y'),
        'news': get_board_posts('N'),
        'study': get_board_posts('ST'),
        'events': get_board_posts('E'),
        'regions': regions,
        'popups': popups,
        'three_days_ago': three_days_ago,
    }
    return render(request, 'main.html', context)


@require_POST
def ajax_main_consult(request):
    """메인 페이지 간이 상담 접수 (AJAX)"""
    jname = request.POST.get('jname', '').strip()
    jphone1 = request.POST.get('jphone1', '010')
    jphone2 = request.POST.get('jphone2', '').strip()
    jphone3 = request.POST.get('jphone3', '').strip()
    jlocal = request.POST.get('jlocal', '').strip()
    consult_gbn = request.POST.get('consult_gbn', 'A1')

    if not jname:
        return JsonResponse({'success': False, 'message': '이름을 입력하여 주세요.'})
    if not jphone2 or not jphone3:
        return JsonResponse({'success': False, 'message': '연락처를 입력하여 주세요.'})

    ConsultFree.objects.create(
        jname=jname,
        jphone1=jphone1,
        jphone2=jphone2,
        jphone3=jphone3,
        jlocal=jlocal,
        j_date=timezone.now(),
        consult_gbn=consult_gbn,
    )

    return JsonResponse({'success': True, 'message': '상담 예약이 접수되었습니다.'})


def robots_txt(request):
    """robots.txt"""
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    content = render(request, 'robots.txt', {
        'scheme': scheme,
        'host': host,
    }).content.decode()
    return HttpResponse(content, content_type='text/plain')
