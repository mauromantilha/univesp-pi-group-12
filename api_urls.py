from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.auth_views import login_view
from accounts.api_views import UsuarioViewSet
from processos.api_views import (
    ComarcaViewSet, VaraViewSet, TipoProcessoViewSet,
    ClienteViewSet, ProcessoViewSet, MovimentacaoViewSet
)
from agenda.api_views import CompromissoViewSet
from jurisprudencia.api_views import DocumentoViewSet
from ia_preditiva.api_views import AnaliseRiscoViewSet
from consulta_tribunais.api_views import TribunalViewSet, ConsultaProcessoViewSet

router = DefaultRouter()

# Accounts
router.register(r'usuarios', UsuarioViewSet, basename='usuario')

# Processos
router.register(r'comarcas', ComarcaViewSet, basename='comarca')
router.register(r'varas', VaraViewSet, basename='vara')
router.register(r'tipos-processo', TipoProcessoViewSet, basename='tipo-processo')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'processos', ProcessoViewSet, basename='processo')
router.register(r'movimentacoes', MovimentacaoViewSet, basename='movimentacao')

# Agenda
router.register(r'compromissos', CompromissoViewSet, basename='compromisso')

# Jurisprudência
router.register(r'documentos', DocumentoViewSet, basename='documento')

# IA Preditiva
router.register(r'analises', AnaliseRiscoViewSet, basename='analise')

# Consulta Tribunais
router.register(r'tribunais', TribunalViewSet, basename='tribunal')
router.register(r'consultas-processos', ConsultaProcessoViewSet, basename='consulta-processo')

urlpatterns = [
    # Auth endpoints
    path('auth/login/', login_view, name='api-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Router URLs
    path('', include(router.urls)),
]
