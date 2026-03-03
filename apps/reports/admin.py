from django.contrib import admin
from .models import MonthlyData


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
