from django.db import models
from django.conf import settings


class Compromisso(models.Model):
    TIPO_CHOICES = [
        ('audiencia', 'Audiência'),
        ('prazo', 'Prazo Fatal'),
        ('reuniao', 'Reunião'),
        ('outro', 'Outro'),
    ]
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    titulo = models.CharField(max_length=200, verbose_name='Título')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='outro', verbose_name='Tipo')
    data = models.DateField(verbose_name='Data')
    hora = models.TimeField(null=True, blank=True, verbose_name='Hora')
    advogado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='compromissos',
        verbose_name='Advogado',
    )
    processo = models.ForeignKey(
        'processos.Processo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compromissos',
        verbose_name='Processo Vinculado',
    )
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name='Status')
    alerta_enviado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Compromisso'
        verbose_name_plural = 'Compromissos'
        ordering = ['data', 'hora']

    def __str__(self):
        return f'{self.data} – {self.titulo}'
