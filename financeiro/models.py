from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

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
    reembolsavel_cliente = models.BooleanField(default=False, verbose_name='Reembolsável ao Cliente')
    faturado_em = models.DateTimeField(null=True, blank=True, verbose_name='Faturado em')
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


class RegraCobranca(models.Model):
    TIPO_COBRANCA_CHOICES = [
        ('hora', 'Hora'),
        ('exito', 'Êxito'),
        ('pacote', 'Pacote'),
        ('recorrencia', 'Recorrência'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='regras_cobranca',
        verbose_name='Cliente',
    )
    processo = models.ForeignKey(
        Processo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='regras_cobranca',
        verbose_name='Processo',
    )
    titulo = models.CharField(max_length=180, verbose_name='Título da Regra')
    tipo_cobranca = models.CharField(max_length=20, choices=TIPO_COBRANCA_CHOICES, verbose_name='Tipo de Cobrança')
    valor_hora = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Valor/Hora')
    percentual_exito = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Percentual de Êxito (%)',
    )
    valor_pacote = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Valor do Pacote')
    valor_recorrente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Recorrente',
    )
    dia_vencimento_recorrencia = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Dia de Vencimento da Recorrência',
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='regras_cobranca_criadas',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Regra de Cobrança'
        verbose_name_plural = 'Regras de Cobrança'
        ordering = ['-atualizado_em']

    def __str__(self):
        return f'{self.titulo} - {self.cliente}'


class ApontamentoTempo(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='apontamentos_tempo',
        verbose_name='Cliente',
    )
    processo = models.ForeignKey(
        Processo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='apontamentos_tempo',
        verbose_name='Processo',
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='apontamentos_tempo_responsavel',
        limit_choices_to={'papel__in': ['advogado', 'administrador', 'estagiario', 'assistente']},
        verbose_name='Responsável',
    )
    regra_cobranca = models.ForeignKey(
        RegraCobranca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='apontamentos',
        verbose_name='Regra de Cobrança',
    )
    data = models.DateField(default=timezone.localdate, verbose_name='Data')
    descricao = models.CharField(max_length=255, verbose_name='Descrição')
    minutos = models.PositiveIntegerField(verbose_name='Minutos Trabalhados')
    valor_hora = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Valor/Hora')
    faturado_em = models.DateTimeField(null=True, blank=True, verbose_name='Faturado em')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='apontamentos_tempo_criados',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Apontamento de Tempo'
        verbose_name_plural = 'Apontamentos de Tempo'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        return f'{self.cliente} - {self.data} - {self.minutos}min'

    @property
    def horas(self):
        return Decimal(self.minutos or 0) / Decimal('60')


class Fatura(models.Model):
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviada', 'Enviada'),
        ('paga', 'Paga'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ]
    STATUS_ONLINE_CHOICES = [
        ('nao_gerado', 'Não Gerado'),
        ('aguardando', 'Aguardando'),
        ('pago', 'Pago'),
        ('expirado', 'Expirado'),
        ('cancelado', 'Cancelado'),
    ]
    GATEWAY_CHOICES = [
        ('manual', 'Manual'),
        ('asaas', 'Asaas'),
        ('mercadopago', 'Mercado Pago'),
        ('stripe', 'Stripe'),
    ]

    numero = models.CharField(max_length=40, unique=True, verbose_name='Número da Fatura')
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='faturas',
        verbose_name='Cliente',
    )
    processo = models.ForeignKey(
        Processo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faturas',
        verbose_name='Processo',
    )
    regra_cobranca = models.ForeignKey(
        RegraCobranca,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faturas',
        verbose_name='Regra de Cobrança',
    )
    periodo_inicio = models.DateField(null=True, blank=True, verbose_name='Início do Período')
    periodo_fim = models.DateField(null=True, blank=True, verbose_name='Fim do Período')
    data_emissao = models.DateField(default=timezone.localdate, verbose_name='Data de Emissão')
    data_vencimento = models.DateField(verbose_name='Data de Vencimento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho', verbose_name='Status')
    subtotal_tempo = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Subtotal Tempo')
    subtotal_despesas = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Subtotal Despesas')
    subtotal_outros = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Subtotal Outros')
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Total')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES, default='manual', verbose_name='Gateway')
    online_status = models.CharField(
        max_length=20,
        choices=STATUS_ONLINE_CHOICES,
        default='nao_gerado',
        verbose_name='Status de Recebimento Online',
    )
    online_external_id = models.CharField(max_length=120, blank=True, null=True, verbose_name='ID Externo')
    online_url = models.URLField(blank=True, null=True, verbose_name='URL de Pagamento')
    data_recebimento_online = models.DateTimeField(blank=True, null=True, verbose_name='Data de Recebimento Online')
    lancamento_receber = models.OneToOneField(
        Lancamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fatura_origem',
        verbose_name='Lançamento Financeiro',
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faturas_criadas',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fatura'
        verbose_name_plural = 'Faturas'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.numero} - {self.cliente}'

    def recalcular_totais(self):
        agregados = self.itens.aggregate(
            tempo=models.Sum('valor_total', filter=models.Q(tipo_item='tempo')),
            despesas=models.Sum('valor_total', filter=models.Q(tipo_item='despesa')),
            outros=models.Sum('valor_total', filter=~models.Q(tipo_item__in=['tempo', 'despesa'])),
            total=models.Sum('valor_total'),
        )
        self.subtotal_tempo = agregados.get('tempo') or Decimal('0')
        self.subtotal_despesas = agregados.get('despesas') or Decimal('0')
        self.subtotal_outros = agregados.get('outros') or Decimal('0')
        self.total = agregados.get('total') or Decimal('0')


class FaturaItem(models.Model):
    TIPO_ITEM_CHOICES = [
        ('tempo', 'Tempo'),
        ('despesa', 'Despesa'),
        ('servico', 'Serviço'),
        ('ajuste', 'Ajuste'),
    ]

    fatura = models.ForeignKey(
        Fatura,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Fatura',
    )
    tipo_item = models.CharField(max_length=20, choices=TIPO_ITEM_CHOICES, verbose_name='Tipo')
    descricao = models.CharField(max_length=255, verbose_name='Descrição')
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name='Quantidade')
    valor_unitario = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='Valor Unitário')
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='Valor Total')
    apontamento = models.ForeignKey(
        ApontamentoTempo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_fatura',
        verbose_name='Apontamento de Tempo',
    )
    lancamento_despesa = models.ForeignKey(
        Lancamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens_fatura_despesa',
        verbose_name='Despesa Vinculada',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Item de Fatura'
        verbose_name_plural = 'Itens de Fatura'
        ordering = ['id']

    def __str__(self):
        return f'{self.fatura.numero} - {self.descricao}'


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
