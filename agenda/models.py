from django.db import models
from django.conf import settings
from processos.models import Processo


class Evento(models.Model):
    TIPO_CHOICES = [
        ('audiencia', 'Audiência'),
        ('prazo', 'Prazo Fatal'),
        ('reuniao', 'Reunião'),
        ('diligencia', 'Diligência'),
        ('outro', 'Outro'),
    ]
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='prazo')
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, null=True, blank=True, related_name='eventos')
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='eventos')
    participantes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='eventos_participante', blank=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    local = models.CharField(max_length=300, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    concluido = models.BooleanField(default=False)
    alerta_dias_antes = models.PositiveSmallIntegerField(default=3, help_text='Alertar X dias antes')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['data_inicio']

    def __str__(self):
        return f'{self.titulo} ({self.data_inicio.strftime("%d/%m/%Y")})'
