from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('students.urls')),
    path('reports/', include('reports.urls')),
    path('accounts/', include('accounts.urls')),
    path('services/', include('services.urls')),
    path('core/', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom Error Handlers
handler404 = 'services.views.handler404'
handler500 = 'services.views.handler500'

