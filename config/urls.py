from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.admin.views.decorators import staff_member_required

# Custom error handlers
handler404 = 'pages.views.error_404'
handler500 = 'pages.views.error_500'
handler403 = 'pages.views.error_403'

# Import analytics view
from jobs.admin import analytics_view

urlpatterns = [
    path('admin/analytics/', staff_member_required(analytics_view), name='admin_analytics'),
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('', include('jobs.urls')),
    path('', include('companies.urls')),
    path('', include('seekers.urls')),
    path('payments/', include('payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if not settings.DEBUG:
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]