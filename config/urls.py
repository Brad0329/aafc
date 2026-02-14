from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/board/Y/', permanent=False)),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('academy/', include('apps.courses.urls')),
    path('enrollment/', include('apps.enrollment.urls')),
    path('payments/', include('apps.payments.urls')),
    path('board/', include('apps.board.urls')),
    path('consult/', include('apps.consult.urls')),
    path('shop/', include('apps.shop.urls')),
    path('points/', include('apps.points.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # /fcdata/ 경로로 직접 접근하는 레거시 이미지 서빙 (shop_goods, board 등)
    urlpatterns += static('/fcdata/', document_root=settings.MEDIA_ROOT / 'fcdata')
