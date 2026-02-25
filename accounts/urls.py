from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='accounts_dashboard'),
    path('portal/', views.meu_portal, name='meu_portal'),
    path('portal/<int:pk>/', views.portal_usuario, name='portal_usuario'),
    path('perfil/', views.perfil, name='perfil'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/novo/', views.novo_usuario, name='novo_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
]
