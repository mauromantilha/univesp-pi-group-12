from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from accounts import views as accounts_views

urlpatterns = [
    # Root redirect
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),

    # Dashboard alias para compatibilidade
    path('dashboard/', accounts_views.dashboard, name='dashboard'),

    # API REST
    path('api/v1/', include('api_urls')),

    # Django Admin
    path('admin/', admin.site.urls),

    # Apps
    path('accounts/', include('accounts.urls')),
    # Atalhos diretos para a área de usuários (admin)
    path('usuarios/', accounts_views.lista_usuarios, name='usuarios_area'),
    path('usuarios/novo/', accounts_views.novo_usuario, name='usuarios_novo_area'),
    path('usuarios/<int:pk>/editar/', accounts_views.editar_usuario, name='usuarios_editar_area'),
    path('processos/', include('processos.urls')),
    path('agenda/', include('agenda.urls')),
    path('jurisprudencia/', include('jurisprudencia.urls')),
    path('ia_preditiva/', include('ia_preditiva.urls')),
    path('financeiro/', include('financeiro.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
