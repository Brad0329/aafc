from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # KCP 결제 (Toss 전환으로 비활성 - 뷰/모델/데이터는 보존)
    # path('kcp/return/', views.kcp_return_view, name='kcp_return'),

    # Toss 결제 (수강신청)
    path('toss/enrollment/success/', views.toss_enrollment_success, name='toss_enrollment_success'),
    path('toss/enrollment/fail/', views.toss_enrollment_fail, name='toss_enrollment_fail'),

    # 수강료 결제 (마이페이지) — 원본 mypage payment_new.asp
    path('tuition/', views.tuition_payment, name='tuition_payment'),
    path('tuition/success/', views.tuition_payment_success, name='tuition_payment_success'),
    path('tuition/fail/', views.tuition_payment_fail, name='tuition_payment_fail'),
]
