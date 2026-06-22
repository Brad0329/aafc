from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('nice/start/', views.nice_start, name='nice_start'),
    path('nice/callback/', views.nice_callback, name='nice_callback'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('id-search/', views.id_search_view, name='id_search'),
    path('pw-search/', views.pw_search_view, name='pw_search'),
    path('mypage/', views.mypage_view, name='mypage'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('child/add/', views.child_add_view, name='child_add'),
    path('child/<int:pk>/edit/', views.child_edit_view, name='child_edit'),
    path('child/<int:pk>/delete/', views.child_delete_view, name='child_delete'),
]
