from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, timedelta
from django_filters.rest_framework import DjangoFilterBackend

from .models import ContaBancaria, PlanoContas, LancamentoFinanceiro
from .serializers import (
    ContaBancariaSerializer, PlanoContasSerializer, LancamentoFinanceiroSerializer
)


class ContaBancariaViewSet(viewsets.ModelViewSet):
    queryset = ContaBancaria.objects.filter(ativo=True)
    serializer_class = ContaBancariaSerializer

    @action(detail=True, methods=["get"], url_path="extrato")
    def extrato(self, request, pk=None):
        conta = self.get_object()
        lancamentos = LancamentoFinanceiro.objects.filter(
            conta_bancaria=conta, status="pago"
        ).select_related("cliente", "categoria", "processo").order_by("-data_pagamento")
        serializer = LancamentoFinanceiroSerializer(
            lancamentos, many=True, context={"request": request}
        )
        return Response({
            "conta": ContaBancariaSerializer(conta).data,
            "lancamentos": serializer.data,
        })


class PlanoContasViewSet(viewsets.ModelViewSet):
    queryset = PlanoContas.objects.filter(ativo=True)
    serializer_class = PlanoContasSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo"]


class LancamentoFinanceiroViewSet(viewsets.ModelViewSet):
    queryset = LancamentoFinanceiro.objects.select_related(
        "cliente", "processo", "conta_bancaria", "categoria"
    ).all()
    serializer_class = LancamentoFinanceiroSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo", "status", "cliente", "processo", "conta_bancaria", "categoria"]
    search_fields = ["descricao", "cliente__nome", "processo__numero"]
    ordering_fields = ["data_vencimento", "valor", "criado_em"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Auto-calculates atrasado status on the fly
        hoje = date.today()
        qs = qs.exclude(status__in=["pago", "cancelado"])
        qs_atrasado = LancamentoFinanceiro.objects.filter(
            data_vencimento__lt=hoje, status="pendente"
        ).update(status="atrasado")
        return super().get_queryset()

    @action(detail=True, methods=["post"], url_path="baixar")
    def baixar(self, request, pk=None):
        lancamento = self.get_object()
        data_pagamento = request.data.get("data_pagamento")
        conta_id = request.data.get("conta_bancaria_id")

        if not data_pagamento:
            return Response(
                {"erro": "data_pagamento e obrigatoria"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conta = None
        if conta_id:
            try:
                conta = ContaBancaria.objects.get(pk=conta_id)
            except ContaBancaria.DoesNotExist:
                return Response(
                    {"erro": "Conta bancaria nao encontrada"},
                    status=status.HTTP_404_NOT_FOUND
                )

        try:
            lancamento.baixar(data_pagamento, conta_bancaria=conta)
        except ValueError as e:
            return Response({"erro": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(lancamento)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        proximo_mes = (inicio_mes + timedelta(days=32)).replace(day=1)

        # Atualiza atrasados
        LancamentoFinanceiro.objects.filter(
            data_vencimento__lt=hoje, status="pendente"
        ).update(status="atrasado")

        receitas_mes = LancamentoFinanceiro.objects.filter(
            tipo="receber", status="pago",
            data_pagamento__gte=inicio_mes, data_pagamento__lt=proximo_mes
        ).aggregate(total=Sum("valor"))["total"] or 0

        despesas_mes = LancamentoFinanceiro.objects.filter(
            tipo="pagar", status="pago",
            data_pagamento__gte=inicio_mes, data_pagamento__lt=proximo_mes
        ).aggregate(total=Sum("valor"))["total"] or 0

        a_receber = LancamentoFinanceiro.objects.filter(
            tipo="receber",
            data_vencimento__gte=inicio_mes,
            data_vencimento__lt=proximo_mes,
            status__in=["pendente", "atrasado"]
        ).aggregate(total=Sum("valor"))["total"] or 0

        a_pagar = LancamentoFinanceiro.objects.filter(
            tipo="pagar",
            data_vencimento__gte=inicio_mes,
            data_vencimento__lt=proximo_mes,
            status__in=["pendente", "atrasado"]
        ).aggregate(total=Sum("valor"))["total"] or 0

        atrasados_count = LancamentoFinanceiro.objects.filter(
            status="atrasado"
        ).count()

        atrasados_valor = LancamentoFinanceiro.objects.filter(
            status="atrasado"
        ).aggregate(total=Sum("valor"))["total"] or 0

        saldo_total = ContaBancaria.objects.filter(
            ativo=True
        ).aggregate(total=Sum("saldo_atual"))["total"] or 0

        # Grafico 6 meses
        grafico = []
        for i in range(5, -1, -1):
            mes_ref = hoje.replace(day=1) - timedelta(days=i * 28)
            mes_ref = mes_ref.replace(day=1)
            prox = (mes_ref + timedelta(days=32)).replace(day=1)
            rec = LancamentoFinanceiro.objects.filter(
                tipo="receber", status="pago",
                data_pagamento__gte=mes_ref, data_pagamento__lt=prox
            ).aggregate(total=Sum("valor"))["total"] or 0
            desp = LancamentoFinanceiro.objects.filter(
                tipo="pagar", status="pago",
                data_pagamento__gte=mes_ref, data_pagamento__lt=prox
            ).aggregate(total=Sum("valor"))["total"] or 0
            grafico.append({
                "mes": mes_ref.strftime("%b/%Y"),
                "receitas": float(rec),
                "despesas": float(desp),
            })

        return Response({
            "receitas_mes": float(receitas_mes),
            "despesas_mes": float(despesas_mes),
            "a_receber_mes": float(a_receber),
            "a_pagar_mes": float(a_pagar),
            "atrasados_count": atrasados_count,
            "atrasados_valor": float(atrasados_valor),
            "saldo_total": float(saldo_total),
            "grafico_6_meses": grafico,
        })
