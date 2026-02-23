from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, VaraViewSet, TipoProcessoViewSet, ProcessoViewSet, MovimentacaoViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'varas', VaraViewSet, basename='vara')
router.register(r'tipos-processo', TipoProcessoViewSet, basename='tipoprocesso')
router.register(r'processos', ProcessoViewSet, basename='processo')
router.register(r'movimentacoes', MovimentacaoViewSet, basename='movimentacao')

urlpatterns = [path('', include(router.urls))]
