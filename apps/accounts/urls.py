from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('mypage/', views.mypage_view, name='mypage'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('child/add/', views.child_add_view, name='child_add'),
    path('child/<int:pk>/edit/', views.child_edit_view, name='child_edit'),
    path('child/<int:pk>/delete/', views.child_delete_view, name='child_delete'),
]
