from django.contrib import admin
from .models import Stadium, Coach, StadiumCoach, Lecture, StadiumGoal, Promotion


class StadiumCoachInline(admin.TabularInline):
    model = StadiumCoach
    extra = 0
    raw_id_fields = ['coach']


class LectureInline(admin.TabularInline):
    model = Lecture
    extra = 0
    fields = ['lecture_code', 'lecture_title', 'lecture_day', 'lecture_time',
              'class_gbn', 'lec_age', 'stu_cnt', 'use_gbn']
    readonly_fields = ['lecture_code']


@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ['sta_code', 'sta_name', 'sta_phone', 'local_code', 'use_gbn', 'order_seq']
    list_filter = ['use_gbn', 'local_code']
    search_fields = ['sta_name', 'sta_nickname', 'sta_address']
    ordering = ['order_seq', 'sta_name']
    inlines = [StadiumCoachInline, LectureInline]
    fieldsets = (
        (None, {'fields': ('sta_code', 'sta_name', 'sta_nickname', 'local_code')}),
        ('연락처/주소', {'fields': ('sta_phone', 'sta_address')}),
        ('이미지', {'fields': ('sta_s_img', 'sta_l_img', 'sta_p_img', 'sta_m_img')}),
        ('상세', {'fields': ('sta_desc', 'sta_coach', 'kapa_tot', 'location_url')}),
        ('구분', {'fields': ('use_gbn', 'inve', 'grou', 'three_lecyn', 'order_seq')}),
        ('기타', {'fields': ('insert_dt',)}),
    )


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ['coach_code', 'coach_name', 'coach_level', 'phone', 'use_gbn', 'order_seq']
    list_filter = ['use_gbn', 'coach_level']
    search_fields = ['coach_name', 'phone']
    ordering = ['order_seq', 'coach_name']


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ['lecture_code', 'lecture_title', 'stadium', 'lecture_day',
                    'lecture_time', 'class_gbn', 'class_gbn2', 'stu_cnt', 'use_gbn']
    list_filter = ['use_gbn', 'class_gbn', 'class_gbn2', 'lecture_day']
    search_fields = ['lecture_title', 'lec_age']
    raw_id_fields = ['stadium', 'coach', 't_coach']
    ordering = ['stadium', 'lecture_day', 'lecture_time']


@admin.register(StadiumGoal)
class StadiumGoalAdmin(admin.ModelAdmin):
    list_display = ['stadium', 'sta_year', 'sta_month', 'sta_goal']
    list_filter = ['sta_year', 'sta_month']
    raw_id_fields = ['stadium']


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['uid', 'title', 'discount', 'discount_unit', 'is_use',
                    'use_mode', 'issue_mode', 'start_date', 'end_date']
    list_filter = ['is_use', 'use_mode', 'issue_mode', 'discount_unit']
    search_fields = ['title', 'summary']
    ordering = ['-uid']
