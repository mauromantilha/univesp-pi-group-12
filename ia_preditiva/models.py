from django.db import models
from django.conf import settings
from processos.models import Processo, TipoProcesso, Vara


class AnaliseRisco(models.Model):
    processo = models.OneToOneField(Processo, on_delete=models.CASCADE, related_name='analise_risco')
    probabilidade_exito = models.FloatField(null=True, blank=True, help_text='0.0 a 1.0')
    nivel_risco = models.CharField(max_length=20, blank=True, null=True, help_text='baixo/medio/alto')
    justificativa = models.TextField(blank=True, null=True)
    baseado_em_processos = models.IntegerField(default=0, help_text='Qtd de processos similares analisados')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Análise de Risco'
        verbose_name_plural = 'Análises de Risco'

    def __str__(self):
        pct = int(self.probabilidade_exito * 100) if self.probabilidade_exito else 0
        return f'Análise: {self.processo.numero} - {pct}% êxito'


class SugestaoJurisprudencia(models.Model):
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name='sugestoes')
    documento_sugerido_id = models.IntegerField(help_text='ID do documento em jurisprudencia.Documento')
    titulo_documento = models.CharField(max_length=300)
    score_relevancia = models.FloatField(help_text='Pontuação de relevância 0.0-1.0')
    motivo = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sugestão de Jurisprudência'
        verbose_name_plural = 'Sugestões de Jurisprudência'
        ordering = ['-score_relevancia']

    def __str__(self):
        return f'Sugestão para {self.processo.numero}: {self.titulo_documento}'
