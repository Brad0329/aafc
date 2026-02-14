from django.contrib import admin
from .models import Board, BoardComment, BoardFile


class BoardFileInline(admin.TabularInline):
    model = BoardFile
    extra = 0
    fields = ['bs_img', 'bs_file', 'bs_downcnt', 'bs_no', 'insert_dt']
    readonly_fields = ['insert_dt']


class BoardCommentInline(admin.TabularInline):
    model = BoardComment
    extra = 0
    fields = ['comment', 'insert_name', 'insert_id', 'insert_dt', 'del_chk']
    readonly_fields = ['insert_dt']


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['b_seq', 'b_gbn', 'b_title', 'insert_name', 'insert_dt', 'b_hit', 'b_notice_yn', 'del_chk']
    list_filter = ['b_gbn', 'del_chk', 'b_notice_yn']
    search_fields = ['b_title', 'b_content', 'insert_name']
    ordering = ['-b_seq']
    inlines = [BoardFileInline, BoardCommentInline]
    fieldsets = (
        (None, {'fields': ('b_seq', 'b_gbn', 'b_title', 'b_content')}),
        ('답글', {'fields': ('b_ref', 'b_level', 'b_step')}),
        ('설정', {'fields': ('b_notice_yn', 'b_hit', 'b_commend', 'del_chk')}),
        ('작성자', {'fields': ('insert_name', 'insert_id', 'insert_type', 'insert_dt', 'insert_ip')}),
    )


@admin.register(BoardComment)
class BoardCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'board', 'b_gbn', 'comment', 'insert_name', 'insert_dt', 'del_chk']
    list_filter = ['b_gbn', 'del_chk']
    search_fields = ['comment', 'insert_name', 'insert_id']
