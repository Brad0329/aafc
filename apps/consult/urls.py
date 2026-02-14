from django.urls import path
from . import views

app_name = 'consult'

urlpatterns = [
    path('', views.consult_form, name='consult'),
    path('free/', views.consult_free_form, name='free'),
    path('api/search-stadium/', views.ajax_search_stadium, name='search_stadium'),
]
