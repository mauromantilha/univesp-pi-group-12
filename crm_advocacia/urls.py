from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('processos/', include('processos.urls')),
    path('agenda/', include('agenda.urls')),
    path('jurisprudencia/', include('jurisprudencia.urls')),
    path('ia/', include('ia_preditiva.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
