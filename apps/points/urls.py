from django.urls import path
from . import views

app_name = 'points'

urlpatterns = [
    path('mypoint/', views.point_list, name='point_list'),
]
