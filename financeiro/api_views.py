from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q, Sum, Count, Max
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.permissions import IsAdvogadoOuAdministradorWrite
from accounts.rbac import processos_visiveis_queryset, usuario_pode_entrar_processo
from processos.models import Processo
from core.security import validate_upload_file
from .models import (
    Lancamento,
    CategoriaFinanceira,
    ContaBancaria,
    LancamentoArquivo,
    RegraCobranca,
    ApontamentoTempo,
    Fatura,
    FaturaItem,
)
from .serializers import (
    LancamentoSerializer,
    CategoriaFinanceiraSerializer,
    ContaBancariaSerializer,
    LancamentoArquivoSerializer,
    RegraCobrancaSerializer,
    ApontamentoTempoSerializer,
    FaturaSerializer,
    FaturaItemSerializer,
)


def _processo_disponivel_para_usuario(usuario, processo):
    if not processo:
        return True
    return usuario_pode_entrar_processo(processo, usuario)


def _lancamentos_por_usuario(usuario):
    qs = Lancamento.objects.select_related(
        'cliente', 'processo', 'criado_por', 'categoria', 'conta_bancaria'
    ).all()
    if usuario.is_administrador():
        return qs
    processos_ids = processos_visiveis_queryset(Processo.objects.all(), usuario).values_list('id', flat=True)
    return qs.filter(
        Q(criado_por=usuario)
        | Q(processo_id__in=processos_ids)
    ).distinct()


def _add_months(inicio_mes, delta_meses):
    total = (inicio_mes.year * 12 + (inicio_mes.month - 1)) + delta_meses
    ano = total // 12
    mes = total % 12 + 1
    return date(ano, mes, 1)


def _to_decimal(value, default=Decimal('0')):
    if value in (None, ''):
        return default
    try:
        return Decimal(str(value))
    except Exception:
        return default


class CategoriaFinanceiraViewSet(viewsets.ModelViewSet):
    queryset = CategoriaFinanceira.objects.all()
    serializer_class = CategoriaFinanceiraSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]

    @staticmethod
    def _garantir_categorias_padrao():
        padrao = [
            ('Honorários', 'receber'),
            ('Acordos', 'receber'),
            ('Reembolsos', 'receber'),
            ('Custas Judiciais', 'pagar'),
            ('Taxas', 'pagar'),
            ('Despesas Operacionais', 'pagar'),
        ]
        for nome, tipo in padrao:
            CategoriaFinanceira.objects.get_or_create(
                nome=nome,
                tipo=tipo,
                criado_por=None,
                defaults={'ativo': True},
            )

    def get_queryset(self):
        self._garantir_categorias_padrao()
        qs = super().get_queryset().filter(ativo=True)
        if self.request.user.is_administrador():
            return qs
        return qs.filter(Q(criado_por__isnull=True) | Q(criado_por=self.request.user))

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    def perform_update(self, serializer):
        instancia = self.get_object()
        if (
            not self.request.user.is_administrador()
            and instancia.criado_por_id not in (None, self.request.user.id)
        ):
            raise PermissionDenied('Você não pode editar esta categoria.')
        serializer.save()

    def perform_destroy(self, instance):
        if (
            not self.request.user.is_administrador()
            and instance.criado_por_id not in (None, self.request.user.id)
        ):
            raise PermissionDenied('Você não pode remover esta categoria.')
        instance.ativo = False
        instance.save(update_fields=['ativo'])


class ContaBancariaViewSet(viewsets.ModelViewSet):
    queryset = ContaBancaria.objects.select_related('criado_por').all()
    serializer_class = ContaBancariaSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_administrador():
            return qs
        return qs.filter(criado_por=self.request.user)

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    def perform_update(self, serializer):
        conta = self.get_object()
        if not self.request.user.is_administrador() and conta.criado_por_id != self.request.user.id:
            raise PermissionDenied('Você não pode editar esta conta.')
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_administrador() and instance.criado_por_id != self.request.user.id:
            raise PermissionDenied('Você não pode remover esta conta.')
        instance.delete()

    @action(detail=True, methods=['get'])
    def extrato(self, request, pk=None):
        conta = self.get_object()
        extrato_qs = _lancamentos_por_usuario(request.user).filter(
            conta_bancaria=conta,
            status='pago',
        ).order_by('-data_pagamento', '-id')
        return Response({
            'conta_id': conta.id,
            'saldo': float(conta.saldo or 0),
            'extrato': LancamentoSerializer(extrato_qs[:100], many=True).data,
        })


