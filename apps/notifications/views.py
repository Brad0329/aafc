from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Notification


@login_required
def notification_list(request):
    """알림장 - 학부모 알림 목록"""
    notifications = Notification.objects.filter(
        member=request.user,
        alim_gbn='P',
        del_chk='N',
    ).order_by('-insert_dt')

    context = {
        'current_menu': 'alim',
        'notifications': notifications,
    }
    return render(request, 'notifications/notification_list.html', context)
