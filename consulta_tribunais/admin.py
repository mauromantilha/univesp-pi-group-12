from django.contrib import admin
from .models import Tribunal, ConsultaProcesso, PerguntaProcesso


@admin.register(Tribunal)
class TribunalAdmin(admin.ModelAdmin):
    list_display = ['sigla', 'nome', 'tipo', 'regiao', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'sigla']


@admin.register(ConsultaProcesso)
class ConsultaProcessoAdmin(admin.ModelAdmin):
    list_display = ['numero_processo', 'tribunal', 'usuario', 'status', 'data_consulta']
    list_filter = ['status', 'tribunal', 'data_consulta']
    search_fields = ['numero_processo']
    readonly_fields = ['data_consulta', 'analise_atualizada_em']


@admin.register(PerguntaProcesso)
class PerguntaProcessoAdmin(admin.ModelAdmin):
    list_display = ['consulta', 'usuario', 'data_pergunta', 'pergunta_resumo']
    list_filter = ['data_pergunta']
    search_fields = ['pergunta', 'resposta']
    
    def pergunta_resumo(self, obj):
        return obj.pergunta[:50] + '...' if len(obj.pergunta) > 50 else obj.pergunta
    pergunta_resumo.short_description = 'Pergunta'
