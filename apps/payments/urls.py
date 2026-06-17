from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # KCP 결제 (Toss 전환으로 비활성 - 뷰/모델/데이터는 보존)
    # path('kcp/return/', views.kcp_return_view, name='kcp_return'),

    # Toss 결제 (수강신청)
    path('toss/enrollment/success/', views.toss_enrollment_success, name='toss_enrollment_success'),
    path('toss/enrollment/fail/', views.toss_enrollment_fail, name='toss_enrollment_fail'),
]
