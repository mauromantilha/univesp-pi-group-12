from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AnaliseRisco
from .serializers import AnaliseRiscoSerializer


class AnaliseRiscoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnaliseRisco.objects.select_related('processo').all()
    serializer_class = AnaliseRiscoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def analisar_processo(self, request):
        """Gera análise de risco para um processo"""
        processo_id = request.data.get('processo_id')
        
        if not processo_id:
            return Response(
                {'error': 'processo_id é obrigatório'},
                status=400
            )
        
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
