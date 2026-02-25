from datetime import date

from django.db.models import Q, Sum, Count
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.permissions import IsAdvogadoOuAdministradorWrite
from .models import Lancamento, CategoriaFinanceira, ContaBancaria, LancamentoArquivo
from .serializers import (
    LancamentoSerializer,
    CategoriaFinanceiraSerializer,
    ContaBancariaSerializer,
    LancamentoArquivoSerializer,
)


def _lancamentos_por_usuario(usuario):
    qs = Lancamento.objects.select_related(
        'cliente', 'processo', 'criado_por', 'categoria', 'conta_bancaria'
    ).all()
    if usuario.is_administrador():
        return qs
    return qs.filter(Q(criado_por=usuario) | Q(processo__advogado=usuario)).distinct()


def _add_months(inicio_mes, delta_meses):
    total = (inicio_mes.year * 12 + (inicio_mes.month - 1)) + delta_meses
    ano = total // 12
    mes = total % 12 + 1
    return date(ano, mes, 1)


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
        return qs

    def perform_create(self, serializer):
        processo = serializer.validated_data.get('processo')
        conta = serializer.validated_data.get('conta_bancaria')
        categoria = serializer.validated_data.get('categoria')

        if (
            processo
            and not self.request.user.is_administrador()
            and processo.advogado_id != self.request.user.id
        ):
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

        if (
            processo
            and not self.request.user.is_administrador()
            and processo.advogado_id != self.request.user.id
        ):
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

        ids_atrasados = list(qs.filter(status='pendente', data_vencimento__lt=hoje).values_list('id', flat=True))
        if ids_atrasados:
            Lancamento.objects.filter(id__in=ids_atrasados).update(status='atrasado')
            qs = self.get_queryset()

        inicio_mes = hoje.replace(day=1)
        inicio_proximo_mes = _add_months(inicio_mes, 1)

        totais = qs.aggregate(
            total_pendente=Sum('valor', filter=Q(status='pendente')),
            total_pago=Sum('valor', filter=Q(status='pago')),
            total_atrasado=Sum('valor', filter=Q(status='atrasado')),
            qtd_pendente=Count('id', filter=Q(status='pendente')),
            qtd_pago=Count('id', filter=Q(status='pago')),
            qtd_atrasado=Count('id', filter=Q(status='atrasado')),
        )

        proximos = qs.filter(
            status='pendente',
            data_vencimento__gte=hoje,
            data_vencimento__lte=hoje + timezone.timedelta(days=7),
        ).order_by('data_vencimento')[:5]

        atrasados = qs.filter(status='atrasado').order_by('data_vencimento')[:5]
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

        atrasados_valor = qs.filter(status='atrasado').aggregate(total=Sum('valor'))['total'] or 0
        atrasados_count = qs.filter(status='atrasado').count()

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
