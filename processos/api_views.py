from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db.models import Q
from accounts.permissions import IsAdvogadoOuAdministradorWrite
from .models import (
    Comarca,
    Vara,
    TipoProcesso,
    Cliente,
    Processo,
    Movimentacao,
    ClienteArquivo,
    ProcessoArquivo,
)
from .serializers import (
    ComarcaSerializer, VaraSerializer, TipoProcessoSerializer,
    ClienteSerializer, ProcessoSerializer, ProcessoListSerializer,
    MovimentacaoSerializer, ClienteArquivoSerializer, ProcessoArquivoSerializer
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
    search_fields = ['nome', 'cpf_cnpj', 'email', 'demanda']
    ordering_fields = ['nome', 'tipo']

    def get_queryset(self):
        queryset = super().get_queryset()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            ativo_normalizado = str(ativo).strip().lower()
            if ativo_normalizado in {'1', 'true', 't', 'sim', 'yes'}:
                queryset = queryset.filter(ativo=True)
            elif ativo_normalizado in {'0', 'false', 'f', 'nao', 'não', 'no'}:
                queryset = queryset.filter(ativo=False)

        if self.request.user.is_administrador():
            return queryset
        return queryset.filter(
            Q(processos__advogado=self.request.user) | Q(responsavel=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        if self.request.user.is_administrador():
            serializer.save()
            return
        serializer.save(responsavel=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.is_administrador():
            serializer.save()
            return
        responsavel = serializer.validated_data.get('responsavel')
        if responsavel and responsavel.pk not in {self.request.user.pk, serializer.instance.responsavel_id}:
            raise PermissionDenied('Você não pode transferir responsável deste cliente.')
        responsavel_final = serializer.instance.responsavel or self.request.user
        serializer.save(responsavel=responsavel_final)

    @action(detail=True, methods=['post'])
    def inativar(self, request, pk=None):
        cliente = self.get_object()
        if not cliente.ativo:
            return Response({'detail': 'Cliente já está inativo.'})
        cliente.ativo = False
        cliente.save(update_fields=['ativo'])
        serializer = self.get_serializer(cliente)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='arquivos')
    def arquivos(self, request, pk=None):
        cliente = self.get_object()
        if request.method == 'GET':
            qs = cliente.arquivos.select_related('enviado_por').all()
            serializer = ClienteArquivoSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)

        arquivos = request.FILES.getlist('arquivos')
        if not arquivos and request.FILES.get('arquivo'):
            arquivos = [request.FILES.get('arquivo')]
        if not arquivos:
            return Response(
                {'error': 'Nenhum arquivo enviado. Use o campo "arquivos".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        criados = []
        for arquivo in arquivos:
            criados.append(
                ClienteArquivo.objects.create(
                    cliente=cliente,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    enviado_por=request.user,
                )
            )
        serializer = ClienteArquivoSerializer(criados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
            queryset_base = queryset
        else:
            queryset_base = queryset.filter(advogado=self.request.user)

        status_filtro = self.request.query_params.get('status')
        if status_filtro:
            queryset_base = queryset_base.filter(status=status_filtro)

        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            queryset_base = queryset_base.filter(cliente_id=cliente_id)

        return queryset_base

    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessoListSerializer
        return ProcessoSerializer

    def _cliente_disponivel_para_usuario(self, cliente):
        if self.request.user.is_administrador():
            return True
        return (
            cliente.processos.filter(advogado=self.request.user).exists()
            or cliente.responsavel_id == self.request.user.id
        )

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

    def _alterar_status(self, processo, novo_status):
        processo.status = novo_status
        processo.save(update_fields=['status', 'atualizado_em'])

    @action(detail=True, methods=['post'])
    def inativar(self, request, pk=None):
        processo = self.get_object()
        self._alterar_status(processo, 'suspenso')
        serializer = self.get_serializer(processo)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def concluir(self, request, pk=None):
        processo = self.get_object()
        self._alterar_status(processo, 'finalizado')
        serializer = self.get_serializer(processo)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def arquivar(self, request, pk=None):
        processo = self.get_object()
        self._alterar_status(processo, 'arquivado')
        serializer = self.get_serializer(processo)
        return Response(serializer.data)

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

    @action(detail=True, methods=['get', 'post'], url_path='arquivos')
    def arquivos(self, request, pk=None):
        processo = self.get_object()
        if request.method == 'GET':
            qs = processo.arquivos.select_related('enviado_por').all()
            serializer = ProcessoArquivoSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)

        arquivos = request.FILES.getlist('arquivos')
        if not arquivos and request.FILES.get('arquivo'):
            arquivos = [request.FILES.get('arquivo')]
        if not arquivos:
            return Response(
                {'error': 'Nenhum arquivo enviado. Use o campo "arquivos".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        criados = []
        for arquivo in arquivos:
            criados.append(
                ProcessoArquivo.objects.create(
                    processo=processo,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    enviado_por=request.user,
                )
            )
        serializer = ProcessoArquivoSerializer(criados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
