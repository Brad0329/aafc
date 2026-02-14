from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('total/', views.total_data_view, name='total_data'),
    path('total/excel/', views.total_data_excel, name='total_data_excel'),
    path('coach/', views.coach_stats_view, name='coach_stats'),
    path('coach/excel/', views.coach_stats_excel, name='coach_stats_excel'),
    path('attendance/', views.attendance_report_view, name='attendance_report'),
    path('attendance/excel/', views.attendance_report_excel, name='attendance_report_excel'),
    path('monthly/', views.monthly_stats_view, name='monthly_stats'),
    path('monthly/excel/', views.monthly_stats_excel, name='monthly_stats_excel'),
]
