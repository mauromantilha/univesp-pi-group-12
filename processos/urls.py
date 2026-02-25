from django.urls import path
from . import views

urlpatterns = [
    # Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/novo/', views.novo_cliente, name='novo_cliente'),
    path('clientes/<int:pk>/', views.detalhe_cliente, name='detalhe_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    # Processos
    path('', views.lista_processos, name='lista_processos'),
    path('novo/', views.novo_processo, name='novo_processo'),
    path('<int:pk>/', views.detalhe_processo, name='detalhe_processo'),
    path('<int:pk>/editar/', views.editar_processo, name='editar_processo'),
    path('<int:processo_pk>/movimentacao/', views.nova_movimentacao, name='nova_movimentacao'),
    path('<int:pk>/arquivos/upload/', views.upload_arquivos_processo, name='upload_arquivos_processo'),
    # Carga de trabalho
    path('carga-trabalho/', views.carga_trabalho, name='carga_trabalho'),
    # Entidades legais
    path('comarcas/', views.lista_comarcas, name='lista_comarcas'),
    path('comarcas/nova/', views.nova_comarca, name='nova_comarca'),
    path('varas/', views.lista_varas, name='lista_varas'),
    path('varas/nova/', views.nova_vara, name='nova_vara'),
    path('tipos/', views.lista_tipos, name='lista_tipos'),
    path('tipos/novo/', views.novo_tipo, name='novo_tipo'),
]
