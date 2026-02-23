from django.db import models
from django.conf import settings


class Cliente(models.Model):
    TIPO_PESSOA = [('fisica', 'Pessoa Física'), ('juridica', 'Pessoa Jurídica')]
    nome = models.CharField(max_length=200)
    tipo_pessoa = models.CharField(max_length=10, choices=TIPO_PESSOA, default='fisica')
    cpf_cnpj = models.CharField(max_length=20, unique=True, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    telefone2 = models.CharField(max_length=20, blank=True, null=True)
    endereco = models.CharField(max_length=300, blank=True, null=True, verbose_name="Logradouro")
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Numero")
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.cpf_cnpj or "sem doc"})'


class Vara(models.Model):
    nome = models.CharField(max_length=200)
    comarca = models.CharField(max_length=200)
    estado = models.CharField(max_length=2)
    tribunal = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = 'Vara'
        verbose_name_plural = 'Varas'
        ordering = ['comarca', 'nome']
        unique_together = ('nome', 'comarca')

    def __str__(self):
        return f'{self.nome} - {self.comarca}/{self.estado}'


class TipoProcesso(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Tipo de Processo'
        verbose_name_plural = 'Tipos de Processo'

    def __str__(self):
        return self.nome


class Processo(models.Model):
    STATUS_CHOICES = [
        ('em_andamento', 'Em Andamento'),
        ('suspenso', 'Suspenso'),
        ('finalizado', 'Finalizado'),
        ('arquivado', 'Arquivado'),
    ]
    POLO_CHOICES = [
        ('ativo', 'Ativo (autor)'),
        ('passivo', 'Passivo (réu)'),
        ('terceiro', 'Terceiro interveniente'),
    ]

    numero = models.CharField(max_length=50, unique=True, verbose_name='Número do Processo')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='processos')
    advogado_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='processos_responsavel', limit_choices_to={'papel__in': ['advogado', 'administrador']}
    )
    advogados_auxiliares = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='processos_auxiliar', blank=True
    )
    vara = models.ForeignKey(Vara, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_processo = models.ForeignKey(TipoProcesso, on_delete=models.PROTECT)
    polo = models.CharField(max_length=10, choices=POLO_CHOICES, default='ativo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento')
    parte_contraria = models.CharField(max_length=200, blank=True, null=True)
    valor_causa = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    descricao = models.TextField(blank=True, null=True)
    data_distribuicao = models.DateField(null=True, blank=True)
    data_encerramento = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Processo'
        verbose_name_plural = 'Processos'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.numero} - {self.cliente.nome}'


class Movimentacao(models.Model):
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name='movimentacoes')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data = models.DateField()
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        ordering = ['-data']

    def __str__(self):
        return f'{self.processo.numero} - {self.titulo} ({self.data})'
