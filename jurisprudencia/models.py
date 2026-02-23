from django.db import models
from django.conf import settings


class Documento(models.Model):
    CATEGORIA_CHOICES = [
        ('sentenca', 'Sentença'),
        ('acordao', 'Acórdão'),
        ('decisao', 'Decisão Interlocutória'),
        ('tese', 'Tese Jurídica'),
        ('jurisprudencia', 'Jurisprudência Externa'),
        ('outro', 'Outro'),
    ]
    titulo = models.CharField(max_length=300, verbose_name='Título')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='outro', verbose_name='Categoria')
    tribunal = models.CharField(max_length=100, blank=True, verbose_name='Tribunal / Órgão')
    processo_referencia = models.ForeignKey(
        'processos.Processo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_juridicos',
        verbose_name='Processo Vinculado',
    )
    conteudo = models.TextField(verbose_name='Conteúdo / Ementa')
    arquivo = models.FileField(upload_to='jurisprudencia/', blank=True, null=True, verbose_name='Arquivo (PDF)')
    tags = models.CharField(max_length=300, blank=True, verbose_name='Tags (separadas por vírgula)')
    adicionado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Adicionado por',
    )
    data_decisao = models.DateField(null=True, blank=True, verbose_name='Data da Decisão')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-criado_em']

    def __str__(self):
        return self.titulo

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]
