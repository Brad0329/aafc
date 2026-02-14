from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('academy/', include('apps.courses.urls')),
    path('enrollment/', include('apps.enrollment.urls')),
    path('payments/', include('apps.payments.urls')),
    path('board/', include('apps.board.urls')),
    path('consult/', include('apps.consult.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
