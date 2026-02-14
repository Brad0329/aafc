from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # 상품 카탈로그
    path('goods/', views.goods_list, name='goods_list'),
    path('goods/<int:gd_code>/', views.goods_view, name='goods_view'),

    # 장바구니
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/delete/', views.cart_delete, name='cart_delete'),

    # 주문/결제
    path('order/', views.order_form, name='order_form'),
    path('order/create/', views.order_create, name='order_create'),
    path('kcp/return/', views.shop_kcp_return, name='kcp_return'),

    # 주문조회
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),

    # AJAX
    path('api/option-stock/', views.ajax_option_stock, name='ajax_option_stock'),
]
