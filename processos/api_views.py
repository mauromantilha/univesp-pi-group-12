from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Comarca, Vara, TipoProcesso, Cliente, Processo, Movimentacao
from .serializers import (
    ComarcaSerializer, VaraSerializer, TipoProcessoSerializer,
    ClienteSerializer, ProcessoSerializer, ProcessoListSerializer,
    MovimentacaoSerializer
)


class ComarcaViewSet(viewsets.ModelViewSet):
    queryset = Comarca.objects.all()
    serializer_class = ComarcaSerializer
    permission_classes = [permissions.IsAuthenticated]


class VaraViewSet(viewsets.ModelViewSet):
    queryset = Vara.objects.select_related('comarca').all()
    serializer_class = VaraSerializer
    permission_classes = [permissions.IsAuthenticated]


class TipoProcessoViewSet(viewsets.ModelViewSet):
    queryset = TipoProcesso.objects.all()
    serializer_class = TipoProcessoSerializer
    permission_classes = [permissions.IsAuthenticated]


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nome', 'cpf_cnpj', 'email']
    ordering_fields = ['nome', 'tipo']


class ProcessoViewSet(viewsets.ModelViewSet):
    queryset = Processo.objects.select_related(
        'cliente', 'advogado', 'tipo', 'vara', 'vara__comarca'
    ).prefetch_related('movimentacoes').all()
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['numero', 'cliente__nome', 'objeto']
    ordering_fields = ['data_distribuicao', 'data_ultima_movimentacao', 'numero']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessoListSerializer
        return ProcessoSerializer
    
    @action(detail=True, methods=['post'])
    def adicionar_movimentacao(self, request, pk=None):
        """Adiciona uma movimentação ao processo"""
        processo = self.get_object()
        serializer = MovimentacaoSerializer(data={
            **request.data,
            'processo': processo.id,
            'usuario': request.user.id
        })
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class MovimentacaoViewSet(viewsets.ModelViewSet):
    queryset = Movimentacao.objects.select_related('processo', 'usuario').all()
    serializer_class = MovimentacaoSerializer
    permission_classes = [permissions.IsAuthenticated]
