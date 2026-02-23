from django.db import models
from django.conf import settings
from django.db import transaction
from decimal import Decimal


class ContaBancaria(models.Model):
    nome_banco = models.CharField(max_length=100, verbose_name="Banco")
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=30, blank=True, null=True)
    saldo_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo_atual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conta Bancaria"
        verbose_name_plural = "Contas Bancarias"
        ordering = ["nome_banco"]

    def __str__(self):
        return f"{self.nome_banco} ({self.conta or 'sem conta'})"


class PlanoContas(models.Model):
    TIPO_CHOICES = [("receita", "Receita"), ("despesa", "Despesa")]
    nome = models.CharField(max_length=150)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plano de Contas"
        verbose_name_plural = "Plano de Contas"
        ordering = ["tipo", "nome"]

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class LancamentoFinanceiro(models.Model):
    TIPO_CHOICES = [("receber", "A Receber"), ("pagar", "A Pagar")]
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("pago", "Pago"),
        ("atrasado", "Atrasado"),
        ("cancelado", "Cancelado"),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    descricao = models.CharField(max_length=300)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pendente")

    processo = models.ForeignKey(
        "processos.Processo", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lancamentos"
    )
    cliente = models.ForeignKey(
        "processos.Cliente", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lancamentos"
    )
    conta_bancaria = models.ForeignKey(
        ContaBancaria, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lancamentos"
    )
    categoria = models.ForeignKey(
        PlanoContas, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lancamentos"
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lancamento Financeiro"
        verbose_name_plural = "Lancamentos Financeiros"
        ordering = ["-data_vencimento"]

    def __str__(self):
        return f"[{self.tipo.upper()}] {self.descricao} - R$ {self.valor} ({self.status})"

    @transaction.atomic
    def baixar(self, data_pagamento, conta_bancaria=None):
        """Realiza a baixa e atualiza saldo da conta bancaria (ACID)."""
        if self.status == "pago":
            raise ValueError("Lancamento ja esta pago.")
        if conta_bancaria:
            self.conta_bancaria = conta_bancaria
        if not self.conta_bancaria:
            raise ValueError("Conta bancaria e obrigatoria para baixa.")
        self.status = "pago"
        self.data_pagamento = data_pagamento
        self.save()
        conta = ContaBancaria.objects.select_for_update().get(pk=self.conta_bancaria.pk)
        if self.tipo == "receber":
            conta.saldo_atual += Decimal(str(self.valor))
        else:
            conta.saldo_atual -= Decimal(str(self.valor))
        conta.save()