class LancamentoViewSet(viewsets.ModelViewSet):
    queryset = Lancamento.objects.select_related(
        'cliente', 'processo', 'criado_por', 'categoria', 'conta_bancaria'
    ).all()
    serializer_class = LancamentoSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]

    def get_queryset(self):
        qs = _lancamentos_por_usuario(self.request.user)
        q = self.request.query_params.get('q', '')
        status_filtro = self.request.query_params.get('status', '')
        tipo_filtro = self.request.query_params.get('tipo', '')
        faturado = self.request.query_params.get('faturado')
        if q:
            qs = qs.filter(Q(descricao__icontains=q) | Q(cliente__nome__icontains=q))
        if status_filtro:
            qs = qs.filter(status=status_filtro)
        if tipo_filtro:
            tipo_normalizado = Lancamento.normalizar_tipo(tipo_filtro)
            if tipo_normalizado == 'receber':
                qs = qs.filter(tipo__in=Lancamento.tipos_receber())
            elif tipo_normalizado == 'pagar':
                qs = qs.filter(tipo__in=Lancamento.tipos_pagar())
            else:
                qs = qs.filter(tipo=tipo_normalizado)
        if faturado is not None:
            valor = str(faturado).strip().lower()
            if valor in {'1', 'true', 'sim', 'yes'}:
                qs = qs.filter(faturado_em__isnull=False)
            elif valor in {'0', 'false', 'nao', 'não', 'no'}:
                qs = qs.filter(faturado_em__isnull=True)
        return qs

    def perform_create(self, serializer):
        processo = serializer.validated_data.get('processo')
        conta = serializer.validated_data.get('conta_bancaria')
        categoria = serializer.validated_data.get('categoria')

        if processo and not _processo_disponivel_para_usuario(self.request.user, processo):
            raise PermissionDenied('Você não pode vincular lançamento a processo de outro advogado.')
        if conta and not self.request.user.is_administrador() and conta.criado_por_id != self.request.user.id:
            raise PermissionDenied('Conta bancária inválida para o seu perfil.')
        if categoria and not self.request.user.is_administrador():
            if categoria.criado_por_id not in (None, self.request.user.id):
                raise PermissionDenied('Categoria inválida para o seu perfil.')

        serializer.save(criado_por=self.request.user)

    def perform_update(self, serializer):
        processo = serializer.validated_data.get('processo', serializer.instance.processo)
        conta = serializer.validated_data.get('conta_bancaria', serializer.instance.conta_bancaria)
        categoria = serializer.validated_data.get('categoria', serializer.instance.categoria)

        if processo and not _processo_disponivel_para_usuario(self.request.user, processo):
            raise PermissionDenied('Você não pode vincular lançamento a processo de outro advogado.')
        if conta and not self.request.user.is_administrador() and conta.criado_por_id != self.request.user.id:
            raise PermissionDenied('Conta bancária inválida para o seu perfil.')
        if categoria and not self.request.user.is_administrador():
            if categoria.criado_por_id not in (None, self.request.user.id):
                raise PermissionDenied('Categoria inválida para o seu perfil.')

        serializer.save()

    @action(detail=True, methods=['post'])
    def baixar(self, request, pk=None):
        lancamento = self.get_object()
        data_pagamento = request.data.get('data_pagamento')
        if not data_pagamento:
            return Response(
                {'error': 'data_pagamento é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            data_pagamento = date.fromisoformat(str(data_pagamento))
        except ValueError:
            return Response(
                {'error': 'data_pagamento inválido. Use o formato YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conta_id = request.data.get('conta_bancaria_id', request.data.get('conta_bancaria'))
        conta = None
        if conta_id not in (None, ''):
            contas_qs = ContaBancaria.objects.all()
            if not request.user.is_administrador():
                contas_qs = contas_qs.filter(criado_por=request.user)
            try:
                conta = contas_qs.get(pk=conta_id)
            except ContaBancaria.DoesNotExist:
                return Response(
                    {'error': 'Conta bancária inválida para o seu perfil.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        lancamento.data_pagamento = data_pagamento
        lancamento.status = 'pago'
        if conta is not None:
            lancamento.conta_bancaria = conta
        lancamento.save()

        return Response(self.get_serializer(lancamento).data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Resumo financeiro (compatível com o frontend SPA e telas legadas)."""
        hoje = timezone.now().date()
        qs = self.get_queryset()

        inicio_mes = hoje.replace(day=1)
        inicio_proximo_mes = _add_months(inicio_mes, 1)

        totais = qs.aggregate(
            total_pendente=Sum('valor', filter=Q(status='pendente')),
            total_pago=Sum('valor', filter=Q(status='pago')),
            total_atrasado=Sum('valor', filter=Q(status='atrasado') | Q(status='pendente', data_vencimento__lt=hoje)),
            qtd_pendente=Count('id', filter=Q(status='pendente')),
            qtd_pago=Count('id', filter=Q(status='pago')),
            qtd_atrasado=Count('id', filter=Q(status='atrasado') | Q(status='pendente', data_vencimento__lt=hoje)),
        )

        proximos = qs.filter(
            status='pendente',
            data_vencimento__gte=hoje,
            data_vencimento__lte=hoje + timedelta(days=7),
        ).order_by('data_vencimento')[:5]

        atrasados = qs.filter(Q(status='atrasado') | Q(status='pendente', data_vencimento__lt=hoje)).order_by('data_vencimento')[:5]
        recentes = qs.filter(status='pago').order_by('-data_pagamento')[:5]

        a_receber_mes = qs.filter(
            tipo__in=Lancamento.tipos_receber(),
            status='pendente',
            data_vencimento__gte=inicio_mes,
            data_vencimento__lt=inicio_proximo_mes,
        ).aggregate(total=Sum('valor'))['total'] or 0

        a_pagar_mes = qs.filter(
            tipo__in=Lancamento.tipos_pagar(),
            status='pendente',
            data_vencimento__gte=inicio_mes,
            data_vencimento__lt=inicio_proximo_mes,
        ).aggregate(total=Sum('valor'))['total'] or 0

        receitas_mes = qs.filter(
            tipo__in=Lancamento.tipos_receber(),
            status='pago',
            data_pagamento__gte=inicio_mes,
            data_pagamento__lt=inicio_proximo_mes,
        ).aggregate(total=Sum('valor'))['total'] or 0

        despesas_mes = qs.filter(
            tipo__in=Lancamento.tipos_pagar(),
            status='pago',
            data_pagamento__gte=inicio_mes,
            data_pagamento__lt=inicio_proximo_mes,
        ).aggregate(total=Sum('valor'))['total'] or 0

        atrasados_valor = qs.filter(
            Q(status='atrasado') | Q(status='pendente', data_vencimento__lt=hoje)
        ).aggregate(total=Sum('valor'))['total'] or 0
        atrasados_count = qs.filter(Q(status='atrasado') | Q(status='pendente', data_vencimento__lt=hoje)).count()

        contas_qs = ContaBancaria.objects.all()
        if not request.user.is_administrador():
            contas_qs = contas_qs.filter(criado_por=request.user)
        contas = list(contas_qs)
        if contas:
            saldo_total = sum((conta.saldo or 0) for conta in contas)
        else:
            entradas_pagas = qs.filter(
                tipo__in=Lancamento.tipos_receber(), status='pago'
            ).aggregate(total=Sum('valor'))['total'] or 0
            saidas_pagas = qs.filter(
                tipo__in=Lancamento.tipos_pagar(), status='pago'
            ).aggregate(total=Sum('valor'))['total'] or 0
            saldo_total = entradas_pagas - saidas_pagas

        grafico = []
        for offset in range(-5, 1):
            inicio_ref = _add_months(inicio_mes, offset)
            fim_ref = _add_months(inicio_ref, 1)
            receitas_ref = qs.filter(
                status='pago',
                tipo__in=Lancamento.tipos_receber(),
                data_pagamento__gte=inicio_ref,
                data_pagamento__lt=fim_ref,
            ).aggregate(total=Sum('valor'))['total'] or 0
            despesas_ref = qs.filter(
                status='pago',
                tipo__in=Lancamento.tipos_pagar(),
                data_pagamento__gte=inicio_ref,
                data_pagamento__lt=fim_ref,
            ).aggregate(total=Sum('valor'))['total'] or 0
            grafico.append({
                'mes': inicio_ref.strftime('%m/%Y'),
                'receitas': float(receitas_ref),
                'despesas': float(despesas_ref),
            })

        apontamentos_qs = ApontamentoTempo.objects.filter(ativo=True, faturado_em__isnull=True)
        faturas_qs = Fatura.objects.all()
        if not request.user.is_administrador():
            apontamentos_qs = apontamentos_qs.filter(
                Q(responsavel=request.user)
                | Q(criado_por=request.user)
                | Q(processo__advogado=request.user)
                | Q(processo__responsaveis__usuario=request.user, processo__responsaveis__ativo=True)
            ).distinct()
            faturas_qs = faturas_qs.filter(
                Q(criado_por=request.user)
                | Q(processo__advogado=request.user)
                | Q(processo__responsaveis__usuario=request.user, processo__responsaveis__ativo=True)
            ).distinct()

        horas_em_aberto = apontamentos_qs.aggregate(total=Sum('minutos'))['total'] or 0

        return Response({
            'saldo_total': float(saldo_total or 0),
            'a_receber_mes': float(a_receber_mes or 0),
            'a_pagar_mes': float(a_pagar_mes or 0),
            'atrasados_valor': float(atrasados_valor or 0),
            'atrasados_count': atrasados_count,
            'receitas_mes': float(receitas_mes or 0),
            'despesas_mes': float(despesas_mes or 0),
            'grafico_6_meses': grafico,
            'totais': {
                'pendente': float(totais['total_pendente'] or 0),
                'pago': float(totais['total_pago'] or 0),
                'atrasado': float(totais['total_atrasado'] or 0),
                'qtd_pendente': totais['qtd_pendente'],
                'qtd_pago': totais['qtd_pago'],
                'qtd_atrasado': totais['qtd_atrasado'],
            },
            'proximos_vencimentos': LancamentoSerializer(proximos, many=True).data,
            'atrasados': LancamentoSerializer(atrasados, many=True).data,
            'ultimos_pagos': LancamentoSerializer(recentes, many=True).data,
            'time_tracking_horas_abertas': float(Decimal(horas_em_aberto) / Decimal('60')),
            'faturas_abertas': faturas_qs.filter(status__in=['rascunho', 'enviada']).count(),
            'recebimentos_online_aguardando': faturas_qs.filter(online_status='aguardando').count(),
        })

    @action(detail=True, methods=['get', 'post'], url_path='arquivos')
    def arquivos(self, request, pk=None):
        lancamento = self.get_object()
        if request.method == 'GET':
            qs = lancamento.arquivos.select_related('enviado_por').all()
            serializer = LancamentoArquivoSerializer(qs, many=True, context={'request': request})
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
            validate_upload_file(arquivo)
            criados.append(
                LancamentoArquivo.objects.create(
                    lancamento=lancamento,
                    arquivo=arquivo,
                    nome_original=arquivo.name,
                    enviado_por=request.user,
                )
            )
        serializer = LancamentoArquivoSerializer(criados, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegraCobrancaViewSet(viewsets.ModelViewSet):
    queryset = RegraCobranca.objects.select_related('cliente', 'processo', 'criado_por').all()
    serializer_class = RegraCobrancaSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]
    ordering_fields = ['criado_em', 'atualizado_em', 'titulo']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_administrador():
            return qs
        return qs.filter(
            Q(criado_por=self.request.user)
            | Q(processo__advogado=self.request.user)
            | Q(processo__responsaveis__usuario=self.request.user, processo__responsaveis__ativo=True)
            | Q(cliente__responsavel=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        processo = serializer.validated_data.get('processo')
        if processo and not _processo_disponivel_para_usuario(self.request.user, processo):
            raise PermissionDenied('Processo inválido para o seu perfil.')
        serializer.save(criado_por=self.request.user)

    def perform_update(self, serializer):
        instancia = self.get_object()
        processo = serializer.validated_data.get('processo', instancia.processo)
        if processo and not _processo_disponivel_para_usuario(self.request.user, processo):
            raise PermissionDenied('Processo inválido para o seu perfil.')
        if not self.request.user.is_administrador() and instancia.criado_por_id != self.request.user.id:
            raise PermissionDenied('Você não pode editar esta regra de cobrança.')
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_administrador() and instance.criado_por_id != self.request.user.id:
            raise PermissionDenied('Você não pode excluir esta regra de cobrança.')
        instance.delete()


class ApontamentoTempoViewSet(viewsets.ModelViewSet):
    queryset = ApontamentoTempo.objects.select_related('cliente', 'processo', 'responsavel', 'regra_cobranca').all()
    serializer_class = ApontamentoTempoSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]
    ordering_fields = ['data', 'criado_em', 'minutos']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_administrador():
            return qs
        return qs.filter(
            Q(responsavel=self.request.user)
            | Q(criado_por=self.request.user)
            | Q(processo__advogado=self.request.user)
            | Q(processo__responsaveis__usuario=self.request.user, processo__responsaveis__ativo=True)
        ).distinct()

    def perform_create(self, serializer):
        processo = serializer.validated_data.get('processo')
        if processo and not _processo_disponivel_para_usuario(self.request.user, processo):
            raise PermissionDenied('Processo inválido para o seu perfil.')
        responsavel = serializer.validated_data.get('responsavel')
        if not responsavel:
            responsavel = self.request.user
        serializer.save(criado_por=self.request.user, responsavel=responsavel)

    def perform_update(self, serializer):
        processo = serializer.validated_data.get('processo', serializer.instance.processo)
        if processo and not _processo_disponivel_para_usuario(self.request.user, processo):
            raise PermissionDenied('Processo inválido para o seu perfil.')
        serializer.save()

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        qs = self.get_queryset().filter(ativo=True)
        cliente_id = request.query_params.get('cliente')
        processo_id = request.query_params.get('processo')
        faturado = request.query_params.get('faturado')

        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        if processo_id:
            qs = qs.filter(processo_id=processo_id)
        if faturado is not None:
            valor = str(faturado).strip().lower()
            if valor in {'1', 'true', 'sim', 'yes'}:
                qs = qs.filter(faturado_em__isnull=False)
            elif valor in {'0', 'false', 'nao', 'não', 'no'}:
                qs = qs.filter(faturado_em__isnull=True)

        total_minutos = qs.aggregate(total=Sum('minutos'))['total'] or 0
        serializer = self.get_serializer(qs.order_by('-data')[:80], many=True)
        return Response({
            'total_minutos': total_minutos,
            'total_horas': float(Decimal(total_minutos) / Decimal('60')),
            'itens': serializer.data,
        })


class FaturaViewSet(viewsets.ModelViewSet):
    queryset = Fatura.objects.select_related(
        'cliente', 'processo', 'regra_cobranca', 'criado_por', 'lancamento_receber'
    ).prefetch_related('itens').all()
    serializer_class = FaturaSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]
    ordering_fields = ['criado_em', 'data_vencimento', 'status', 'numero']
    search_fields = ['numero', 'cliente__nome', 'processo__numero']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_administrador():
            return qs
        return qs.filter(
            Q(criado_por=self.request.user)
            | Q(processo__advogado=self.request.user)
            | Q(processo__responsaveis__usuario=self.request.user, processo__responsaveis__ativo=True)
            | Q(cliente__responsavel=self.request.user)
        ).distinct()

    def _next_numero(self):
        base = timezone.now().strftime('FAT-%Y%m%d')
        ultimo = Fatura.objects.filter(numero__startswith=base).aggregate(maior=Max('numero'))['maior']
        if not ultimo:
            return f'{base}-001'
        try:
            seq = int(str(ultimo).split('-')[-1]) + 1
        except Exception:
            seq = 1
        return f'{base}-{seq:03d}'

    def _validar_acesso(self, cliente, processo=None):
        if self.request.user.is_administrador():
            return
        if processo and not _processo_disponivel_para_usuario(self.request.user, processo):
            raise PermissionDenied('Processo inválido para o seu perfil.')
        if cliente.responsavel_id == self.request.user.id:
            return
        if processo and _processo_disponivel_para_usuario(self.request.user, processo):
            return
        if cliente.processos.filter(
            Q(advogado=self.request.user)
            | Q(responsaveis__usuario=self.request.user, responsaveis__ativo=True)
        ).exists():
            return
        raise PermissionDenied('Cliente inválido para o seu perfil.')

    def perform_create(self, serializer):
        cliente = serializer.validated_data['cliente']
        processo = serializer.validated_data.get('processo')
        self._validar_acesso(cliente, processo)
        serializer.save(criado_por=self.request.user, numero=self._next_numero())

    def perform_update(self, serializer):
        instancia = self.get_object()
        cliente = serializer.validated_data.get('cliente', instancia.cliente)
        processo = serializer.validated_data.get('processo', instancia.processo)
        self._validar_acesso(cliente, processo)
        serializer.save()

    @action(detail=False, methods=['post'])
    def gerar(self, request):
        cliente_id = request.data.get('cliente')
        if not cliente_id:
            return Response({'detail': 'Campo "cliente" é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        from processos.models import Cliente, Processo

        try:
            cliente = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            return Response({'detail': 'Cliente não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        processo = None
        processo_id = request.data.get('processo')
        if processo_id:
            try:
                processo = Processo.objects.get(pk=processo_id)
            except Processo.DoesNotExist:
                return Response({'detail': 'Processo não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        self._validar_acesso(cliente, processo)

        regra = None
        regra_id = request.data.get('regra_cobranca')
        if regra_id:
            try:
                regra = RegraCobranca.objects.get(pk=regra_id)
            except RegraCobranca.DoesNotExist:
                return Response({'detail': 'Regra de cobrança não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        hoje = timezone.now().date()
        periodo_inicio = request.data.get('periodo_inicio') or hoje.replace(day=1)
        periodo_fim = request.data.get('periodo_fim') or hoje
        if isinstance(periodo_inicio, str):
            periodo_inicio = date.fromisoformat(periodo_inicio)
        if isinstance(periodo_fim, str):
            periodo_fim = date.fromisoformat(periodo_fim)

        data_vencimento = request.data.get('data_vencimento')
        if not data_vencimento:
            data_vencimento = hoje + timedelta(days=7)
        elif isinstance(data_vencimento, str):
            data_vencimento = date.fromisoformat(data_vencimento)

        fatura = Fatura.objects.create(
            numero=self._next_numero(),
            cliente=cliente,
            processo=processo,
            regra_cobranca=regra,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            data_vencimento=data_vencimento,
            status='rascunho',
            criado_por=request.user,
            observacoes=request.data.get('observacoes', ''),
        )

        apontamentos_qs = ApontamentoTempo.objects.filter(
            cliente=cliente,
            ativo=True,
            faturado_em__isnull=True,
            data__gte=periodo_inicio,
            data__lte=periodo_fim,
        )
        if processo:
            apontamentos_qs = apontamentos_qs.filter(processo=processo)
        if not request.user.is_administrador():
            apontamentos_qs = apontamentos_qs.filter(
                Q(responsavel=request.user)
                | Q(criado_por=request.user)
                | Q(processo__advogado=request.user)
                | Q(processo__responsaveis__usuario=request.user, processo__responsaveis__ativo=True)
            ).distinct()

        for ap in apontamentos_qs:
            valor_hora = ap.valor_hora
            if not valor_hora and ap.regra_cobranca and ap.regra_cobranca.valor_hora:
                valor_hora = ap.regra_cobranca.valor_hora
            if not valor_hora and regra and regra.valor_hora:
                valor_hora = regra.valor_hora
            valor_hora = valor_hora or Decimal('0')
            quantidade = (Decimal(ap.minutos) / Decimal('60')).quantize(Decimal('0.01'))
            total = (quantidade * Decimal(valor_hora)).quantize(Decimal('0.01'))
            FaturaItem.objects.create(
                fatura=fatura,
                tipo_item='tempo',
                descricao=f'Apontamento {ap.data:%d/%m/%Y} - {ap.descricao}',
                quantidade=quantidade,
                valor_unitario=valor_hora,
                valor_total=total,
                apontamento=ap,
            )

        incluir_despesas = str(request.data.get('incluir_despesas_reembolsaveis', 'true')).lower() not in {'0', 'false', 'nao', 'não'}
        if incluir_despesas:
            despesas_qs = _lancamentos_por_usuario(request.user).filter(
                cliente=cliente,
                status='pago',
                tipo__in=Lancamento.tipos_pagar(),
                reembolsavel_cliente=True,
                faturado_em__isnull=True,
                data_pagamento__isnull=False,
                data_pagamento__gte=periodo_inicio,
                data_pagamento__lte=periodo_fim,
            )
            if processo:
                despesas_qs = despesas_qs.filter(processo=processo)

            for despesa in despesas_qs:
                valor = Decimal(despesa.valor or 0).quantize(Decimal('0.01'))
                FaturaItem.objects.create(
                    fatura=fatura,
                    tipo_item='despesa',
                    descricao=f'Despesa reembolsável - {despesa.descricao}',
                    quantidade=Decimal('1.00'),
                    valor_unitario=valor,
                    valor_total=valor,
                    lancamento_despesa=despesa,
                )

        if regra:
            if regra.tipo_cobranca == 'pacote' and regra.valor_pacote:
                valor = Decimal(regra.valor_pacote).quantize(Decimal('0.01'))
                FaturaItem.objects.create(
                    fatura=fatura,
                    tipo_item='servico',
                    descricao=f'Pacote - {regra.titulo}',
                    quantidade=Decimal('1.00'),
                    valor_unitario=valor,
                    valor_total=valor,
                )
            if regra.tipo_cobranca == 'recorrencia' and regra.valor_recorrente:
                valor = Decimal(regra.valor_recorrente).quantize(Decimal('0.01'))
                FaturaItem.objects.create(
                    fatura=fatura,
                    tipo_item='servico',
                    descricao=f'Recorrência - {regra.titulo}',
                    quantidade=Decimal('1.00'),
                    valor_unitario=valor,
                    valor_total=valor,
                )
            if regra.tipo_cobranca == 'exito' and regra.percentual_exito:
                base_exito = _to_decimal(request.data.get('valor_base_exito'))
                if base_exito > 0:
                    percentual = Decimal(regra.percentual_exito) / Decimal('100')
                    valor = (base_exito * percentual).quantize(Decimal('0.01'))
                    FaturaItem.objects.create(
                        fatura=fatura,
                        tipo_item='servico',
                        descricao=f'Êxito - {regra.percentual_exito}% sobre base',
                        quantidade=Decimal('1.00'),
                        valor_unitario=valor,
                        valor_total=valor,
                    )

        adicional_valor = _to_decimal(request.data.get('adicional_valor'))
        adicional_descricao = request.data.get('adicional_descricao')
        if adicional_valor > 0:
            FaturaItem.objects.create(
                fatura=fatura,
                tipo_item='ajuste',
                descricao=adicional_descricao or 'Ajuste manual',
                quantidade=Decimal('1.00'),
                valor_unitario=adicional_valor,
                valor_total=adicional_valor,
            )

        fatura.recalcular_totais()
        fatura.save(update_fields=['subtotal_tempo', 'subtotal_despesas', 'subtotal_outros', 'total', 'atualizado_em'])

        return Response(self.get_serializer(fatura).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        fatura = self.get_object()
        if fatura.status in {'cancelada', 'paga'}:
            return Response({'detail': 'Fatura não pode ser enviada neste status.'}, status=status.HTTP_400_BAD_REQUEST)

        categoria_honorarios, _ = CategoriaFinanceira.objects.get_or_create(
            nome='Honorários',
            tipo='receber',
            criado_por=None,
            defaults={'ativo': True},
        )

        descricao = f'Fatura {fatura.numero} - {fatura.cliente.nome}'
        if fatura.lancamento_receber_id:
            lancamento = fatura.lancamento_receber
            lancamento.cliente = fatura.cliente
            lancamento.processo = fatura.processo
            lancamento.categoria = categoria_honorarios
            lancamento.tipo = 'receber'
            lancamento.descricao = descricao
            lancamento.valor = fatura.total
            lancamento.data_vencimento = fatura.data_vencimento
            lancamento.status = 'pendente'
            lancamento.save()
        else:
            lancamento = Lancamento.objects.create(
                cliente=fatura.cliente,
                processo=fatura.processo,
                categoria=categoria_honorarios,
                tipo='receber',
                descricao=descricao,
                valor=fatura.total,
                data_vencimento=fatura.data_vencimento,
                status='pendente',
                observacoes=f'Gerado automaticamente pela fatura {fatura.numero}.',
                criado_por=request.user,
            )
            fatura.lancamento_receber = lancamento

        agora = timezone.now()
        apontamento_ids = list(fatura.itens.filter(apontamento__isnull=False).values_list('apontamento_id', flat=True))
        despesa_ids = list(fatura.itens.filter(lancamento_despesa__isnull=False).values_list('lancamento_despesa_id', flat=True))
        if apontamento_ids:
            ApontamentoTempo.objects.filter(id__in=apontamento_ids).update(faturado_em=agora)
        if despesa_ids:
            Lancamento.objects.filter(id__in=despesa_ids).update(faturado_em=agora)

        fatura.status = 'enviada'
        fatura.save(update_fields=['status', 'lancamento_receber', 'atualizado_em'])
        return Response(self.get_serializer(fatura).data)

    @action(detail=True, methods=['post'], url_path='gerar-link')
    def gerar_link(self, request, pk=None):
        fatura = self.get_object()
        gateway = request.data.get('gateway') or fatura.gateway or 'manual'
        if gateway not in {'manual', 'asaas', 'mercadopago', 'stripe'}:
            return Response({'detail': 'Gateway inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        external_id = request.data.get('external_id') or f'PAY-{fatura.numero}-{timezone.now().strftime("%H%M%S")}'
        base_url = request.data.get('base_url') or 'https://crm.15.228.15.4.nip.io'
        online_url = request.data.get('online_url') or f'{base_url}/financeiro/faturas/{fatura.id}/pagar/{external_id}'

        fatura.gateway = gateway
        fatura.online_external_id = external_id
        fatura.online_url = online_url
        fatura.online_status = 'aguardando'
        fatura.save(update_fields=['gateway', 'online_external_id', 'online_url', 'online_status', 'atualizado_em'])
        return Response(self.get_serializer(fatura).data)

    @action(detail=True, methods=['post'])
    def marcar_paga(self, request, pk=None):
        fatura = self.get_object()
        data_pagamento = request.data.get('data_pagamento')
        if data_pagamento:
            try:
                data_pagamento = date.fromisoformat(str(data_pagamento))
            except ValueError:
                return Response({'detail': 'data_pagamento inválida. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            data_pagamento = timezone.now().date()

        fatura.status = 'paga'
        fatura.online_status = 'pago'
        fatura.data_recebimento_online = timezone.now()
        fatura.save(update_fields=['status', 'online_status', 'data_recebimento_online', 'atualizado_em'])

        if fatura.lancamento_receber_id:
            lancamento = fatura.lancamento_receber
            lancamento.status = 'pago'
            lancamento.data_pagamento = data_pagamento
            lancamento.save(update_fields=['status', 'data_pagamento', 'atualizado_em'])

        return Response(self.get_serializer(fatura).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        fatura = self.get_object()
        if fatura.status == 'paga':
            return Response({'detail': 'Não é possível cancelar uma fatura paga.'}, status=status.HTTP_400_BAD_REQUEST)
        fatura.status = 'cancelada'
        fatura.online_status = 'cancelado'
        fatura.save(update_fields=['status', 'online_status', 'atualizado_em'])
        if fatura.lancamento_receber_id and fatura.lancamento_receber.status != 'pago':
            fatura.lancamento_receber.status = 'cancelado'
            fatura.lancamento_receber.save(update_fields=['status', 'atualizado_em'])
        return Response(self.get_serializer(fatura).data)

    @action(detail=True, methods=['get', 'post'], url_path='itens')
    def itens(self, request, pk=None):
        fatura = self.get_object()
        if request.method == 'GET':
            serializer = FaturaItemSerializer(fatura.itens.all(), many=True)
            return Response(serializer.data)

        if fatura.status != 'rascunho':
            return Response({'detail': 'Só é permitido incluir itens em faturas rascunho.'}, status=status.HTTP_400_BAD_REQUEST)

        payload = request.data.copy()
        payload['fatura'] = fatura.id
        serializer = FaturaItemSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        fatura.recalcular_totais()
        fatura.save(update_fields=['subtotal_tempo', 'subtotal_despesas', 'subtotal_outros', 'total', 'atualizado_em'])
        return Response(self.get_serializer(fatura).data, status=status.HTTP_201_CREATED)
