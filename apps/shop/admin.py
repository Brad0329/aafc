from django.contrib import admin
from .models import (
    Category, Product, ProductOption, ProductOptionItem, ProductOptionStock,
    Cart, CartOption, Order, OrderItem, OrderItemOption, OrderDelivery,
    ShopPaymentKCP,
)


# ── Inline 정의 ──

class ProductOptionItemInline(admin.TabularInline):
    model = ProductOptionItem
    extra = 0
    fields = ['opt_item', 'opt_price', 'opt_sort']


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 0
    fields = ['opt_name', 'opt_is_display', 'opt_is_require', 'opt_sort', 'del_ok']
    show_change_link = True


class CartOptionInline(admin.TabularInline):
    model = CartOption
    extra = 0
    fields = ['option_title', 'option_item', 'option_price', 'sort']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['goods_title', 'goods_uid', 'price', 'option_price', 'ea', 'option_txt']
    readonly_fields = ['goods_title', 'goods_uid', 'price', 'option_price', 'ea', 'option_txt']


class OrderDeliveryInline(admin.TabularInline):
    model = OrderDelivery
    extra = 0
    fields = ['delivery_name', 'delivery_no', 'delivery_fee', 'is_delivery', 'delivery_date']


class OrderItemOptionInline(admin.TabularInline):
    model = OrderItemOption
    extra = 0
    fields = ['title', 'item', 'price', 'sort']


# ── Admin 등록 ──

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['cate_code', 'cate_name', 'cate_depth', 'cate_sort', 'cate_parent', 'cate_is_display', 'del_ok']
    list_filter = ['cate_is_display', 'del_ok', 'cate_depth']
    search_fields = ['cate_name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['gd_code', 'gd_name', 'category', 'gd_price', 'gd_market_price',
                    'gd_display', 'gd_is_soldout', 'gd_option_kind', 'gd_delivery_kind', 'del_ok']
    list_filter = ['gd_display', 'gd_is_soldout', 'del_ok', 'gd_option_kind', 'gd_delivery_kind', 'category']
    search_fields = ['gd_name', 'gd_code']
    inlines = [ProductOptionInline]
    fieldsets = (
        ('기본 정보', {'fields': (
            'gd_code', 'category', 'gd_name', 'gd_type', 'gd_state',
        )}),
        ('이미지', {'fields': (
            'gd_img_b', 'gd_img_m', 'gd_img_s', 'gd_desc_img',
        )}),
        ('가격', {'fields': (
            'gd_price', 'gd_market_price', 'gd_original_price', 'gd_pay_price',
            'gd_pay_point', 'gd_point',
        )}),
        ('옵션/재고', {'fields': (
            'gd_option_kind', 'gd_stock',
        )}),
        ('배송', {'fields': (
            'gd_delivery_kind', 'gd_delivery_fee', 'gd_delivery_limit',
            'gd_delivery_policy', 'gd_change_policy',
        )}),
        ('노출/정렬', {'fields': (
            'gd_display', 'gd_is_soldout', 'gd_sort', 'gd_readcnt', 'del_ok',
        )}),
        ('지역', {'fields': (
            'local_code', 'sta_code', 'local_gubun', 'local_gubun2',
        )}),
        ('상품설명', {'fields': ('gd_desc',)}),
        ('제조 정보', {'fields': (
            'gd_product', 'gd_place_of_origin', 'gd_brand',
        )}),
    )


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'opt_name', 'opt_is_display', 'opt_is_require', 'opt_sort', 'del_ok']
    list_filter = ['del_ok', 'opt_is_display']
    search_fields = ['opt_name']
    inlines = [ProductOptionItemInline]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'member', 'product', 'ea', 'option_kind', 'insert_dt']
    list_filter = ['option_kind']
    search_fields = ['member__username']
    inlines = [CartOptionInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_no', 'member', 'settle_price', 'payway', 'state',
                    'is_finish', 'ord_name', 'rcv_name', 'child_id', 'reg_date']
    list_filter = ['state', 'payway', 'is_finish', 'is_cancel']
    search_fields = ['order_no', 'ord_name', 'rcv_name', 'member__username']
    inlines = [OrderItemInline, OrderDeliveryInline]
    readonly_fields = ['reg_date']
    fieldsets = (
        ('주문 기본', {'fields': ('order_no', 'member', 'user_id', 'child_id', 'state', 'is_finish')}),
        ('결제', {'fields': (
            'payway', 'pay_method', 'pg',
            'total_price', 'total_order_price', 'total_option_price',
            'total_delivery_fee', 'total_user_discount', 'total_coupon_discount',
            'use_cmoney', 'settle_price', 'org_settle_price', 'add_cmoney',
        )}),
        ('주문자', {'fields': (
            'ord_name', 'ord_tel', 'ord_mobile',
            'ord_post', 'ord_addr', 'ord_addr_detail', 'ord_email',
        )}),
        ('수령인', {'fields': (
            'rcv_name', 'rcv_tel', 'rcv_mobile',
            'rcv_post', 'rcv_addr', 'rcv_addr_detail', 'rcv_email',
        )}),
        ('기타', {'fields': (
            'order_memo', 'admin_memo', 'mobile_yn',
            'is_confirm', 'is_delivery_finish', 'is_refunded', 'is_cancel',
            'reg_date', 'cancel_date', 'confirm_date',
        )}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'goods_title', 'goods_uid', 'price', 'ea', 'option_price']
    search_fields = ['goods_title', 'order__order_no']
    inlines = [OrderItemOptionInline]


@admin.register(OrderDelivery)
class OrderDeliveryAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'delivery_name', 'delivery_no', 'delivery_fee', 'is_delivery', 'delivery_date']
    list_filter = ['is_delivery', 'delivery_name']
    search_fields = ['order__order_no', 'delivery_no']


@admin.register(ShopPaymentKCP)
class ShopPaymentKCPAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'use_pay_method', 'res_cd', 'amount',
                    'card_name', 'app_no', 'tno', 'member_num', 'insert_dt']
    list_filter = ['use_pay_method', 'res_cd']
    search_fields = ['tno', 'app_no', 'member_num', 'order__order_no']
    readonly_fields = [
        'order', 'use_pay_method', 'res_cd', 'res_msg', 'tno', 'amount',
        'card_cd', 'card_name', 'app_time', 'app_no', 'noinf', 'quota',
        'bank_name', 'depositor', 'account', 'cash_yn', 'cash_authno',
        'noti_id', 'member_num', 'insert_dt',
    ]
