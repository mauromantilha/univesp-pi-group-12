from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, timedelta
from .models import Compromisso
from .serializers import CompromissoSerializer


class CompromissoViewSet(viewsets.ModelViewSet):
    queryset = Compromisso.objects.select_related('advogado', 'processo').all()
    serializer_class = CompromissoSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['data', 'hora', 'status']
    
    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """Retorna compromissos dos próximos 7 dias"""
        hoje = datetime.now().date()
        proximos_7_dias = hoje + timedelta(days=7)
        
        compromissos = self.queryset.filter(
            data__gte=hoje,
            data__lte=proximos_7_dias,
            status='pendente'
        )
        
        serializer = self.get_serializer(compromissos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mes(self, request):
        """Retorna compromissos do mês atual"""
        ano = request.query_params.get('ano')
        mes = request.query_params.get('mes')
        
        if not ano or not mes:
            hoje = datetime.now().date()
            ano = hoje.year
            mes = hoje.month
        
        compromissos = self.queryset.filter(
            data__year=ano,
            data__month=mes
        )
        
        serializer = self.get_serializer(compromissos, many=True)
        return Response(serializer.data)
