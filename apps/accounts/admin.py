from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Member, MemberChild, OutMember


@admin.register(Member)
class MemberAdmin(UserAdmin):
    list_display = ['username', 'name', 'phone', 'email', 'status', 'is_active', 'insert_dt']
    list_filter = ['status', 'is_active', 'sms_consent', 'join_path']
    search_fields = ['username', 'name', 'phone', 'email']
    ordering = ['-insert_dt']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('개인정보', {'fields': ('name', 'email', 'phone', 'tel', 'birth', 'gender')}),
        ('주소', {'fields': ('zipcode', 'address1', 'address2')}),
        ('동의/상태', {'fields': ('sms_consent', 'mail_consent', 'status', 'is_active')}),
        ('인증', {'fields': ('join_ncsafe', 'join_safe_di', 'join_safegbn', 'join_path')}),
        ('권한', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('기타', {'fields': ('login_count', 'failed_count', 'member_code', 'insert_dt', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'password1', 'password2', 'email', 'phone'),
        }),
    )


class MemberChildInline(admin.TabularInline):
    model = MemberChild
    extra = 0
    fields = ['name', 'birth', 'gender', 'school', 'grade', 'phone', 'course_state', 'status']


@admin.register(MemberChild)
class MemberChildAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'birth', 'school', 'grade', 'course_state', 'status']
    list_filter = ['course_state', 'status', 'gender']
    search_fields = ['name', 'parent__username', 'parent__name']
    raw_id_fields = ['parent']


@admin.register(OutMember)
class OutMemberAdmin(admin.ModelAdmin):
    list_display = ['member_id', 'member_name', 'out_dt']
    search_fields = ['member_id', 'member_name']
