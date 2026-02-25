from django.db import models


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
