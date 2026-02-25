from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from accounts.permissions import IsAdvogadoOuAdministradorWrite
from .models import Comarca, Vara, TipoProcesso, Cliente, Processo, Movimentacao
from .serializers import (
    ComarcaSerializer, VaraSerializer, TipoProcessoSerializer,
    ClienteSerializer, ProcessoSerializer, ProcessoListSerializer,
    MovimentacaoSerializer
)


class IsAdminForWrite(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_administrador())


class ComarcaViewSet(viewsets.ModelViewSet):
    queryset = Comarca.objects.all()
    serializer_class = ComarcaSerializer
    permission_classes = [IsAdminForWrite]


class VaraViewSet(viewsets.ModelViewSet):
    queryset = Vara.objects.select_related('comarca').all()
    serializer_class = VaraSerializer
    permission_classes = [IsAdminForWrite]


class TipoProcessoViewSet(viewsets.ModelViewSet):
    queryset = TipoProcesso.objects.all()
    serializer_class = TipoProcessoSerializer
    permission_classes = [IsAdminForWrite]


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]
    search_fields = ['nome', 'cpf_cnpj', 'email']
    ordering_fields = ['nome', 'tipo']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_administrador():
            return queryset
        return queryset.filter(processos__advogado=self.request.user).distinct()


class ProcessoViewSet(viewsets.ModelViewSet):
    queryset = Processo.objects.select_related(
        'cliente', 'advogado', 'tipo', 'vara', 'vara__comarca'
    ).prefetch_related('movimentacoes').all()
    permission_classes = [IsAdvogadoOuAdministradorWrite]
    search_fields = ['numero', 'cliente__nome', 'objeto']
    ordering_fields = ['criado_em', 'numero']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_administrador():
            return queryset
        return queryset.filter(advogado=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessoListSerializer
        return ProcessoSerializer

    def _cliente_disponivel_para_usuario(self, cliente):
        if self.request.user.is_administrador():
            return True
        return cliente.processos.filter(advogado=self.request.user).exists() or not cliente.processos.exists()

    def perform_create(self, serializer):
        if self.request.user.is_administrador():
            serializer.save()
            return
        cliente = serializer.validated_data['cliente']
        if not self._cliente_disponivel_para_usuario(cliente):
            raise PermissionDenied('Cliente não disponível para seu perfil.')
        serializer.save(advogado=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.is_administrador():
            serializer.save()
            return
        if serializer.instance.advogado_id != self.request.user.id:
            raise PermissionDenied('Você não tem permissão para editar este processo.')
        cliente = serializer.validated_data.get('cliente', serializer.instance.cliente)
        if not self._cliente_disponivel_para_usuario(cliente):
            raise PermissionDenied('Cliente não disponível para seu perfil.')
        serializer.save(advogado=self.request.user)

    @action(detail=True, methods=['get'])
    def movimentacoes(self, request, pk=None):
        """Retorna as movimentações de um processo"""
        processo = self.get_object()
        movs = processo.movimentacoes.select_related('autor').order_by('-data', '-criado_em')
        serializer = MovimentacaoSerializer(movs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def adicionar_movimentacao(self, request, pk=None):
        """Adiciona uma movimentação ao processo"""
        processo = self.get_object()
        data = {**request.data, 'processo': processo.id, 'autor': request.user.id}
        serializer = MovimentacaoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class MovimentacaoViewSet(viewsets.ModelViewSet):
    queryset = Movimentacao.objects.select_related('processo', 'autor').all()
    serializer_class = MovimentacaoSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_administrador():
            return queryset
        return queryset.filter(processo__advogado=self.request.user)

    def perform_create(self, serializer):
        processo = serializer.validated_data['processo']
        if not self.request.user.is_administrador() and processo.advogado_id != self.request.user.id:
            raise PermissionDenied('Você não pode registrar movimentações neste processo.')
        serializer.save(autor=self.request.user)

    def perform_update(self, serializer):
        processo = serializer.validated_data.get('processo', serializer.instance.processo)
        if not self.request.user.is_administrador() and processo.advogado_id != self.request.user.id:
            raise PermissionDenied('Você não pode editar movimentações deste processo.')
        serializer.save(autor=self.request.user)
