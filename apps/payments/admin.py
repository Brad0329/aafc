from django.contrib import admin
from .models import PaymentKCP, PaymentFail


@admin.register(PaymentKCP)
class PaymentKCPAdmin(admin.ModelAdmin):
    list_display = ['id', 'ordr_idxx', 'amount', 'res_cd', 'res_msg',
                    'member_num', 'pg_gbn', 'pay_seq', 'insert_dt']
    list_filter = ['pg_gbn', 'res_cd']
    search_fields = ['ordr_idxx', 'member_num', 'good_name']
    ordering = ['-id']


@admin.register(PaymentFail)
class PaymentFailAdmin(admin.ModelAdmin):
    list_display = ['id', 'ordr_idxx', 'res_cd', 'res_msg', 'member_num', 'insert_dt']
    search_fields = ['ordr_idxx', 'member_num']
    ordering = ['-id']
