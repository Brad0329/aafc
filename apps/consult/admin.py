from django.contrib import admin
from .models import Consult, ConsultAnswer, ConsultFree, ConsultRegion


class ConsultAnswerInline(admin.TabularInline):
    model = ConsultAnswer
    extra = 0
    fields = ['consult_category', 'consult_answer', 'stat_code', 'coach_code', 'con_answer_dt']
    readonly_fields = ['con_answer_dt']


@admin.register(Consult)
class ConsultAdmin(admin.ModelAdmin):
    list_display = ['id', 'consult_name', 'consult_tel', 'stu_name', 'sta_code',
                    'consult_gbn', 'consult_dt', 'del_chk']
    list_filter = ['del_chk', 'consult_gbn']
    search_fields = ['consult_name', 'consult_tel', 'stu_name', 'consult_title']
    ordering = ['-id']
    inlines = [ConsultAnswerInline]
    fieldsets = (
        (None, {'fields': ('consult_name', 'consult_tel', 'consult_gbn', 'consult_title', 'consult_content')}),
        ('회원정보', {'fields': ('member_id', 'member_name', 'child_id', 'child_name')}),
        ('수강생', {'fields': ('stu_name', 'stu_sex', 'stu_age')}),
        ('구장/경로', {'fields': ('local_code', 'sta_code', 'path_code', 'line_code')}),
        ('기타', {'fields': ('consult_pwd', 'manage_id', 'company_name', 'com_employee_no', 'del_chk', 'consult_dt')}),
    )
    readonly_fields = ['consult_dt']


@admin.register(ConsultFree)
class ConsultFreeAdmin(admin.ModelAdmin):
    list_display = ['id', 'jname', 'jphone1', 'jphone2', 'jphone3', 'jlocal',
                    'consult_gbn', 'confirm_yn', 'j_date', 'del_chk']
    list_filter = ['confirm_yn', 'del_chk', 'consult_gbn']
    search_fields = ['jname', 'jphone2', 'jphone3']
    ordering = ['-id']


@admin.register(ConsultRegion)
class ConsultRegionAdmin(admin.ModelAdmin):
    list_display = ['id', 'reg_name', 'reg_gbn', 'mphone', 'del_chk']
    list_filter = ['del_chk', 'reg_gbn']
    search_fields = ['reg_name']
