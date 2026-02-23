from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cliente, Vara, TipoProcesso, Processo, Movimentacao
from .serializers import (ClienteSerializer, VaraSerializer, TipoProcessoSerializer,
                          ProcessoSerializer, ProcessoDetalheSerializer, MovimentacaoSerializer)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_pessoa', 'estado']
    search_fields = ['nome', 'cpf_cnpj', 'email', 'telefone']
    ordering_fields = ['nome', 'criado_em']


class VaraViewSet(viewsets.ModelViewSet):
    queryset = Vara.objects.all()
    serializer_class = VaraSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'comarca', 'estado', 'tribunal']


class TipoProcessoViewSet(viewsets.ModelViewSet):
    queryset = TipoProcesso.objects.all()
    serializer_class = TipoProcessoSerializer


class ProcessoViewSet(viewsets.ModelViewSet):
    queryset = Processo.objects.select_related(
        'cliente', 'advogado_responsavel', 'vara', 'tipo_processo'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'tipo_processo', 'advogado_responsavel', 'polo']
    search_fields = ['numero', 'cliente__nome', 'parte_contraria']
    ordering_fields = ['criado_em', 'numero', 'data_distribuicao']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProcessoDetalheSerializer
        return ProcessoSerializer

    @action(detail=True, methods=['get'])
    def movimentacoes(self, request, pk=None):
        processo = self.get_object()
        movs = processo.movimentacoes.all()
        serializer = MovimentacaoSerializer(movs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='meus-processos')
    def meus_processos(self, request):
        qs = self.queryset.filter(advogado_responsavel=request.user)
        serializer = ProcessoSerializer(qs, many=True)
        return Response(serializer.data)


class MovimentacaoViewSet(viewsets.ModelViewSet):
    queryset = Movimentacao.objects.select_related('processo', 'autor').all()
    serializer_class = MovimentacaoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['processo']
    ordering_fields = ['data', 'criado_em']

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)
