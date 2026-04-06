from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('', include('jobs.urls')),
    path('', include('companies.urls')),
    path('', include('seekers.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)