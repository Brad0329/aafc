from django.urls import path
from . import views

app_name = 'board'

urlpatterns = [
    path('comment/add/', views.comment_add, name='comment_add'),
    path('comment/<int:bc_seq>/delete/', views.comment_delete, name='comment_delete'),
    path('<str:board_id>/', views.board_list, name='list'),
    path('<str:board_id>/write/', views.board_write, name='write'),
    path('<str:board_id>/<int:b_seq>/', views.board_view, name='view'),
    path('<str:board_id>/<int:b_seq>/edit/', views.board_edit, name='edit'),
    path('<str:board_id>/<int:b_seq>/delete/', views.board_delete, name='delete'),
]
