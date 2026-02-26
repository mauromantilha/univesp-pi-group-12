import logging
import os
import re
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from agenda.models import Compromisso
from accounts.permissions import IsAdvogadoOuAdministradorWrite
from consulta_tribunais.models import ConsultaProcesso
from consulta_tribunais.services.groq_service import GroqService
from financeiro.models import Lancamento
from jurisprudencia.models import Documento
from processos.models import Cliente, Processo

from .models import AnaliseRisco, IAEventoSistema
from .serializers import AnaliseRiscoSerializer, IAEventoSistemaSerializer

logger = logging.getLogger(__name__)


class IAChatRateThrottle(UserRateThrottle):
    scope = 'ia_chat'


def _resposta_fallback_ia():
    return (
        'IA indisponível no momento. Verifique a configuração da chave GROQ_API_KEY '
        'ou tente novamente em instantes.'
    )


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _tokenizar(texto):
    if not texto:
        return set()
    stop = {
        'para', 'com', 'das', 'dos', 'que', 'uma', 'por', 'não', 'nos',
        'nas', 'ser', 'sua', 'seu', 'sobre', 'entre', 'processo', 'cliente',
        'demanda', 'caso', 'juridico', 'jurídico', 'legal', 'ação', 'acao',
    }
    termos = {
        t for t in re.split(r'[^\wÀ-ÿ]+', str(texto).lower())
        if len(t) >= 4 and t not in stop
    }
    return termos


