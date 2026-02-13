from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # KCP 결제 결과 처리
    path('kcp/return/', views.kcp_return_view, name='kcp_return'),
]
