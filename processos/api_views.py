from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db.models import Q, Max
from django.utils import timezone
from accounts.permissions import IsAdvogadoOuAdministradorWrite
from agenda.models import Compromisso
from agenda.serializers import CompromissoSerializer
from .models import (
    Comarca,
    Vara,
    TipoProcesso,
    Cliente,
    ClienteAutomacao,
    ClienteTarefa,
    ClienteContrato,
    Processo,
    ProcessoParte,
    ProcessoResponsavel,
    ProcessoTarefa,
    DocumentoTemplate,
    Movimentacao,
    ClienteArquivo,
    ProcessoArquivo,
    ProcessoPeca,
)
from .serializers import (
    ComarcaSerializer, VaraSerializer, TipoProcessoSerializer,
    ClienteSerializer, ProcessoSerializer, ProcessoListSerializer,
    MovimentacaoSerializer, ClienteArquivoSerializer, ProcessoArquivoSerializer,
    ClienteAutomacaoSerializer, ClienteTarefaSerializer, ClienteContratoSerializer,
    ProcessoParteSerializer, ProcessoResponsavelSerializer, ProcessoTarefaSerializer,
    DocumentoTemplateSerializer, ProcessoPecaSerializer,
)

WORKFLOW_ETAPAS = {
    'contencioso': ['triagem', 'estrategia', 'instrucao', 'negociacao', 'execucao', 'encerramento'],
    'consultivo': ['triagem', 'estrategia', 'negociacao', 'execucao', 'encerramento'],
    'massificado': ['triagem', 'instrucao', 'monitoramento', 'execucao', 'encerramento'],
}


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
    search_fields = ['nome', 'cpf_cnpj', 'email', 'demanda', 'lead_origem', 'lead_campanha']
    ordering_fields = ['nome', 'tipo', 'lead_etapa', 'lead_sla_resposta_em', 'qualificacao_score']

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
            Q(processos__advogado=self.request.user)
            | Q(processos__responsaveis__usuario=self.request.user, processos__responsaveis__ativo=True)
            | Q(responsavel=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        if self.request.user.is_administrador():
            serializer.save()
            return
        serializer.save(responsavel=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.is_administrador():
            processo = serializer.save()
            if processo.advogado_id:
                ProcessoResponsavel.objects.get_or_create(
                    processo=processo,
                    usuario_id=processo.advogado_id,
                    defaults={'papel': 'principal', 'ativo': True},
                )
            return
        responsavel = serializer.validated_data.get('responsavel')
        lead_responsavel = serializer.validated_data.get('lead_responsavel')
        if responsavel and responsavel.pk not in {self.request.user.pk, serializer.instance.responsavel_id}:
            raise PermissionDenied('Você não pode transferir responsável deste cliente.')
        if lead_responsavel and lead_responsavel.pk not in {self.request.user.pk, serializer.instance.lead_responsavel_id}:
            raise PermissionDenied('Você não pode transferir responsável do lead deste cliente.')
        responsavel_final = serializer.instance.responsavel or self.request.user
        lead_responsavel_final = serializer.instance.lead_responsavel or self.request.user
        serializer.save(
            responsavel=responsavel_final,
            lead_responsavel=lead_responsavel_final,
        )

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
            qs = cliente.arquivos.select_related('enviado_por', 'template').all()
            termo = request.query_params.get('q')
            if termo:
                qs = qs.filter(
                    Q(nome_original__icontains=termo)
                    | Q(titulo__icontains=termo)
                    | Q(documento_referencia__icontains=termo)
                    | Q(template_nome__icontains=termo)
                    | Q(template__nome__icontains=termo)
                    | Q(categoria__icontains=termo)
                    | Q(descricao__icontains=termo)
                )
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
        template_obj = None
        template_id = request.data.get('template')
        if template_id:
            try:
                template_obj = DocumentoTemplate.objects.get(pk=template_id, tipo_alvo='cliente', ativo=True)
            except DocumentoTemplate.DoesNotExist:
                return Response({'detail': 'Template de cliente não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        titulo = request.data.get('titulo')
        documento_referencia = request.data.get('documento_referencia')
        template_nome = request.data.get('template_nome')
        categoria = request.data.get('categoria')
        descricao = request.data.get('descricao')

        for arquivo in arquivos:
            referencia = documento_referencia or arquivo.name
            ultimo = (
                cliente.arquivos.filter(documento_referencia=referencia)
                .aggregate(maior=Max('versao'))
                .get('maior')
                or 0
            )
            criados.append(
                ClienteArquivo.objects.create(
                    cliente=cliente,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    titulo=titulo or arquivo.name,
                    documento_referencia=referencia,
                    versao=ultimo + 1,
                    template=template_obj,
                    template_nome=template_nome or (template_obj.nome if template_obj else None),
                    categoria=categoria,
                    descricao=descricao,
                    enviado_por=request.user,
                )
            )
        serializer = ClienteArquivoSerializer(criados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get', 'post'], url_path='documentos-templates')
    def documentos_templates(self, request):
        if request.method == 'GET':
            qs = DocumentoTemplate.objects.filter(tipo_alvo='cliente', ativo=True).order_by('nome')
            serializer = DocumentoTemplateSerializer(qs, many=True)
            return Response(serializer.data)

        if not request.user.is_administrador():
            raise PermissionDenied('Somente administradores podem cadastrar templates.')
        payload = request.data.copy()
        payload['tipo_alvo'] = 'cliente'
        serializer = DocumentoTemplateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(criado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'patch'], url_path='pipeline')
    def pipeline(self, request, pk=None):
        cliente = self.get_object()
        if request.method == 'GET':
            return Response({
                'lead_origem': cliente.lead_origem,
                'lead_campanha': cliente.lead_campanha,
                'lead_etapa': cliente.lead_etapa,
                'lead_sla_resposta_em': cliente.lead_sla_resposta_em,
                'lead_ultimo_contato_em': cliente.lead_ultimo_contato_em,
                'lead_responsavel': cliente.lead_responsavel_id,
            })

        campos = [
            'lead_origem',
            'lead_campanha',
            'lead_etapa',
            'lead_sla_resposta_em',
            'lead_ultimo_contato_em',
            'lead_responsavel',
        ]
        data = {k: request.data.get(k) for k in campos if k in request.data}
        serializer = self.get_serializer(cliente, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'patch'], url_path='qualificacao')
    def qualificacao(self, request, pk=None):
        cliente = self.get_object()
        if request.method == 'GET':
            return Response({
                'formulario_qualificacao': cliente.formulario_qualificacao,
                'qualificacao_status': cliente.qualificacao_status,
                'qualificacao_score': cliente.qualificacao_score,
            })

        campos = ['formulario_qualificacao', 'qualificacao_status', 'qualificacao_score']
        data = {k: request.data.get(k) for k in campos if k in request.data}
        serializer = self.get_serializer(cliente, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'patch'], url_path='conflito-interesses')
    def conflito_interesses(self, request, pk=None):
        cliente = self.get_object()
        if request.method == 'GET':
            return Response({
                'conflito_interesses_status': cliente.conflito_interesses_status,
                'conflito_interesses_observacoes': cliente.conflito_interesses_observacoes,
            })

        campos = ['conflito_interesses_status', 'conflito_interesses_observacoes']
        data = {k: request.data.get(k) for k in campos if k in request.data}
        serializer = self.get_serializer(cliente, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='automacoes')
    def automacoes(self, request, pk=None):
        cliente = self.get_object()
        if request.method == 'GET':
            qs = cliente.automacoes.select_related('criado_por').all()
            serializer = ClienteAutomacaoSerializer(qs, many=True)
            return Response(serializer.data)

        payload = {**request.data, 'cliente': cliente.id}
        serializer = ClienteAutomacaoSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(criado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='tarefas')
    def tarefas(self, request, pk=None):
        cliente = self.get_object()
        if request.method == 'GET':
            qs = cliente.tarefas.select_related('responsavel', 'criado_por').all()
            serializer = ClienteTarefaSerializer(qs, many=True)
            return Response(serializer.data)

        payload = {**request.data, 'cliente': cliente.id}
        serializer = ClienteTarefaSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(criado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'tarefas/(?P<tarefa_id>[^/.]+)/concluir')
    def concluir_tarefa(self, request, pk=None, tarefa_id=None):
        cliente = self.get_object()
        try:
            tarefa = cliente.tarefas.get(pk=tarefa_id)
        except ClienteTarefa.DoesNotExist:
            return Response({'detail': 'Tarefa não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        tarefa.status = 'concluida'
        tarefa.save(update_fields=['status', 'atualizado_em'])
        serializer = ClienteTarefaSerializer(tarefa)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='contratos')
    def contratos(self, request, pk=None):
        cliente = self.get_object()
        if request.method == 'GET':
            qs = cliente.contratos.select_related('criado_por').all()
            serializer = ClienteContratoSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)

        payload = request.data.copy()
        payload['cliente'] = cliente.id
        serializer = ClienteContratoSerializer(data=payload, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(criado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'contratos/(?P<contrato_id>[^/.]+)/enviar-assinatura')
    def enviar_assinatura(self, request, pk=None, contrato_id=None):
        cliente = self.get_object()
        try:
            contrato = cliente.contratos.get(pk=contrato_id)
        except ClienteContrato.DoesNotExist:
            return Response({'detail': 'Contrato não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        contrato.status_assinatura = 'enviado'
        if request.data.get('assinatura_provedor'):
            contrato.assinatura_provedor = request.data.get('assinatura_provedor')
        if request.data.get('assinatura_envelope_id'):
            contrato.assinatura_envelope_id = request.data.get('assinatura_envelope_id')
        if request.data.get('assinatura_link'):
            contrato.assinatura_link = request.data.get('assinatura_link')
        contrato.save(
            update_fields=['status_assinatura', 'assinatura_provedor', 'assinatura_envelope_id', 'assinatura_link']
        )
        serializer = ClienteContratoSerializer(contrato, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path=r'contratos/(?P<contrato_id>[^/.]+)/marcar-assinado')
    def marcar_assinado(self, request, pk=None, contrato_id=None):
        cliente = self.get_object()
        try:
            contrato = cliente.contratos.get(pk=contrato_id)
        except ClienteContrato.DoesNotExist:
            return Response({'detail': 'Contrato não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        contrato.status_assinatura = 'assinado'
        contrato.assinado_em = timezone.now()
        contrato.save(update_fields=['status_assinatura', 'assinado_em'])
        serializer = ClienteContratoSerializer(contrato, context={'request': request})
        return Response(serializer.data)


class ProcessoViewSet(viewsets.ModelViewSet):
    queryset = Processo.objects.select_related(
        'cliente', 'advogado', 'tipo', 'vara', 'vara__comarca'
    ).prefetch_related(
        'movimentacoes',
        'partes',
        'responsaveis__usuario',
        'tarefas__responsavel',
        'pecas',
    ).all()
    permission_classes = [IsAdvogadoOuAdministradorWrite]
    search_fields = ['numero', 'cliente__nome', 'objeto']
    ordering_fields = ['criado_em', 'numero', 'status', 'tipo_caso', 'etapa_workflow']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_administrador():
            queryset_base = queryset
        else:
            queryset_base = queryset.filter(
                Q(advogado=self.request.user)
                | Q(responsaveis__usuario=self.request.user, responsaveis__ativo=True)
            ).distinct()

        status_filtro = self.request.query_params.get('status')
        if status_filtro:
            queryset_base = queryset_base.filter(status=status_filtro)

        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            queryset_base = queryset_base.filter(cliente_id=cliente_id)

        tipo_caso = self.request.query_params.get('tipo_caso')
        if tipo_caso:
            queryset_base = queryset_base.filter(tipo_caso=tipo_caso)

        return queryset_base

    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessoListSerializer
        return ProcessoSerializer

    def _is_admin_or_principal(self, processo):
        return self.request.user.is_administrador() or processo.advogado_id == self.request.user.id

    def _is_responsavel_do_processo(self, processo):
        if self._is_admin_or_principal(processo):
            return True
        return processo.responsaveis.filter(usuario=self.request.user, ativo=True).exists()

    def _workflow_etapas_para(self, tipo_caso):
        return WORKFLOW_ETAPAS.get(tipo_caso, WORKFLOW_ETAPAS['contencioso'])

    def _cliente_disponivel_para_usuario(self, cliente):
        if self.request.user.is_administrador():
            return True
        return (
            cliente.processos.filter(
                Q(advogado=self.request.user)
                | Q(responsaveis__usuario=self.request.user, responsaveis__ativo=True)
            ).exists()
            or cliente.responsavel_id == self.request.user.id
        )

    def perform_create(self, serializer):
        if self.request.user.is_administrador():
            processo = serializer.save()
            if processo.advogado_id:
                ProcessoResponsavel.objects.get_or_create(
                    processo=processo,
                    usuario_id=processo.advogado_id,
                    defaults={'papel': 'principal', 'ativo': True},
                )
            return
        cliente = serializer.validated_data['cliente']
        if not self._cliente_disponivel_para_usuario(cliente):
            raise PermissionDenied('Cliente não disponível para seu perfil.')
        processo = serializer.save(advogado=self.request.user)
        ProcessoResponsavel.objects.get_or_create(
            processo=processo,
            usuario=self.request.user,
            defaults={'papel': 'principal', 'ativo': True},
        )

    def perform_update(self, serializer):
        if self.request.user.is_administrador():
            serializer.save()
            return
        if not self._is_admin_or_principal(serializer.instance):
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
        if not self._is_responsavel_do_processo(processo):
            raise PermissionDenied('Você não pode adicionar movimentação neste processo.')
        data = {**request.data, 'processo': processo.id, 'autor': request.user.id}
        serializer = MovimentacaoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['get', 'patch'], url_path='workflow')
    def workflow(self, request, pk=None):
        processo = self.get_object()
        if request.method == 'GET':
            return Response({
                'tipo_caso': processo.tipo_caso,
                'tipo_caso_display': processo.get_tipo_caso_display(),
                'etapa_workflow': processo.etapa_workflow,
                'etapa_workflow_display': processo.get_etapa_workflow_display(),
                'etapas_disponiveis': self._workflow_etapas_para(processo.tipo_caso),
            })

        if not self._is_admin_or_principal(processo):
            raise PermissionDenied('Somente responsável principal pode alterar workflow.')

        tipo_caso = request.data.get('tipo_caso', processo.tipo_caso)
        if tipo_caso not in WORKFLOW_ETAPAS:
            return Response(
                {'detail': 'Tipo de caso inválido.', 'tipos_disponiveis': list(WORKFLOW_ETAPAS.keys())},
                status=status.HTTP_400_BAD_REQUEST,
            )
        etapa_workflow = request.data.get('etapa_workflow', processo.etapa_workflow)
        etapas_validas = self._workflow_etapas_para(tipo_caso)
        if etapa_workflow not in etapas_validas:
            return Response(
                {
                    'detail': 'Etapa inválida para o tipo de caso informado.',
                    'tipo_caso': tipo_caso,
                    'etapas_disponiveis': etapas_validas,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        processo.tipo_caso = tipo_caso
        processo.etapa_workflow = etapa_workflow
        processo.save(update_fields=['tipo_caso', 'etapa_workflow', 'atualizado_em'])
        serializer = self.get_serializer(processo)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='partes')
    def partes(self, request, pk=None):
        processo = self.get_object()
        if request.method == 'GET':
            qs = processo.partes.all().order_by('nome')
            serializer = ProcessoParteSerializer(qs, many=True)
            return Response(serializer.data)

        if not self._is_responsavel_do_processo(processo):
            raise PermissionDenied('Você não pode cadastrar partes neste processo.')
        payload = {**request.data, 'processo': processo.id}
        serializer = ProcessoParteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'delete'], url_path=r'partes/(?P<parte_id>[^/.]+)')
    def gerenciar_parte(self, request, pk=None, parte_id=None):
        processo = self.get_object()
        if not self._is_responsavel_do_processo(processo):
            raise PermissionDenied('Você não pode alterar partes neste processo.')
        try:
            parte = processo.partes.get(pk=parte_id)
        except ProcessoParte.DoesNotExist:
            return Response({'detail': 'Parte não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            parte.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = ProcessoParteSerializer(parte, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='responsaveis')
    def responsaveis(self, request, pk=None):
        processo = self.get_object()
        if request.method == 'GET':
            qs = processo.responsaveis.select_related('usuario').all()
            serializer = ProcessoResponsavelSerializer(qs, many=True)
            return Response(serializer.data)

        if not self._is_admin_or_principal(processo):
            raise PermissionDenied('Somente responsável principal pode gerenciar equipe do processo.')

        usuario_id = request.data.get('usuario')
        if not usuario_id:
            return Response({'detail': 'Campo "usuario" é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        existente = processo.responsaveis.filter(usuario_id=usuario_id).first()
        payload = {**request.data, 'processo': processo.id}
        if existente:
            serializer = ProcessoResponsavelSerializer(existente, data=payload, partial=True)
        else:
            serializer = ProcessoResponsavelSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        code = status.HTTP_200_OK if existente else status.HTTP_201_CREATED
        return Response(serializer.data, status=code)

    @action(detail=True, methods=['patch', 'delete'], url_path=r'responsaveis/(?P<responsavel_id>[^/.]+)')
    def gerenciar_responsavel(self, request, pk=None, responsavel_id=None):
        processo = self.get_object()
        if not self._is_admin_or_principal(processo):
            raise PermissionDenied('Somente responsável principal pode gerenciar equipe do processo.')
        try:
            responsavel = processo.responsaveis.get(pk=responsavel_id)
        except ProcessoResponsavel.DoesNotExist:
            return Response({'detail': 'Responsável não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            if responsavel.usuario_id == processo.advogado_id:
                return Response(
                    {'detail': 'Não é permitido remover o responsável principal do processo.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            responsavel.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = ProcessoResponsavelSerializer(responsavel, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='tarefas')
    def tarefas(self, request, pk=None):
        processo = self.get_object()
        if request.method == 'GET':
            qs = processo.tarefas.select_related('responsavel', 'criado_por').all()
            serializer = ProcessoTarefaSerializer(qs, many=True)
            return Response(serializer.data)

        if not self._is_responsavel_do_processo(processo):
            raise PermissionDenied('Você não pode criar tarefas neste processo.')
        payload = {**request.data, 'processo': processo.id}
        serializer = ProcessoTarefaSerializer(data=payload)
        serializer.is_valid(raise_exception=True)

        if not self._is_admin_or_principal(processo):
            responsavel = serializer.validated_data.get('responsavel')
            if responsavel and responsavel.id != request.user.id:
                raise PermissionDenied('Você só pode atribuir tarefas para si neste processo.')
            serializer.save(criado_por=request.user, responsavel=request.user)
        else:
            serializer.save(criado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'tarefas/(?P<tarefa_id>[^/.]+)/concluir')
    def concluir_tarefa(self, request, pk=None, tarefa_id=None):
        processo = self.get_object()
        try:
            tarefa = processo.tarefas.get(pk=tarefa_id)
        except ProcessoTarefa.DoesNotExist:
            return Response({'detail': 'Tarefa não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if not (
            self._is_admin_or_principal(processo)
            or tarefa.responsavel_id == request.user.id
        ):
            raise PermissionDenied('Você não pode concluir esta tarefa.')

        tarefa.status = 'concluida'
        tarefa.concluido_em = timezone.now()
        tarefa.save(update_fields=['status', 'concluido_em', 'atualizado_em'])
        serializer = ProcessoTarefaSerializer(tarefa)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='prazos')
    def prazos(self, request, pk=None):
        processo = self.get_object()
        if request.method == 'GET':
            qs = processo.compromissos.filter(tipo='prazo').select_related('advogado').order_by('data', 'hora')
            serializer = CompromissoSerializer(qs, many=True)
            return Response(serializer.data)

        if not self._is_responsavel_do_processo(processo):
            raise PermissionDenied('Você não pode cadastrar prazos neste processo.')

        payload = request.data.copy()
        payload['processo'] = processo.id
        payload['tipo'] = 'prazo'
        if not payload.get('titulo'):
            payload['titulo'] = f'Prazo - {processo.numero}'
        if self.request.user.is_administrador():
            payload['advogado'] = payload.get('advogado') or processo.advogado_id or request.user.id
        else:
            payload['advogado'] = request.user.id

        serializer = CompromissoSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'prazos/(?P<prazo_id>[^/.]+)/concluir')
    def concluir_prazo(self, request, pk=None, prazo_id=None):
        processo = self.get_object()
        try:
            prazo = processo.compromissos.get(pk=prazo_id, tipo='prazo')
        except Compromisso.DoesNotExist:
            return Response({'detail': 'Prazo não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if not (
            self._is_admin_or_principal(processo)
            or prazo.advogado_id == request.user.id
        ):
            raise PermissionDenied('Você não pode concluir este prazo.')

        prazo.status = 'concluido'
        prazo.save(update_fields=['status'])
        serializer = CompromissoSerializer(prazo)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='arquivos')
    def arquivos(self, request, pk=None):
        processo = self.get_object()
        if request.method == 'GET':
            qs = processo.arquivos.select_related('enviado_por', 'template').all()
            termo = request.query_params.get('q')
            if termo:
                qs = qs.filter(
                    Q(nome_original__icontains=termo)
                    | Q(titulo__icontains=termo)
                    | Q(documento_referencia__icontains=termo)
                    | Q(template_nome__icontains=termo)
                    | Q(template__nome__icontains=termo)
                    | Q(categoria__icontains=termo)
                    | Q(descricao__icontains=termo)
                )
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
        template_obj = None
        template_id = request.data.get('template')
        if template_id:
            try:
                template_obj = DocumentoTemplate.objects.get(pk=template_id, tipo_alvo='processo', ativo=True)
            except DocumentoTemplate.DoesNotExist:
                return Response({'detail': 'Template de processo não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        titulo = request.data.get('titulo')
        documento_referencia = request.data.get('documento_referencia')
        template_nome = request.data.get('template_nome')
        categoria = request.data.get('categoria')
        descricao = request.data.get('descricao')

        for arquivo in arquivos:
            referencia = documento_referencia or arquivo.name
            ultimo = (
                processo.arquivos.filter(documento_referencia=referencia)
                .aggregate(maior=Max('versao'))
                .get('maior')
                or 0
            )
            criados.append(
                ProcessoArquivo.objects.create(
                    processo=processo,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    titulo=titulo or arquivo.name,
                    documento_referencia=referencia,
                    versao=ultimo + 1,
                    template=template_obj,
                    template_nome=template_nome or (template_obj.nome if template_obj else None),
                    categoria=categoria,
                    descricao=descricao,
                    enviado_por=request.user,
                )
            )
        serializer = ProcessoArquivoSerializer(criados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get', 'post'], url_path='documentos-templates')
    def documentos_templates(self, request):
        if request.method == 'GET':
            qs = DocumentoTemplate.objects.filter(tipo_alvo='processo', ativo=True).order_by('nome')
            serializer = DocumentoTemplateSerializer(qs, many=True)
            return Response(serializer.data)

        if not request.user.is_administrador():
            raise PermissionDenied('Somente administradores podem cadastrar templates.')
        payload = request.data.copy()
        payload['tipo_alvo'] = 'processo'
        serializer = DocumentoTemplateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save(criado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='pecas')
    def pecas(self, request, pk=None):
        processo = self.get_object()
        if request.method == 'GET':
            qs = processo.pecas.select_related('criado_por', 'atualizado_por').all()
            status_filtro = request.query_params.get('status')
            tipo_filtro = request.query_params.get('tipo')
            termo = request.query_params.get('q')
            if status_filtro:
                qs = qs.filter(status=status_filtro)
            if tipo_filtro:
                qs = qs.filter(tipo_peca=tipo_filtro)
            if termo:
                qs = qs.filter(Q(titulo__icontains=termo) | Q(conteudo__icontains=termo))
            serializer = ProcessoPecaSerializer(qs, many=True)
            return Response(serializer.data)

        if not self._is_responsavel_do_processo(processo):
            raise PermissionDenied('Você não pode criar peças neste processo.')

        payload = request.data.copy()
        payload['processo'] = processo.id
        serializer = ProcessoPecaSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        titulo = serializer.validated_data.get('titulo', '').strip()
        tipo_peca = serializer.validated_data.get('tipo_peca')
        ultima_versao = (
            processo.pecas.filter(titulo=titulo, tipo_peca=tipo_peca)
            .aggregate(maior=Max('versao'))
            .get('maior')
            or 0
        )
        serializer.save(
            criado_por=request.user,
            atualizado_por=request.user,
            versao=ultima_versao + 1,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'delete'], url_path=r'pecas/(?P<peca_id>[^/.]+)')
    def gerenciar_peca(self, request, pk=None, peca_id=None):
        processo = self.get_object()
        if not self._is_responsavel_do_processo(processo):
            raise PermissionDenied('Você não pode alterar peças neste processo.')
        try:
            peca = processo.pecas.get(pk=peca_id)
        except ProcessoPeca.DoesNotExist:
            return Response({'detail': 'Peça não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            peca.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = ProcessoPecaSerializer(peca, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(atualizado_por=request.user)
        return Response(serializer.data)


class MovimentacaoViewSet(viewsets.ModelViewSet):
    queryset = Movimentacao.objects.select_related('processo', 'autor').all()
    serializer_class = MovimentacaoSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_administrador():
            return queryset
        return queryset.filter(
            Q(processo__advogado=self.request.user)
            | Q(processo__responsaveis__usuario=self.request.user, processo__responsaveis__ativo=True)
        ).distinct()

    def perform_create(self, serializer):
        processo = serializer.validated_data['processo']
        if not self.request.user.is_administrador() and not (
            processo.advogado_id == self.request.user.id
            or processo.responsaveis.filter(usuario=self.request.user, ativo=True).exists()
        ):
            raise PermissionDenied('Você não pode registrar movimentações neste processo.')
        serializer.save(autor=self.request.user)

    def perform_update(self, serializer):
        processo = serializer.validated_data.get('processo', serializer.instance.processo)
        if not self.request.user.is_administrador() and not (
            processo.advogado_id == self.request.user.id
            or processo.responsaveis.filter(usuario=self.request.user, ativo=True).exists()
        ):
            raise PermissionDenied('Você não pode editar movimentações deste processo.')
        serializer.save(autor=self.request.user)
