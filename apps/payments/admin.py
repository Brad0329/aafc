from django.contrib import admin
from .models import PaymentKCP, PaymentFail, PaymentToss


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


@admin.register(PaymentToss)
class PaymentTossAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'amount', 'method', 'status', 'res_cd',
                    'member_num', 'pay_seq', 'insert_dt']
    list_filter = ['method', 'status', 'pg_gbn']
    search_fields = ['order_id', 'payment_key', 'member_num', 'good_name']
    ordering = ['-id']
    readonly_fields = [f.name for f in PaymentToss._meta.fields]
