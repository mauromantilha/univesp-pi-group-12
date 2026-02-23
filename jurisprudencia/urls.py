from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_documentos, name='lista_documentos'),
    path('novo/', views.novo_documento, name='novo_documento'),
    path('<int:pk>/', views.detalhe_documento, name='detalhe_documento'),
    path('<int:pk>/editar/', views.editar_documento, name='editar_documento'),
]
