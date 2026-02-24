from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.core.cache import cache
import os

from .models import Tribunal, ConsultaProcesso, PerguntaProcesso
from .serializers import (
    TribunalSerializer, ConsultaProcessoSerializer,
    ConsultaProcessoCreateSerializer, PerguntaProcessoSerializer
)
from .services.datajud_service import DataJudService, formatar_dados_processo
from .services.groq_service import GroqService


class TribunalViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para tribunais disponíveis"""
    queryset = Tribunal.objects.filter(ativo=True)
    serializer_class = TribunalSerializer
    permission_classes = [permissions.IsAuthenticated]


class ConsultaProcessoViewSet(viewsets.ModelViewSet):
    """ViewSet para consultas de processos"""
    queryset = ConsultaProcesso.objects.select_related('tribunal', 'usuario').prefetch_related('perguntas').all()
    serializer_class = ConsultaProcessoSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['data_consulta', 'numero_processo']
    
    def get_queryset(self):
        """Filtra consultas do usuário ou todas se admin"""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(usuario=self.request.user)
        return queryset
    
    @action(detail=False, methods=['post'])
    def buscar_avancado(self, request):
        """
        Busca avançada de processos.
        
        IMPORTANTE: A API Pública DataJud NÃO possui dados de partes/advogados.
        
        Campos disponíveis para busca:
        - classe: Nome da classe processual (ex: "Reclamação Trabalhista")
        - orgao_julgador: Nome do órgão (ex: "1ª Vara")
        - assunto: Assunto (ex: "Horas Extras")
        - data_inicio: Data inicial YYYYMMDD (ex: "20240101")
        - data_fim: Data final YYYYMMDD (ex: "20241231")
        """
        tribunal_id = request.data.get('tribunal_id')
        filtros = {
            'classe': request.data.get('classe', '').strip(),
            'orgao_julgador': request.data.get('orgao_julgador', '').strip(),
            'assunto': request.data.get('assunto', '').strip(),
            'data_inicio': request.data.get('data_inicio', '').strip(),
            'data_fim': request.data.get('data_fim', '').strip(),
        }
        
        # Remove filtros vazios
        filtros = {k: v for k, v in filtros.items() if v}
        
        max_results = int(request.data.get('max_results', 20))
        
        try:
            tribunal = Tribunal.objects.get(id=tribunal_id, ativo=True)
        except Tribunal.DoesNotExist:
            return Response(
                {'error': 'Tribunal não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            datajud = DataJudService(tribunal)
            processos = datajud.buscar_processos_avancado(filtros, max_results)
            
            return Response({
                'total': len(processos),
                'processos': processos,
                'filtros_aplicados': filtros,
                'aviso': 'A API pública DataJud não possui dados de partes/advogados.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def consultar(self, request):
        """Realiza uma nova consulta no tribunal"""
        serializer = ConsultaProcessoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tribunal_id = serializer.validated_data['tribunal_id']
        numero_processo = serializer.validated_data['numero_processo']
        processo_vinculado_id = serializer.validated_data.get('processo_vinculado_id')
        analisar_com_ia = serializer.validated_data.get('analisar_com_ia', True)
        
        try:
            tribunal = Tribunal.objects.get(id=tribunal_id, ativo=True)
        except Tribunal.DoesNotExist:
            return Response(
                {'error': 'Tribunal não encontrado ou inativo'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cria registro da consulta
        consulta = ConsultaProcesso.objects.create(
            tribunal=tribunal,
            numero_processo=numero_processo,
            usuario=request.user,
            processo_vinculado_id=processo_vinculado_id,
            status='processando'
        )
        
        try:
            # Consulta no DataJud
            datajud = DataJudService(tribunal)
            dados = datajud.consultar_processo(numero_processo)
            
            if not dados:
                consulta.status = 'erro'
                consulta.erro_mensagem = 'Processo não encontrado no tribunal'
                consulta.save()
                return Response(
                    {'error': 'Processo não encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            consulta.dados_processo = dados
            consulta.status = 'sucesso'
            
            # Análise com IA se solicitado
            if analisar_com_ia:
                try:
                    groq_api_key = os.getenv('GROQ_API_KEY')
                    if groq_api_key:
                        groq = GroqService(groq_api_key)
                        dados_formatados = formatar_dados_processo(dados)
                        analise = groq.analisar_processo(dados_formatados)
                        consulta.analise_ia = analise
                        consulta.analise_atualizada_em = timezone.now()
                except Exception as e:
                    # Falha na IA não impede a consulta
                    consulta.erro_mensagem = f"Aviso: Erro na análise IA: {str(e)}"
            
            consulta.save()
            
            serializer = ConsultaProcessoSerializer(consulta)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            consulta.status = 'erro'
            consulta.erro_mensagem = str(e)
            consulta.save()
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def fazer_pergunta(self, request, pk=None):
        """Faz uma pergunta sobre o processo consultado"""
        consulta = self.get_object()
        pergunta_texto = request.data.get('pergunta', '').strip()
        
        if not pergunta_texto:
            return Response(
                {'error': 'Pergunta não pode ser vazia'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not consulta.dados_processo:
            return Response(
                {'error': 'Consulta sem dados para análise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                return Response(
                    {'error': 'IA não configurada (GROQ_API_KEY ausente)'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            groq = GroqService(groq_api_key)
            dados_formatados = formatar_dados_processo(consulta.dados_processo)
            
            # Pega histórico de perguntas
            historico = list(consulta.perguntas.values('pergunta', 'resposta').order_by('-data_pergunta')[:3])
            
            resposta = groq.responder_pergunta(dados_formatados, pergunta_texto, historico)
            
            # Salva a pergunta e resposta
            pergunta_obj = PerguntaProcesso.objects.create(
                consulta=consulta,
                usuario=request.user,
                pergunta=pergunta_texto,
                resposta=resposta
            )
            
            serializer = PerguntaProcessoSerializer(pergunta_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao processar pergunta: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reanalisar(self, request, pk=None):
        """Gera nova análise IA do processo"""
        consulta = self.get_object()
        
        if not consulta.dados_processo:
            return Response(
                {'error': 'Consulta sem dados para análise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                return Response(
                    {'error': 'IA não configurada'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            groq = GroqService(groq_api_key)
            dados_formatados = formatar_dados_processo(consulta.dados_processo)
            analise = groq.analisar_processo(dados_formatados)
            
            consulta.analise_ia = analise
            consulta.analise_atualizada_em = timezone.now()
            consulta.save()
            
            serializer = ConsultaProcessoSerializer(consulta)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao reanalisar: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
