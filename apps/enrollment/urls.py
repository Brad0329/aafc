from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    # Step 1: 자녀선택 → 권역 → 구장 → 강좌 → 시작일
    path('apply/', views.apply_step1_view, name='apply_step1'),

    # AJAX endpoints for Step 1
    path('api/stadiums/', views.ajax_load_stadiums, name='ajax_stadiums'),
    path('api/lectures/', views.ajax_load_lectures, name='ajax_lectures'),
    path('api/course-days/', views.ajax_course_days, name='ajax_course_days'),
    path('api/recommend-check/', views.ajax_recommend_check, name='ajax_recommend_check'),
    path('api/waitlist-add/', views.ajax_waitlist_add, name='ajax_waitlist_add'),

    # Step 2: 할인/프로모션 확인
    path('apply/step2/', views.apply_step2_view, name='apply_step2'),
    path('api/promotions/', views.ajax_load_promotions, name='ajax_promotions'),

    # Step 3: 결제 확인
    path('apply/step3/', views.apply_step3_view, name='apply_step3'),

    # 결제내역 (마이페이지)
    path('payment-history/', views.payment_history_view, name='payment_history'),
]
