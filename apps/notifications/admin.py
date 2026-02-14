from django.contrib import admin
from .models import Notification, OfficeNotification, SMSLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['no_seq', 'alim_gbn', 'member', 'member_name', 'alim_title', 'insert_name', 'insert_dt', 'del_chk']
    list_filter = ['alim_gbn', 'del_chk']
    search_fields = ['alim_title', 'alim_content', 'member_name']


@admin.register(OfficeNotification)
class OfficeNotificationAdmin(admin.ModelAdmin):
    list_display = ['no_seq', 'atitle', 'del_chk', 'reg_dt', 'reg_id']
    list_filter = ['del_chk']
    search_fields = ['atitle', 'acontent']


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'date_client_req', 'subject', 'callback', 'recipient_num', 'service_type', 'msg_status']
    list_filter = ['service_type', 'msg_status']
    search_fields = ['recipient_num', 'subject', 'content', 'callback']
    readonly_fields = [
        'msg_key', 'date_client_req', 'subject', 'content', 'callback',
        'service_type', 'msg_status', 'recipient_num', 'broadcast_yn',
        'date_sent', 'date_rslt', 'rslt',
    ]
