from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from .views import main_view, ajax_main_consult, robots_txt
from .sitemaps import StaticSitemap, BoardSitemap, ProductSitemap

sitemaps = {
    'static': StaticSitemap,
    'board': BoardSitemap,
    'product': ProductSitemap,
}

urlpatterns = [
    path('', main_view, name='main'),
    path('ajax/main-consult/', ajax_main_consult, name='ajax_main_consult'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
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
path('ba_office/', include('apps.office.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # /fcdata/ 경로로 직접 접근하는 레거시 이미지 서빙 (shop_goods, board 등)
    urlpatterns += static('/fcdata/', document_root=settings.MEDIA_ROOT / 'fcdata')
