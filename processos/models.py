from django.db import models
from django.conf import settings


class Comarca(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Nome')
    estado = models.CharField(max_length=2, verbose_name='Estado (UF)')

    class Meta:
        verbose_name = 'Comarca'
        verbose_name_plural = 'Comarcas'
        ordering = ['estado', 'nome']

    def __str__(self):
        return f'{self.nome}/{self.estado}'


class Vara(models.Model):
    nome = models.CharField(max_length=150, verbose_name='Nome da Vara')
    comarca = models.ForeignKey(Comarca, on_delete=models.CASCADE, related_name='varas', verbose_name='Comarca')

    class Meta:
        verbose_name = 'Vara'
        verbose_name_plural = 'Varas'
        ordering = ['comarca', 'nome']

    def __str__(self):
        return f'{self.nome} - {self.comarca}'


class TipoProcesso(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Tipo')
    descricao = models.TextField(blank=True, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Tipo de Processo'
        verbose_name_plural = 'Tipos de Processo'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    TIPO_CHOICES = [('pf', 'Pessoa Física'), ('pj', 'Pessoa Jurídica')]
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='pf', verbose_name='Tipo')
    nome = models.CharField(max_length=200, verbose_name='Nome / Razão Social')
    cpf_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name='CPF / CNPJ')
    email = models.EmailField(blank=True, null=True, verbose_name='E-mail')
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    endereco = models.TextField(blank=True, null=True, verbose_name='Endereço')
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Processo(models.Model):
    STATUS_CHOICES = [
        ('em_andamento', 'Em Andamento'),
        ('suspenso', 'Suspenso'),
        ('finalizado', 'Finalizado'),
        ('arquivado', 'Arquivado'),
    ]
    numero = models.CharField(max_length=30, unique=True, verbose_name='Número do Processo')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='processos', verbose_name='Cliente')
    advogado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processos',
        verbose_name='Advogado Responsável',
        limit_choices_to={'papel__in': ['advogado', 'administrador']},
    )
    tipo = models.ForeignKey(TipoProcesso, on_delete=models.SET_NULL, null=True, verbose_name='Tipo')
    vara = models.ForeignKey(Vara, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Vara')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento', verbose_name='Status')
    valor_causa = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Valor da Causa (R$)')
    objeto = models.TextField(verbose_name='Objeto / Descrição')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Processo'
        verbose_name_plural = 'Processos'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.numero} - {self.cliente}'


class ProcessoArquivo(models.Model):
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='arquivos',
        verbose_name='Processo',
    )
    arquivo = models.FileField(upload_to='processos/arquivos/', verbose_name='Arquivo')
    nome_original = models.CharField(max_length=255, blank=True, verbose_name='Nome Original')
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arquivos_processo_enviados',
        verbose_name='Enviado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Arquivo do Processo'
        verbose_name_plural = 'Arquivos do Processo'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_original or self.arquivo.name


class Movimentacao(models.Model):
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name='movimentacoes', verbose_name='Processo')
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Autor',
    )
    data = models.DateField(verbose_name='Data')
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descricao = models.TextField(verbose_name='Descrição')
    documento = models.FileField(upload_to='movimentacoes/', blank=True, null=True, verbose_name='Documento Anexo')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        return f'{self.data} - {self.titulo}'
