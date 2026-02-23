from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnaliseRiscoViewSet, SugestaoJurisprudenciaViewSet

router = DefaultRouter()
router.register(r'analises', AnaliseRiscoViewSet, basename='analise')
router.register(r'sugestoes', SugestaoJurisprudenciaViewSet, basename='sugestao')

urlpatterns = [path('', include(router.urls))]
