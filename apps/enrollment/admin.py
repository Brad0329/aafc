from django.contrib import admin
from .models import Enrollment, EnrollmentCourse, EnrollmentBill, WaitStudent, Attendance, ChangeHistory


class EnrollmentCourseInline(admin.TabularInline):
    model = EnrollmentCourse
    extra = 0
    fields = ['bill_code', 'course_ym', 'course_ym_amt', 'lecture_code', 'start_ymd', 'course_stats']


class EnrollmentBillInline(admin.TabularInline):
    model = EnrollmentBill
    extra = 0
    fields = ['bill_code', 'bill_desc', 'bill_amt', 'pay_stats']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'member', 'child', 'pay_stats', 'pay_price', 'pay_method',
                    'lecture_stats', 'lec_cycle', 'lec_period', 'start_dt', 'end_dt',
                    'apply_gubun', 'insert_dt']
    list_filter = ['pay_stats', 'lecture_stats', 'apply_gubun', 'lec_cycle', 'lec_period']
    search_fields = ['member__username', 'member__name', 'child__name', 'child__child_id']
    raw_id_fields = ['member', 'child']
    ordering = ['-id']
    inlines = [EnrollmentBillInline, EnrollmentCourseInline]
    fieldsets = (
        (None, {'fields': ('member', 'child')}),
        ('결제', {'fields': ('pay_stats', 'pay_method', 'pay_price', 'pay_dt')}),
        ('수강', {'fields': ('lecture_stats', 'lec_cycle', 'lec_period', 'start_dt', 'end_dt')}),
        ('신청', {'fields': ('apply_gubun', 'source_gubun', 'recommend_id')}),
        ('할인', {'fields': (
            ('discount1_id', 'discount1_price'),
            ('discount2_id', 'discount2_price'),
            ('discount3_id', 'discount3_price'),
            ('discount4_id', 'discount4_price'),
            ('discount5_id', 'discount5_price'),
            ('discount6_id', 'discount6_price'),
        )}),
        ('기타', {'fields': ('del_chk', 'insert_id', 'insert_dt')}),
    )
    readonly_fields = ['insert_dt']


@admin.register(WaitStudent)
class WaitStudentAdmin(admin.ModelAdmin):
    list_display = ['id', 'child_name', 'member_id', 'lecture_code', 'sta_code',
                    'wait_seq', 'trans_gbn', 'del_chk', 'insert_dt']
    list_filter = ['trans_gbn', 'del_chk']
    search_fields = ['member_id', 'child_name', 'child_id']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'attendance_dt', 'sta_code', 'lecture_code', 'child_id',
                    'attendance_gbn', 'complete_yn', 'app_month']
    list_filter = ['attendance_gbn', 'complete_yn']
    search_fields = ['child_id', 'attendance_dt']
    ordering = ['-id']


@admin.register(ChangeHistory)
class ChangeHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'chg_gbn', 'chg_desc', 'member_id', 'child_id',
                    'no_seq', 'reg_dt', 'reg_id']
    list_filter = ['chg_gbn']
    search_fields = ['member_id', 'child_id', 'chg_desc']
    ordering = ['-id']
