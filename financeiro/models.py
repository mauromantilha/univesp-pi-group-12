from django.db import models
from django.conf import settings
from processos.models import Cliente, Processo


class CategoriaFinanceira(models.Model):
    TIPO_CHOICES = [
        ('receber', 'Receber'),
        ('pagar', 'Pagar'),
    ]

    nome = models.CharField(max_length=120, verbose_name='Nome')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categorias_financeiras',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoria Financeira'
        verbose_name_plural = 'Categorias Financeiras'
        ordering = ['tipo', 'nome']
        unique_together = [('nome', 'tipo', 'criado_por')]

    def __str__(self):
        return f'{self.nome} ({self.get_tipo_display()})'


class ContaBancaria(models.Model):
    nome = models.CharField(max_length=120, verbose_name='Nome')
    banco = models.CharField(max_length=120, blank=True, verbose_name='Banco')
    agencia = models.CharField(max_length=30, blank=True, verbose_name='Agência')
    conta_numero = models.CharField(max_length=40, blank=True, verbose_name='Número da Conta')
    saldo_inicial = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Saldo Inicial')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contas_bancarias',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conta Bancária'
        verbose_name_plural = 'Contas Bancárias'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def saldo(self):
        from django.db.models import Sum

        entradas = self.lancamentos.filter(
            status='pago',
            tipo__in=Lancamento.tipos_receber(),
        ).aggregate(total=Sum('valor'))['total'] or 0
        saidas = self.lancamentos.filter(
            status='pago',
            tipo__in=Lancamento.tipos_pagar(),
        ).aggregate(total=Sum('valor'))['total'] or 0
        return (self.saldo_inicial or 0) + entradas - saidas


class Lancamento(models.Model):
    TIPO_CHOICES = [
        ('receber', 'A Receber'),
        ('pagar', 'A Pagar'),
        ('honorario', 'Honorário'),
        ('despesa', 'Despesa'),
        ('reembolso', 'Reembolso'),
        ('pagamento', 'Pagamento Recebido'),
    ]
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('atrasado', 'Atrasado'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name='Cliente',
    )
    processo = models.ForeignKey(
        Processo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos',
        verbose_name='Processo',
    )
    categoria = models.ForeignKey(
        CategoriaFinanceira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos',
        verbose_name='Categoria',
    )
    conta_bancaria = models.ForeignKey(
        ContaBancaria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos',
        verbose_name='Conta Bancária',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    descricao = models.CharField(max_length=255, verbose_name='Descrição')
    valor = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='Valor (R$)')
    data_vencimento = models.DateField(verbose_name='Vencimento')
    data_pagamento = models.DateField(null=True, blank=True, verbose_name='Data de Pagamento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name='Status')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='lancamentos_criados',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lançamento'
        verbose_name_plural = 'Lançamentos'
        ordering = ['-data_vencimento']

    def __str__(self):
        return f'{self.get_tipo_display()} – {self.cliente} – R$ {self.valor}'

    @property
    def esta_atrasado(self):
        from django.utils import timezone
        return (
            self.status == 'pendente'
            and self.data_vencimento < timezone.now().date()
        )

    @classmethod
    def tipos_receber(cls):
        return ['receber', 'honorario', 'reembolso', 'pagamento']

    @classmethod
    def tipos_pagar(cls):
        return ['pagar', 'despesa']

    @classmethod
    def normalizar_tipo(cls, tipo):
        if not tipo:
            return tipo
        valor = str(tipo).strip().lower()
        if valor in {'receita', 'receber', 'pagamento', 'honorario', 'reembolso'}:
            return 'receber' if valor in {'receita', 'receber'} else valor
        if valor in {'despesa', 'pagar'}:
            return 'pagar' if valor == 'despesa' or valor == 'pagar' else valor
        return valor

    @property
    def tipo_financeiro(self):
        if self.tipo in self.tipos_pagar():
            return 'pagar'
        return 'receber'


class LancamentoArquivo(models.Model):
    lancamento = models.ForeignKey(
        Lancamento,
        on_delete=models.CASCADE,
        related_name='arquivos',
        verbose_name='Lançamento',
    )
    arquivo = models.FileField(upload_to='financeiro/arquivos/', verbose_name='Arquivo')
    nome_original = models.CharField(max_length=255, blank=True, verbose_name='Nome Original')
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arquivos_lancamento_enviados',
        verbose_name='Enviado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Arquivo de Lançamento'
        verbose_name_plural = 'Arquivos de Lançamento'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_original or self.arquivo.name
