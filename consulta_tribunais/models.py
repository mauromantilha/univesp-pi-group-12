from django.db import models
from django.conf import settings
from django.utils import timezone


class Tribunal(models.Model):
    """Cadastro de tribunais disponíveis"""
    nome = models.CharField(max_length=200, verbose_name='Nome do Tribunal')
    sigla = models.CharField(max_length=20, unique=True, verbose_name='Sigla')
    tipo = models.CharField(max_length=50, verbose_name='Tipo', 
                           choices=[
                               ('trabalho', 'Justiça do Trabalho'),
                               ('federal', 'Justiça Federal'),
                               ('estadual', 'Justiça Estadual'),
                               ('eleitoral', 'Justiça Eleitoral'),
                               ('militar', 'Justiça Militar'),
                           ])
    regiao = models.CharField(max_length=50, blank=True, verbose_name='Região')
    api_endpoint = models.URLField(verbose_name='Endpoint da API')
    api_key = models.CharField(max_length=500, verbose_name='API Key', blank=True)
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Tribunal'
        verbose_name_plural = 'Tribunais'
        ordering = ['tipo', 'regiao']
    
    def __str__(self):
        return f"{self.sigla} - {self.nome}"


class ConsultaProcesso(models.Model):
    """Histórico de consultas realizadas"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('sucesso', 'Sucesso'),
        ('erro', 'Erro'),
    ]
    
    tribunal = models.ForeignKey(Tribunal, on_delete=models.CASCADE, 
                                related_name='consultas', verbose_name='Tribunal')
    numero_processo = models.CharField(max_length=50, verbose_name='Número do Processo')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, related_name='consultas_tribunal',
                               verbose_name='Usuário')
    processo_vinculado = models.ForeignKey('processos.Processo', on_delete=models.SET_NULL,
                                          null=True, blank=True,
                                          related_name='consultas_tribunal',
                                          verbose_name='Processo Vinculado')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                             default='pendente', verbose_name='Status')
    data_consulta = models.DateTimeField(auto_now_add=True, verbose_name='Data da Consulta')
    dados_processo = models.JSONField(null=True, blank=True, verbose_name='Dados do Processo')
    erro_mensagem = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    
    # Cache da análise por IA
    analise_ia = models.TextField(blank=True, verbose_name='Análise da IA')
    analise_atualizada_em = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Consulta de Processo'
        verbose_name_plural = 'Consultas de Processos'
        ordering = ['-data_consulta']
        indexes = [
            models.Index(fields=['numero_processo', 'tribunal']),
            models.Index(fields=['-data_consulta']),
        ]
    
    def __str__(self):
        return f"{self.numero_processo} - {self.tribunal.sigla}"


class PerguntaProcesso(models.Model):
    """Perguntas feitas sobre processos consultados"""
    consulta = models.ForeignKey(ConsultaProcesso, on_delete=models.CASCADE,
                                related_name='perguntas', verbose_name='Consulta')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, verbose_name='Usuário')
    pergunta = models.TextField(verbose_name='Pergunta')
    resposta = models.TextField(blank=True, verbose_name='Resposta da IA')
    data_pergunta = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pergunta sobre Processo'
        verbose_name_plural = 'Perguntas sobre Processos'
        ordering = ['-data_pergunta']
    
    def __str__(self):
        return f"{self.pergunta[:50]}..."
