from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('alim/', views.notification_list, name='notification_list'),
]
