from django.contrib import admin
from .models import PointConfig, PointHistory


@admin.register(PointConfig)
class PointConfigAdmin(admin.ModelAdmin):
    list_display = ['point_seq', 'point_title', 'use_yn', 'app_gbn', 'save_gbn', 'save_point', 'limit_point']
    list_filter = ['use_yn', 'app_gbn', 'save_gbn']
    search_fields = ['point_seq', 'point_title']


@admin.register(PointHistory)
class PointHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'point_dt', 'member', 'member_name', 'app_gbn', 'app_point', 'point_desc', 'order_no', 'insert_dt']
    list_filter = ['app_gbn']
    search_fields = ['member_id', 'member_name', 'point_desc', 'order_no']
    readonly_fields = ['insert_dt']