def _similaridade(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    den = max(len(a), len(b))
    if den == 0:
        return 0.0
    return inter / den


def _nivel_risco(probabilidade_sucesso):
    valor = float(probabilidade_sucesso or 0)
    if valor >= 70:
        return 'baixo'
    if valor >= 40:
        return 'medio'
    return 'alto'


def _user_processos_queryset(user):
    qs = Processo.objects.select_related('cliente', 'tipo', 'advogado').prefetch_related('movimentacoes').all()
    if user.is_administrador():
        return qs
    return qs.filter(
        Q(advogado=user)
        | Q(responsaveis__usuario=user, responsaveis__ativo=True)
    ).distinct()


def _user_clientes_queryset(user):
    qs = Cliente.objects.all()
    if user.is_administrador():
        return qs
    return qs.filter(
        Q(processos__advogado=user)
        | Q(processos__responsaveis__usuario=user, processos__responsaveis__ativo=True)
        | Q(responsavel=user)
    ).distinct()


def _buscar_jurisprudencia_superior(usuario, termos, limite=8):
    termos = [t for t in termos if t]
    if not termos:
        return []

    tribunal_filter = (
        Q(tribunal__icontains='STF')
        | Q(tribunal__icontains='STJ')
        | Q(tribunal__icontains='TST')
        | Q(tags__icontains='STF')
        | Q(tags__icontains='STJ')
        | Q(tags__icontains='TST')
    )

    docs_qs = Documento.objects.filter(tribunal_filter)
    if not usuario.is_administrador():
        docs_qs = docs_qs.filter(
            Q(processo_referencia__advogado=usuario)
            | Q(processo_referencia__responsaveis__usuario=usuario, processo_referencia__responsaveis__ativo=True)
            | Q(adicionado_por=usuario)
            | Q(processo_referencia__isnull=True)
        ).distinct()

    termo_query = Q()
    for termo in termos:
        termo_query |= Q(titulo__icontains=termo)
        termo_query |= Q(conteudo__icontains=termo)
        termo_query |= Q(tags__icontains=termo)

    docs = docs_qs.filter(termo_query).order_by('-criado_em')[:limite]
    resultado = []
    for doc in docs:
        resultado.append({
            'fonte': 'documento_interno',
            'id': doc.id,
            'titulo': doc.titulo,
            'tribunal': doc.tribunal,
            'categoria': doc.categoria,
            'data_decisao': doc.data_decisao,
            'resumo': (doc.conteudo or '')[:280],
        })

    consultas = ConsultaProcesso.objects.select_related('tribunal').filter(
        tribunal__sigla__in=['STF', 'STJ', 'TST'],
        status='sucesso',
    )
    if not usuario.is_administrador():
        consultas = consultas.filter(usuario=usuario)

    for consulta in consultas.order_by('-data_consulta')[:limite]:
        dados = consulta.dados_processo or {}
        blob = f"{dados.get('classe', '')} {' '.join(dados.get('assuntos', []) if isinstance(dados.get('assuntos'), list) else [])}"
        tokens = _tokenizar(blob)
        if not any(t in tokens for t in termos):
            continue
        resultado.append({
            'fonte': 'consulta_tribunal_superior',
            'consulta_id': consulta.id,
            'tribunal': consulta.tribunal.sigla,
            'numero_processo': consulta.numero_processo,
            'classe': dados.get('classe'),
            'assuntos': dados.get('assuntos'),
            'analise_ia': consulta.analise_ia,
        })
        if len(resultado) >= limite:
            break

    return resultado[:limite]


def _movimentacao_favoravel(processo):
    favoravel_kw = [
        'procedente', 'provido', 'ganho', 'deferido', 'acolhido', 'favorável', 'favoravel'
    ]
    for mov in processo.movimentacoes.all():
        texto = f"{mov.titulo or ''} {mov.descricao or ''}".lower()
        if any(k in texto for k in favoravel_kw):
            return True
    return False


def _heuristica_revisao_texto(texto):
    texto = (texto or '').strip()
    erros_gramatica = []
    erros_logica = []
    riscos_indeferimento = []
    sugestoes = []

    if not texto:
        return {
            'score_qualidade': 0,
            'erros_gramatica': ['Texto da peça está vazio.'],
            'erros_logica': ['Não há argumentos jurídicos para análise.'],
            'riscos_indeferimento': ['Peça vazia pode ser indeferida liminarmente.'],
            'sugestoes': ['Escreva a estrutura mínima: fatos, fundamentos e pedidos.'],
        }

    if '  ' in texto:
        erros_gramatica.append('Há espaços duplos no texto.')
    if re.search(r'\.{4,}', texto):
        erros_gramatica.append('Pontuação excessiva (reticências em excesso).')
    if re.search(r'\bnao\b', texto.lower()) and 'não' not in texto.lower():
        erros_gramatica.append('Use acentuação adequada: “não”.')

    texto_lower = texto.lower()
    if 'dos fatos' not in texto_lower and 'fatos' not in texto_lower:
        erros_logica.append('A peça não evidencia seção de fatos.')
    if 'do direito' not in texto_lower and 'fundament' not in texto_lower:
        erros_logica.append('A peça não evidencia fundamentação jurídica.')
    if 'pedido' not in texto_lower and 'requer' not in texto_lower:
        erros_logica.append('A peça não evidencia seção de pedidos.')

    if 'art.' not in texto_lower and 'artigo' not in texto_lower and 'lei' not in texto_lower:
        riscos_indeferimento.append('Ausência de base legal explícita pode fragilizar o pedido.')
    if 'prova' not in texto_lower and 'documento' not in texto_lower:
        riscos_indeferimento.append('Não há menção de provas/documentos de suporte.')
    if len(texto.split()) < 120:
        riscos_indeferimento.append('Texto muito curto para peça processual completa.')

    if not erros_gramatica:
        sugestoes.append('Gramática geral está adequada.')
    else:
        sugestoes.append('Revisar ortografia, acentuação e pontuação antes de protocolar.')

    if not erros_logica:
        sugestoes.append('Estrutura argumentativa está razoável.')
    else:
        sugestoes.append('Estruture com tópicos: fatos, direito, pedidos, provas e requerimentos finais.')

    if riscos_indeferimento:
        sugestoes.append('Antes do protocolo, valide competência, legitimidade e documentos obrigatórios.')

    score = 100
    score -= min(30, len(erros_gramatica) * 8)
    score -= min(35, len(erros_logica) * 12)
    score -= min(35, len(riscos_indeferimento) * 10)
    score = max(0, min(100, score))

    return {
        'score_qualidade': score,
        'erros_gramatica': erros_gramatica,
        'erros_logica': erros_logica,
        'riscos_indeferimento': riscos_indeferimento,
        'sugestoes': sugestoes,
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([IAChatRateThrottle])
def ia_chat(request):
    """
    Endpoint de chat jurídico com IA.
    Recebe { "mensagem": "...", "historico": [{role, content}] }.
    """
    mensagem = request.data.get('mensagem', '').strip()
    historico = request.data.get('historico') or []
    if not mensagem:
        return Response({'error': 'Campo "mensagem" obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        return Response(
            {'resposta': _resposta_fallback_ia(), 'fallback': True},
            status=status.HTTP_200_OK,
        )

    try:
        mensagens = [
            {
                'role': 'system',
                'content': (
                    'Você é um assistente jurídico brasileiro especializado em contencioso e consultivo. '
                    'Responda de forma objetiva, técnica e clara, com alertas de risco processual quando cabível.'
                ),
            }
        ]
        for item in historico[-8:]:
            role = item.get('role')
            content = (item.get('content') or '').strip()
            if role in {'assistant', 'user'} and content:
                mensagens.append({'role': role, 'content': content})
        mensagens.append({'role': 'user', 'content': mensagem})

        groq = GroqService(groq_api_key)
        completion = groq.client.chat.completions.create(
            messages=mensagens,
            model=groq.model,
            temperature=0.25,
            max_tokens=1700,
        )
        resposta = completion.choices[0].message.content
        return Response({'resposta': resposta})
    except Exception:
        logger.exception('Falha na integração com IA no endpoint ia_chat')
        IAEventoSistema.objects.create(
            tipo='ia',
            severidade='alerta',
            mensagem='Falha no endpoint de chat IA',
            rota='/api/v1/ia/chat/',
            detalhes={'usuario': request.user.id},
            criado_por=request.user,
        )
        return Response(
            {'resposta': _resposta_fallback_ia(), 'fallback': True},
            status=status.HTTP_200_OK,
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ia_sugerir(request):
    processo_id = _safe_int(request.data.get('processo_id') if request.method == 'POST' else request.query_params.get('processo_id'))
    cliente_id = _safe_int(request.data.get('cliente_id') if request.method == 'POST' else request.query_params.get('cliente_id'))
    termo = (
        request.data.get('q')
        or request.data.get('texto')
        or request.data.get('mensagem')
        or request.query_params.get('q')
        or request.query_params.get('texto')
        or ''
    ).strip()

    processos_qs = _user_processos_queryset(request.user)
    clientes_qs = _user_clientes_queryset(request.user)

    if processo_id and not termo:
        processo = processos_qs.filter(id=processo_id).first()
        if processo:
            termo = ' '.join(filter(None, [
                processo.numero,
                processo.objeto,
                processo.tipo.nome if processo.tipo else '',
                processo.cliente.demanda if processo.cliente else '',
            ]))

    if cliente_id and not termo:
        cliente = clientes_qs.filter(id=cliente_id).first()
        if cliente:
            termo = ' '.join(filter(None, [cliente.nome, cliente.demanda, cliente.observacoes]))

    if not termo:
        return Response({'sugestoes': []}, status=status.HTTP_200_OK)

    tokens = list(_tokenizar(termo))[:6]
    query = Q()
    for t in tokens or [termo]:
        query |= Q(titulo__icontains=t) | Q(conteudo__icontains=t) | Q(tags__icontains=t)

    qs = Documento.objects.filter(query)
    if not request.user.is_administrador():
        qs = qs.filter(
            Q(processo_referencia__advogado=request.user)
            | Q(processo_referencia__responsaveis__usuario=request.user, processo_referencia__responsaveis__ativo=True)
            | Q(adicionado_por=request.user)
            | Q(processo_referencia__isnull=True)
        ).distinct()

    sugestoes = []
    for doc in qs.order_by('-criado_em')[:12]:
        sugestoes.append({
            'id': doc.id,
            'titulo': doc.titulo,
            'categoria': doc.categoria,
            'tribunal': doc.tribunal,
            'data_decisao': doc.data_decisao,
            'resumo': (doc.conteudo or '')[:320],
            'tags': doc.tags,
        })

    jurisprudencia_superior = _buscar_jurisprudencia_superior(request.user, tokens, limite=8)

    return Response({
        'sugestoes': sugestoes,
        'jurisprudencia_superior': jurisprudencia_superior,
    }, status=status.HTTP_200_OK)


class AnaliseRiscoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnaliseRisco.objects.select_related('processo').all()
    serializer_class = AnaliseRiscoSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_administrador():
            return queryset
        return queryset.filter(
            Q(processo__advogado=self.request.user)
            | Q(processo__responsaveis__usuario=self.request.user, processo__responsaveis__ativo=True)
        ).distinct()

    def _resolver_processo(self, processo_id):
        qs = _user_processos_queryset(self.request.user)
        processo = qs.filter(id=processo_id).first()
        if not processo:
            raise PermissionDenied('Você não tem permissão para analisar este processo.')
        return processo

    def _similares_internos(self, processo=None, demanda=''):
        base_qs = _user_processos_queryset(self.request.user)
        if processo:
            base_qs = base_qs.exclude(id=processo.id)
            referencia = ' '.join(filter(None, [
                processo.objeto,
                processo.cliente.demanda if processo.cliente else '',
                processo.tipo.nome if processo.tipo else '',
            ]))
        else:
            referencia = demanda

        tokens_ref = _tokenizar(referencia)
        similares = []
        for item in base_qs.select_related('cliente', 'tipo').order_by('-criado_em')[:250]:
            texto_item = ' '.join(filter(None, [
                item.objeto,
                item.cliente.demanda if item.cliente else '',
                item.tipo.nome if item.tipo else '',
            ]))
            score = _similaridade(tokens_ref, _tokenizar(texto_item))
            if score < 0.2:
                continue
            similares.append({
                'id': item.id,
                'numero': item.numero,
                'cliente_nome': item.cliente.nome if item.cliente else '-',
                'tipo_nome': item.tipo.nome if item.tipo else '-',
                'status': item.status,
                'score_similaridade': round(score * 100, 1),
            })
        similares.sort(key=lambda x: x['score_similaridade'], reverse=True)
        return similares[:12]

    @action(detail=False, methods=['post'])
    def analisar_processo(self, request):
        processo_id = _safe_int(request.data.get('processo_id'))
        if not processo_id:
            return Response({'error': 'processo_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        processo = self._resolver_processo(processo_id)
        similares = self._similares_internos(processo=processo)

        total_similares = len(similares)
        finalizados_ids = [s['id'] for s in similares]
        finalizados_qs = _user_processos_queryset(request.user).filter(id__in=finalizados_ids, status='finalizado')
        vitorias = sum(1 for p in finalizados_qs if _movimentacao_favoravel(p))

        base = 55.0
        if total_similares > 0:
            base = 45.0 + (vitorias / max(total_similares, 1)) * 45.0
        if processo.status == 'suspenso':
            base -= 10
        if processo.status == 'arquivado':
            base -= 20
        if processo.etapa_workflow in {'execucao', 'encerramento'}:
            base += 5

        hoje = timezone.localdate()
        prazos_atrasados = processo.compromissos.filter(tipo='prazo', status='pendente', data__lt=hoje).count()
        tarefas_atrasadas = processo.tarefas.filter(status='pendente', prazo_em__lt=timezone.now()).count()
        base -= min(20, prazos_atrasados * 6)
        base -= min(15, tarefas_atrasadas * 4)

        prob = round(max(5.0, min(95.0, base)), 2)

        fatores_risco = []
        pontos_favoraveis = []
        recomendacoes = []

        if prazos_atrasados:
            fatores_risco.append(f'{prazos_atrasados} prazo(s) em atraso no processo.')
            recomendacoes.append('Regularizar imediatamente os prazos pendentes e atualizar a agenda.')
        if tarefas_atrasadas:
            fatores_risco.append(f'{tarefas_atrasadas} tarefa(s) vencida(s) sem conclusão.')
        if total_similares == 0:
            fatores_risco.append('Baixa base histórica interna de casos similares.')
            recomendacoes.append('Adicionar precedentes internos e documentos de apoio para fortalecer a tese.')
        if vitorias > 0:
            pontos_favoraveis.append(f'Histórico interno com {vitorias} caso(s) similar(es) favorável(is).')
        if processo.valor_causa:
            pontos_favoraveis.append('Valor da causa definido, facilitando estratégia de negociação.')
        if processo.tipo_caso == 'consultivo':
            pontos_favoraveis.append('Caso consultivo com potencial de condução preventiva de risco.')
        if not fatores_risco:
            pontos_favoraveis.append('Não foram encontrados riscos operacionais críticos imediatos.')

        termos = list(_tokenizar(' '.join(filter(None, [
            processo.objeto,
            processo.tipo.nome if processo.tipo else '',
            processo.cliente.demanda if processo.cliente else '',
        ]))))[:8]
        jurisprudencias = _buscar_jurisprudencia_superior(request.user, termos, limite=8)

        justificativa = (
            f'Probabilidade baseada em {total_similares} similar(es) interno(s), '
            f'com {vitorias} desfecho(s) favorável(is), considerando status, '
            f'etapa do workflow e pendências de prazo/tarefas.'
        )

        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            try:
                prompt = (
                    f'Analise juridicamente o processo {processo.numero}. '\
                    f'Objeto: {processo.objeto}. '\
                    f'Tipo caso: {processo.tipo_caso}. '\
                    f'Prazos atrasados: {prazos_atrasados}. '\
                    f'Tarefas atrasadas: {tarefas_atrasadas}. '\
                    f'Similares internos: {total_similares}; vitórias: {vitorias}. '\
                    'Retorne resumo objetivo em português com riscos e próximos passos.'
                )
                groq = GroqService(groq_api_key)
                completion = groq.client.chat.completions.create(
                    messages=[
                        {
                            'role': 'system',
                            'content': (
                                'Você é um advogado sênior de contencioso. '
                                'Produza análise objetiva com foco em risco processual e estratégia.'
                            ),
                        },
                        {'role': 'user', 'content': prompt},
                    ],
                    model=groq.model,
                    temperature=0.2,
                    max_tokens=900,
                )
                justificativa = completion.choices[0].message.content or justificativa
            except Exception:
                logger.exception('Falha em resumo IA para analisar_processo')

        analise, _ = AnaliseRisco.objects.get_or_create(processo=processo)
        analise.probabilidade_exito = prob
        analise.justificativa = justificativa
        analise.processos_similares = total_similares
        analise.vitorias_similares = vitorias
        analise.save()

        return Response({
            'processo_id': processo.id,
            'processo_numero': processo.numero,
            'cliente_id': processo.cliente_id,
            'cliente_nome': processo.cliente.nome if processo.cliente else '-',
            'probabilidade_sucesso': prob,
            'probabilidade_exito': prob,
            'nivel_risco': _nivel_risco(prob),
            'processos_similares': total_similares,
            'vitorias_similares': vitorias,
            'fatores_risco': fatores_risco,
            'pontos_favoraveis': pontos_favoraveis,
            'recomendacoes': recomendacoes,
            'justificativa': justificativa,
            'similares_internos': similares,
            'jurisprudencia_superior': jurisprudencias,
        })

    @action(detail=False, methods=['post'], url_path='analisar')
    def analisar(self, request):
        return self.analisar_processo(request)

    @action(detail=False, methods=['post'], url_path='cliente')
    def analisar_cliente(self, request):
        cliente_id = _safe_int(request.data.get('cliente_id'))
        if not cliente_id:
            return Response({'error': 'cliente_id é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

        cliente = _user_clientes_queryset(request.user).filter(id=cliente_id).first()
        if not cliente:
            raise PermissionDenied('Cliente não disponível para seu perfil.')

        processos_cliente = _user_processos_queryset(request.user).filter(cliente=cliente)
        total_processos = processos_cliente.count()
        ativos = processos_cliente.filter(status='em_andamento').count()
        finalizados = processos_cliente.filter(status='finalizado').count()
        arquivados = processos_cliente.filter(status='arquivado').count()

        demanda = (request.data.get('demanda') or cliente.demanda or '').strip()
        similares_demanda = self._similares_internos(demanda=demanda)

        base = 60.0
        if total_processos == 0:
            base = 45.0
        else:
            base += min(20.0, finalizados * 4.0)
            base -= min(15.0, arquivados * 3.0)

        prazos_criticos = Compromisso.objects.filter(
            processo__cliente=cliente,
            tipo='prazo',
            status='pendente',
            data__lte=timezone.localdate() + timedelta(days=3),
        ).count()
        base -= min(20, prazos_criticos * 4)

        prob = round(max(5.0, min(95.0, base)), 2)

        termos = list(_tokenizar(' '.join(filter(None, [cliente.demanda, cliente.observacoes, demanda]))))[:8]
        jurisprudencias = _buscar_jurisprudencia_superior(request.user, termos, limite=8)

        return Response({
            'cliente_id': cliente.id,
            'cliente_nome': cliente.nome,
            'demanda': demanda,
            'probabilidade_sucesso': prob,
            'nivel_risco': _nivel_risco(prob),
            'resumo': {
                'total_processos': total_processos,
                'ativos': ativos,
                'finalizados': finalizados,
                'arquivados': arquivados,
                'prazos_criticos_3_dias': prazos_criticos,
            },
            'similares_internos': similares_demanda,
            'jurisprudencia_superior': jurisprudencias,
            'recomendacoes': [
                'Priorizar regularização de prazos críticos do cliente.',
                'Usar histórico interno de demandas similares na estratégia de atendimento.',
                'Padronizar narrativa inicial da demanda para reduzir inconsistências em peças.',
            ],
        })

    @action(detail=False, methods=['post'], url_path='demanda')
    def analisar_demanda(self, request):
        demanda = (request.data.get('demanda') or '').strip()
        if not demanda:
            return Response({'error': 'Campo demanda é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        similares = self._similares_internos(demanda=demanda)
        finalizados_ids = [s['id'] for s in similares]
        finalizados_qs = _user_processos_queryset(request.user).filter(id__in=finalizados_ids, status='finalizado')
        vitorias = sum(1 for p in finalizados_qs if _movimentacao_favoravel(p))
        total = len(similares)

        prob = 50.0
        if total:
            prob = 40.0 + (vitorias / max(total, 1)) * 50.0
        prob = round(max(5.0, min(95.0, prob)), 2)

        termos = list(_tokenizar(demanda))[:8]
        jurisprudencias = _buscar_jurisprudencia_superior(request.user, termos, limite=8)

        return Response({
            'demanda': demanda,
            'probabilidade_sucesso': prob,
            'nivel_risco': _nivel_risco(prob),
            'similares_internos': similares,
            'resumo_similares': {
                'total': total,
                'vitorias_estimadas': vitorias,
            },
            'jurisprudencia_superior': jurisprudencias,
            'recomendacoes': [
                'Estruturar a tese inicial com base nos similares mais aderentes.',
                'Mapear prova documental desde o primeiro atendimento do cliente.',
                'Validar risco de improcedência para pedidos sem lastro probatório suficiente.',
            ],
        })

    @action(detail=False, methods=['post'], url_path='similares-internos')
    def similares_internos(self, request):
        processo_id = _safe_int(request.data.get('processo_id'))
        demanda = (request.data.get('demanda') or '').strip()
        processo = None
        if processo_id:
            processo = self._resolver_processo(processo_id)
        if not processo and not demanda:
            return Response({'error': 'Informe processo_id ou demanda.'}, status=status.HTTP_400_BAD_REQUEST)

        similares = self._similares_internos(processo=processo, demanda=demanda)
        return Response({'similares_internos': similares})

    @action(detail=False, methods=['post'], url_path='jurisprudencia-superior')
    def jurisprudencia_superior(self, request):
        termos = []
        processo_id = _safe_int(request.data.get('processo_id'))
        cliente_id = _safe_int(request.data.get('cliente_id'))
        demanda = (request.data.get('demanda') or '').strip()

        if processo_id:
            processo = self._resolver_processo(processo_id)
            termos.extend(list(_tokenizar(' '.join(filter(None, [
                processo.objeto,
                processo.tipo.nome if processo.tipo else '',
                processo.cliente.demanda if processo.cliente else '',
            ])))))
        if cliente_id:
            cliente = _user_clientes_queryset(request.user).filter(id=cliente_id).first()
            if not cliente:
                raise PermissionDenied('Cliente não disponível para seu perfil.')
            termos.extend(list(_tokenizar(' '.join(filter(None, [cliente.demanda, cliente.observacoes])))))
        if demanda:
            termos.extend(list(_tokenizar(demanda)))

        termos = list(dict.fromkeys(termos))[:12]
        if not termos:
            return Response({'error': 'Informe processo_id, cliente_id ou demanda.'}, status=status.HTTP_400_BAD_REQUEST)

        resultado = _buscar_jurisprudencia_superior(request.user, termos, limite=12)
        return Response({'termos': termos, 'jurisprudencia_superior': resultado})

    @action(detail=False, methods=['post'], url_path='redigir-peca')
    def redigir_peca(self, request):
        tipo_peca = (request.data.get('tipo_peca') or 'peticao').strip().lower()
        processo_id = _safe_int(request.data.get('processo_id'))
        objetivo = (request.data.get('objetivo') or '').strip()
        tese = (request.data.get('tese_principal') or '').strip()
        pedidos = request.data.get('pedidos') or []

        processo = None
        contexto = ''
        if processo_id:
            processo = self._resolver_processo(processo_id)
            contexto = (
                f'Processo {processo.numero}; cliente {processo.cliente.nome}; '
                f'tipo {processo.tipo.nome if processo.tipo else "-"}; objeto: {processo.objeto}'
            )

        if not objetivo and not tese and not processo:
            return Response(
                {'error': 'Informe ao menos processo_id, objetivo ou tese_principal.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pedidos_txt = ''
        if isinstance(pedidos, list) and pedidos:
            pedidos_txt = '\n'.join([f'- {p}' for p in pedidos if p])

        template = (
            f'EXCELENTÍSSIMO(A) SENHOR(A) JUIZ(A) DE DIREITO\n\n'
            f'Processo: {processo.numero if processo else "[informar]"}\n\n'
            'I. DOS FATOS\n'
            f'{objetivo or "Descrever os fatos relevantes com cronologia objetiva."}\n\n'
            'II. DO DIREITO\n'
            f'{tese or "Apresentar fundamentos legais, doutrinários e jurisprudenciais."}\n\n'
            'III. DOS PEDIDOS\n'
            f'{pedidos_txt or "- Requer o acolhimento integral dos pedidos formulados."}\n\n'
            'IV. REQUERIMENTOS FINAIS\n'
            '- Protesta provar o alegado por todos os meios de prova em direito admitidos.\n'
            '- Termos em que, pede deferimento.'
        )

        texto = template
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            try:
                prompt = (
                    f'Redija uma minuta de {tipo_peca} em português jurídico formal.\n'
                    f'Contexto: {contexto}\n'
                    f'Objetivo: {objetivo}\n'
                    f'Tese principal: {tese}\n'
                    f'Pedidos:\n{pedidos_txt or "- conforme contexto"}\n'
                    'Estruture em Fatos, Direito, Pedidos e Requerimentos Finais.'
                )
                groq = GroqService(groq_api_key)
                completion = groq.client.chat.completions.create(
                    messages=[
                        {
                            'role': 'system',
                            'content': 'Você é um redator jurídico brasileiro especializado em peças processuais.',
                        },
                        {'role': 'user', 'content': prompt},
                    ],
                    model=groq.model,
                    temperature=0.2,
                    max_tokens=1800,
                )
                texto_ia = (completion.choices[0].message.content or '').strip()
                if texto_ia:
                    texto = texto_ia
            except Exception:
                logger.exception('Falha em redigir_peca com IA')
                IAEventoSistema.objects.create(
                    tipo='ia',
                    severidade='alerta',
                    mensagem='Falha ao redigir peça com IA',
                    rota='/api/v1/ia/analises/redigir-peca/',
                    detalhes={'processo_id': processo_id, 'tipo_peca': tipo_peca},
                    criado_por=request.user,
                )

        return Response({
            'tipo_peca': tipo_peca,
            'processo_id': processo.id if processo else None,
            'texto': texto,
            'contexto': contexto,
        })

    @action(detail=False, methods=['post'], url_path='revisar-peca')
    def revisar_peca(self, request):
        texto = request.data.get('texto') or ''
        if not str(texto).strip():
            return Response({'error': 'Campo texto é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        tipo_peca = (request.data.get('tipo_peca') or 'peticao').strip().lower()
        revisao = _heuristica_revisao_texto(texto)

        comentario_ia = ''
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            try:
                prompt = (
                    f'Revise a seguinte peça ({tipo_peca}) e aponte em tópicos: '\
                    '1) gramática, 2) lógica jurídica, 3) riscos de indeferimento, 4) melhorias de redação.\n\n'
                    f'TEXTO:\n{texto[:6000]}'
                )
                groq = GroqService(groq_api_key)
                completion = groq.client.chat.completions.create(
                    messages=[
                        {
                            'role': 'system',
                            'content': 'Você é revisor jurídico técnico e objetivo. Responda em português.',
                        },
                        {'role': 'user', 'content': prompt},
                    ],
                    model=groq.model,
                    temperature=0.15,
                    max_tokens=1200,
                )
                comentario_ia = completion.choices[0].message.content or ''
            except Exception:
                logger.exception('Falha em revisar_peca com IA')

        return Response({
            'tipo_peca': tipo_peca,
            **revisao,
            'comentario_ia': comentario_ia,
        })

    @action(detail=False, methods=['get'], url_path='monitoramento')
    def monitoramento(self, request):
        hoje = timezone.localdate()
        limite = hoje + timedelta(days=7)

        processos_qs = _user_processos_queryset(request.user)
        processo_ids = list(processos_qs.values_list('id', flat=True))

        prazos_qs = Compromisso.objects.filter(
            processo_id__in=processo_ids,
            tipo='prazo',
            status='pendente',
        ).select_related('processo')
        prazos_atrasados = prazos_qs.filter(data__lt=hoje).order_by('data')[:20]
        prazos_proximos = prazos_qs.filter(data__gte=hoje, data__lte=limite).order_by('data')[:20]

        financeiro_qs = Lancamento.objects.filter(
            Q(criado_por=request.user)
            | Q(processo_id__in=processo_ids)
            | Q(cliente__responsavel=request.user)
        ).distinct()
        if request.user.is_administrador():
            financeiro_qs = Lancamento.objects.all()

        contas_pagar_pendentes = financeiro_qs.filter(tipo__in=Lancamento.tipos_pagar(), status='pendente').count()
        contas_receber_pendentes = financeiro_qs.filter(tipo__in=Lancamento.tipos_receber(), status='pendente').count()
        contas_atrasadas = financeiro_qs.filter(status='atrasado').count()

        eventos_qs = IAEventoSistema.objects.all()
        if not request.user.is_administrador():
            eventos_qs = eventos_qs.filter(Q(criado_por=request.user) | Q(criado_por__isnull=True))
        eventos_qs = eventos_qs.filter(resolvido=False)

        if not os.getenv('GROQ_API_KEY'):
            if not IAEventoSistema.objects.filter(
                tipo='ia',
                severidade='alerta',
                mensagem='GROQ_API_KEY ausente no ambiente',
                resolvido=False,
            ).exists():
                IAEventoSistema.objects.create(
                    tipo='ia',
                    severidade='alerta',
                    mensagem='GROQ_API_KEY ausente no ambiente',
                    rota='/api/v1/ia/analises/monitoramento/',
                    criado_por=None,
                )

        eventos = IAEventoSistemaSerializer(eventos_qs.order_by('-criado_em')[:30], many=True).data

        return Response({
            'prazos': {
                'atrasados_total': prazos_qs.filter(data__lt=hoje).count(),
                'proximos_7_dias_total': prazos_qs.filter(data__gte=hoje, data__lte=limite).count(),
                'atrasados': [
                    {
                        'id': p.id,
                        'titulo': p.titulo,
                        'data': p.data,
                        'processo_numero': p.processo.numero if p.processo else None,
                    }
                    for p in prazos_atrasados
                ],
                'proximos': [
                    {
                        'id': p.id,
                        'titulo': p.titulo,
                        'data': p.data,
                        'processo_numero': p.processo.numero if p.processo else None,
                    }
                    for p in prazos_proximos
                ],
            },
            'financeiro': {
                'contas_pagar_pendentes': contas_pagar_pendentes,
                'contas_receber_pendentes': contas_receber_pendentes,
                'contas_atrasadas': contas_atrasadas,
            },
            'sistema': {
                'eventos_abertos': len(eventos),
                'eventos': eventos,
            },
        })

    @action(detail=False, methods=['post'], url_path='registrar-erro')
    def registrar_erro(self, request):
        serializer = IAEventoSistemaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evento = serializer.save(criado_por=request.user)
        return Response(IAEventoSistemaSerializer(evento).data, status=status.HTTP_201_CREATED)
