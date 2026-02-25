import os
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.throttling import UserRateThrottle
from django.db.models import Q
from accounts.permissions import IsAdvogadoOuAdministradorWrite
from .models import AnaliseRisco
from .serializers import AnaliseRiscoSerializer
from consulta_tribunais.services.groq_service import GroqService
from jurisprudencia.models import Documento

logger = logging.getLogger(__name__)


class IAChatRateThrottle(UserRateThrottle):
    scope = 'ia_chat'


def _resposta_fallback_ia():
    return (
        'IA indisponível no momento. Verifique a configuração da chave GROQ_API_KEY '
        'ou tente novamente em instantes.'
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([IAChatRateThrottle])
def ia_chat(request):
    """
    Endpoint de chat jurídico com IA.
    Recebe { "mensagem": "..." } e retorna { "resposta": "..." }
    """
    mensagem = request.data.get('mensagem', '').strip()
    if not mensagem:
        return Response({'error': 'Campo "mensagem" obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        return Response(
            {'resposta': _resposta_fallback_ia(), 'fallback': True},
            status=status.HTTP_200_OK
        )

    try:
        groq = GroqService(groq_api_key)
        completion = groq.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente jurídico brasileiro especializado. "
                        "Responda perguntas sobre direito de forma clara, objetiva e profissional, "
                        "com base na legislação brasileira vigente. "
                        "Sempre indique artigos de lei relevantes quando aplicável."
                    )
                },
                {"role": "user", "content": mensagem}
            ],
            model=groq.model,
            temperature=0.3,
            max_tokens=1500,
        )
        resposta = completion.choices[0].message.content
        return Response({'resposta': resposta})
    except Exception:
        logger.exception('Falha na integração com IA no endpoint ia_chat')
        return Response(
            {'resposta': _resposta_fallback_ia(), 'fallback': True},
            status=status.HTTP_200_OK
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ia_sugerir(request):
    termo = (
        request.data.get('q')
        or request.data.get('texto')
        or request.data.get('mensagem')
        or request.query_params.get('q')
        or request.query_params.get('texto')
        or ''
    ).strip()
    if not termo:
        return Response({'sugestoes': []}, status=status.HTTP_200_OK)

    qs = Documento.objects.filter(
        Q(titulo__icontains=termo) |
        Q(conteudo__icontains=termo) |
        Q(tags__icontains=termo)
    )
    if not request.user.is_administrador():
        qs = qs.filter(
            Q(processo_referencia__advogado=request.user) |
            Q(adicionado_por=request.user) |
            Q(processo_referencia__isnull=True)
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

    return Response({'sugestoes': sugestoes}, status=status.HTTP_200_OK)


class AnaliseRiscoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnaliseRisco.objects.select_related('processo').all()
    serializer_class = AnaliseRiscoSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_administrador():
            return queryset
        return queryset.filter(processo__advogado=self.request.user)
    
    @action(detail=False, methods=['post'])
    def analisar_processo(self, request):
        """Gera análise de risco para um processo"""
        processo_id = request.data.get('processo_id')
        
        if not processo_id:
            return Response(
                {'error': 'processo_id é obrigatório'},
                status=400
            )
        
        try:
            processo_id = int(processo_id)
        except (TypeError, ValueError):
            return Response(
                {'error': 'processo_id inválido'},
                status=400
            )

        from processos.models import Processo
        processos_qs = Processo.objects.all()
        if not request.user.is_administrador():
            processos_qs = processos_qs.filter(advogado=request.user)
        if not processos_qs.filter(id=processo_id).exists():
            raise PermissionDenied('Você não tem permissão para analisar este processo.')

        # Aqui iria a lógica de análise preditiva
        # Por enquanto, retorna dados simulados
        analise, created = AnaliseRisco.objects.get_or_create(
            processo_id=processo_id,
            defaults={
                'probabilidade_exito': 75.0,
                'justificativa': 'Análise baseada em processos similares',
                'processos_similares': 10,
                'vitorias_similares': 7
            }
        )
        
        serializer = self.get_serializer(analise)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='analisar')
    def analisar(self, request):
        return self.analisar_processo(request)
