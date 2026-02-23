from django.db import models
from django.conf import settings
from processos.models import TipoProcesso, Vara


class Documento(models.Model):
    TIPO_CHOICES = [
        ('sentenca', 'Sentença'),
        ('acordao', 'Acórdão'),
        ('peticao', 'Petição'),
        ('decisao', 'Decisão Interlocutória'),
        ('tese', 'Tese Jurídica'),
        ('outro', 'Outro'),
    ]
    titulo = models.CharField(max_length=300)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sentenca')
    tipo_processo = models.ForeignKey(TipoProcesso, on_delete=models.SET_NULL, null=True, blank=True)
    vara = models.ForeignKey(Vara, on_delete=models.SET_NULL, null=True, blank=True)
    juiz = models.CharField(max_length=200, blank=True, null=True)
    numero_processo = models.CharField(max_length=50, blank=True, null=True)
    data_decisao = models.DateField(null=True, blank=True)
    resultado = models.CharField(max_length=50, blank=True, null=True, help_text='Ex: procedente, improcedente')
    valor_causa = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    resumo = models.TextField(blank=True, null=True)
    conteudo = models.TextField(help_text='Texto completo do documento para busca')
    arquivo = models.FileField(upload_to='jurisprudencia/', blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True, null=True, help_text='Tags separadas por vírgula')
    adicionado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Documento Jurídico'
        verbose_name_plural = 'Documentos Jurídicos'
        ordering = ['-data_decisao']

    def __str__(self):
        return f'{self.titulo} ({self.get_tipo_display()})'
