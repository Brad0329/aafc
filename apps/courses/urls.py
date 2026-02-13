from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # 아카데미 섹션
    path('stadium/', views.stadium_list_view, name='stadium_list'),
    path('stadium/<int:sta_code>/', views.stadium_detail_view, name='stadium_detail'),
    path('coach/', views.coach_list_view, name='coach_list'),
    path('program/', views.program_view, name='program'),
    # AAFC 섹션
    path('greeting/', views.greeting_view, name='greeting'),
    path('emblem/', views.emblem_view, name='emblem'),
    path('waytocome/', views.waytocome_view, name='waytocome'),
]
