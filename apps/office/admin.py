from django.contrib import admin
from .models import OfficeUser, OfficeLoginHistory


@admin.register(OfficeUser)
class OfficeUserAdmin(admin.ModelAdmin):
    list_display = ['office_code', 'office_name', 'office_id', 'office_part',
                    'power_level', 'use_auth', 'del_chk']
    list_filter = ['use_auth', 'del_chk']
    search_fields = ['office_name', 'office_id']


@admin.register(OfficeLoginHistory)
class OfficeLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['office_id', 'login_dt', 'login_ip']
    list_filter = ['office_id']
    search_fields = ['office_id']
