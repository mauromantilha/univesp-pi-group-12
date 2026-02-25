from django.urls import path
from . import views

urlpatterns = [
    path('processo/<int:processo_pk>/risco/', views.analise_risco, name='analise_risco'),
    path('sugestoes/', views.sugestoes_jurisprudencia, name='sugestoes_jurisprudencia'),
]
