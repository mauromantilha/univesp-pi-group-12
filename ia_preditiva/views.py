from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AnaliseRisco, SugestaoJurisprudencia
from .serializers import AnaliseRiscoSerializer, SugestaoJurisprudenciaSerializer
from processos.models import Processo


class AnaliseRiscoViewSet(viewsets.ModelViewSet):
    queryset = AnaliseRisco.objects.select_related('processo').all()
    serializer_class = AnaliseRiscoSerializer

    @action(detail=False, methods=['post'], url_path='analisar')
    def analisar(self, request):
        processo_id = request.data.get('processo_id')
        if not processo_id:
            return Response({'erro': 'processo_id obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            processo = Processo.objects.get(pk=processo_id)
        except Processo.DoesNotExist:
            return Response({'erro': 'Processo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Análise simples baseada em histórico (regra de negócio básica)
        from jurisprudencia.models import Documento
        from django.db.models import Count
        similares = Documento.objects.filter(tipo_processo=processo.tipo_processo)
        total = similares.count()
        procedentes = similares.filter(resultado__icontains='procedente').count()
        prob = (procedentes / total) if total > 0 else 0.5

        analise, _ = AnaliseRisco.objects.update_or_create(
            processo=processo,
            defaults={
                'probabilidade_exito': prob,
                'nivel_risco': 'baixo' if prob >= 0.6 else 'medio' if prob >= 0.4 else 'alto',
                'baseado_em_processos': total,
                'justificativa': f'Baseado em {total} decisões similares no repositório. {procedentes} procedentes.'
            }
        )
        serializer = AnaliseRiscoSerializer(analise)
        return Response(serializer.data)


class SugestaoJurisprudenciaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SugestaoJurisprudencia.objects.all()
    serializer_class = SugestaoJurisprudenciaSerializer

    @action(detail=False, methods=['post'], url_path='sugerir')
    def sugerir(self, request):
        processo_id = request.data.get('processo_id')
        if not processo_id:
            return Response({'erro': 'processo_id obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            processo = Processo.objects.get(pk=processo_id)
        except Processo.DoesNotExist:
            return Response({'erro': 'Processo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        from jurisprudencia.models import Documento
        docs = Documento.objects.filter(tipo_processo=processo.tipo_processo)[:5]
        sugestoes = []
        for doc in docs:
            obj, _ = SugestaoJurisprudencia.objects.update_or_create(
                processo=processo,
                documento_sugerido_id=doc.pk,
                defaults={
                    'titulo_documento': doc.titulo,
                    'score_relevancia': 0.8,
                    'motivo': f'Mesmo tipo de processo: {processo.tipo_processo.nome}'
                }
            )
            sugestoes.append(obj)
        serializer = SugestaoJurisprudenciaSerializer(sugestoes, many=True)
        return Response(serializer.data)
