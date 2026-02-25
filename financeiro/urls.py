from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_lancamentos, name='lista_lancamentos'),
    path('novo/', views.novo_lancamento, name='novo_lancamento'),
    path('<int:pk>/', views.detalhe_lancamento, name='detalhe_lancamento'),
    path('<int:pk>/editar/', views.editar_lancamento, name='editar_lancamento'),
    path('<int:pk>/arquivos/upload/', views.upload_arquivos_lancamento, name='upload_arquivos_lancamento'),
    # API interna: retorna cliente de um processo (usado pelo JS do form)
    path('api/processo/<int:processo_pk>/cliente/', views.api_cliente_do_processo, name='api_cliente_do_processo'),
]
