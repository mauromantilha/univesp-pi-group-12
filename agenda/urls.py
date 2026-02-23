from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('novo/', views.novo_compromisso, name='novo_compromisso'),
    path('<int:pk>/editar/', views.editar_compromisso, name='editar_compromisso'),
    path('<int:pk>/excluir/', views.excluir_compromisso, name='excluir_compromisso'),
    path('alertas/', views.alertas, name='alertas'),
]
