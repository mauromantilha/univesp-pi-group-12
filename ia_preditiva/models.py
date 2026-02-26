from django.db import models
from django.conf import settings


class AnaliseRisco(models.Model):
    """Cache das análises de risco para evitar recálculos."""
    processo = models.OneToOneField(
        'processos.Processo',
        on_delete=models.CASCADE,
        related_name='analise_risco',
        verbose_name='Processo',
    )
    probabilidade_exito = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Probabilidade de Êxito (%)',
    )
    justificativa = models.TextField(blank=True, verbose_name='Justificativa')
    processos_similares = models.IntegerField(default=0, verbose_name='Processos Similares Encontrados')
    vitorias_similares = models.IntegerField(default=0, verbose_name='Vitórias em Processos Similares')
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Análise de Risco'
        verbose_name_plural = 'Análises de Risco'

    def __str__(self):
        return f'Análise – {self.processo}'


class IAEventoSistema(models.Model):
    TIPO_CHOICES = [
        ('frontend', 'Frontend'),
        ('backend', 'Backend'),
        ('integracao', 'Integração'),
        ('ia', 'IA'),
        ('financeiro', 'Financeiro'),
        ('prazos', 'Prazos'),
    ]
    SEVERIDADE_CHOICES = [
        ('info', 'Info'),
        ('alerta', 'Alerta'),
        ('critico', 'Crítico'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='backend', verbose_name='Tipo')
    severidade = models.CharField(max_length=20, choices=SEVERIDADE_CHOICES, default='alerta', verbose_name='Severidade')
    mensagem = models.CharField(max_length=300, verbose_name='Mensagem')
    rota = models.CharField(max_length=255, blank=True, verbose_name='Rota')
    detalhes = models.JSONField(blank=True, null=True, verbose_name='Detalhes')
    resolvido = models.BooleanField(default=False, verbose_name='Resolvido')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_ia_reportados',
        verbose_name='Reportado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Evento de Monitoramento IA'
        verbose_name_plural = 'Eventos de Monitoramento IA'
        ordering = ['resolvido', '-criado_em']

    def __str__(self):
        return f'{self.get_severidade_display()} - {self.mensagem}'
