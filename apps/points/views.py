from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Case, When, IntegerField
from django.shortcuts import render

from .models import PointHistory


@login_required
def point_list(request):
    """마이포인트 - 포인트 조회"""
    histories = PointHistory.objects.filter(member=request.user)

    # 포인트 잔액 계산: SUM(S) - SUM(U)
    balance_data = histories.aggregate(
        total_save=Sum(
            Case(When(app_gbn='S', then='app_point'), default=0, output_field=IntegerField())
        ),
        total_use=Sum(
            Case(When(app_gbn='U', then='app_point'), default=0, output_field=IntegerField())
        ),
    )
    total_save = balance_data['total_save'] or 0
    total_use = balance_data['total_use'] or 0
    point_balance = total_save - total_use

    # 내역 목록 (최신순, 페이징)
    history_list = histories.order_by('-insert_dt', '-id')
    paginator = Paginator(history_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'current_menu': 'mypoint',
        'point_balance': point_balance,
        'total_save': total_save,
        'total_use': total_use,
        'page_obj': page_obj,
    }
    return render(request, 'points/point_list.html', context)
