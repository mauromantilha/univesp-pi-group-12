from django.urls import path, include
from rest_framework.routers import DefaultRouter

from accounts.auth_views import login_view, refresh_view, logout_view
from accounts.api_views import UsuarioViewSet
from processos.api_views import (
    ComarcaViewSet, VaraViewSet, TipoProcessoViewSet,
    ClienteViewSet, ProcessoViewSet, MovimentacaoViewSet
)
from agenda.api_views import CompromissoViewSet
from jurisprudencia.api_views import DocumentoViewSet
from ia_preditiva.api_views import AnaliseRiscoViewSet, ia_chat, ia_sugerir
from consulta_tribunais.api_views import TribunalViewSet, ConsultaProcessoViewSet
from financeiro.api_views import LancamentoViewSet, CategoriaFinanceiraViewSet, ContaBancariaViewSet
from financeiro.api_views import RegraCobrancaViewSet, ApontamentoTempoViewSet, FaturaViewSet

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

# Agenda (dois prefixos: compromissos e eventos)
router.register(r'compromissos', CompromissoViewSet, basename='compromisso')
router.register(r'eventos', CompromissoViewSet, basename='evento')

# Jurisprudência
router.register(r'documentos', DocumentoViewSet, basename='documento')

# IA Preditiva
router.register(r'analises', AnaliseRiscoViewSet, basename='analise')
router.register(r'ia/analises', AnaliseRiscoViewSet, basename='ia-analise')

# Consulta Tribunais
router.register(r'tribunais', TribunalViewSet, basename='tribunal')
router.register(r'consultas-processos', ConsultaProcessoViewSet, basename='consulta-processo')
router.register(r'consultas-tribunais', ConsultaProcessoViewSet, basename='consulta-tribunais-legacy')

# Financeiro
router.register(r'financeiro/lancamentos', LancamentoViewSet, basename='lancamento')
router.register(r'financeiro/categorias', CategoriaFinanceiraViewSet, basename='categoria-financeira')
router.register(r'financeiro/contas', ContaBancariaViewSet, basename='conta-bancaria')
router.register(r'financeiro/regras-cobranca', RegraCobrancaViewSet, basename='regra-cobranca')
router.register(r'financeiro/apontamentos-tempo', ApontamentoTempoViewSet, basename='apontamento-tempo')
router.register(r'financeiro/faturas', FaturaViewSet, basename='fatura')

urlpatterns = [
    # Auth endpoints
    path('auth/login/', login_view, name='api-login'),
    path('auth/refresh/', refresh_view, name='token-refresh'),
    path('auth/logout/', logout_view, name='api-logout'),

    # IA Chat
    path('ia/chat/', ia_chat, name='ia-chat'),
    path('ia/sugestoes/sugerir/', ia_sugerir, name='ia-sugestoes'),

    # Router URLs
    path('', include(router.urls)),
]
