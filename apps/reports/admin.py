from django.contrib import admin
from .models import (
    DailyTotalData, DailyCoachData, DailyCoachDataNew,
    DailyCoachDataMonth, MonthlyData,
)


@admin.register(DailyTotalData)
class DailyTotalDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'proc_dt', 'member_name', 'child_name', 'sta_name',
                    'lecture_title', 'coach_name', 'pay_stats', 'pay_method',
                    'pay_price', 'course_ym']
    list_filter = ['pay_stats', 'pay_method']
    search_fields = ['member_id', 'member_name', 'child_name', 'sta_name', 'coach_name']
    ordering = ['-id']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyCoachData)
class DailyCoachDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'course_ym', 'lgbn_name', 'sta_name', 'coach_name',
                    'member_id', 'child_id', 'cl_cnt', 'm1001_price', 'm2001_price']
    list_filter = ['lgbn_name']
    search_fields = ['coach_name', 'sta_name', 'member_id']
    ordering = ['-id']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyCoachDataNew)
class DailyCoachDataNewAdmin(admin.ModelAdmin):
    list_display = ['id', 'proc_dt', 'course_ym', 'coach_name', 'sta_code',
                    'pay_method', 'cl_cnt', 'm1001_price', 'm2001_price']
    search_fields = ['coach_name', 'member_id']
    ordering = ['-id']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyCoachDataMonth)
class DailyCoachDataMonthAdmin(admin.ModelAdmin):
    list_display = ['id', 'course_ym', 'coach_name', 'new_coach_name', 'sta_code',
                    'pay_method', 'cl_cnt', 'm1001_price', 'm2001_price']
    search_fields = ['coach_name', 'new_coach_name', 'member_id']
    ordering = ['-id']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(MonthlyData)
class MonthlyDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'proc_dt', 'code_desc', 'sta_name', 'm_cnt', 'goal_cnt',
                    'tocl', 'stats_tot_cnt', 'stats_ln_cnt']
    list_filter = ['code_desc']
    search_fields = ['sta_name']
    ordering = ['-id']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
