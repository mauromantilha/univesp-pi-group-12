from django.contrib import admin
from .models import AnaliseRisco, SugestaoJurisprudencia

@admin.register(AnaliseRisco)
class AnaliseRiscoAdmin(admin.ModelAdmin):
    list_display = ('processo', 'nivel_risco', 'probabilidade_exito', 'criado_em', 'criado_por')
    list_filter = ('nivel_risco', 'criado_em')
    search_fields = ('processo__numero',)
    raw_id_fields = ('processo', 'criado_por')

@admin.register(SugestaoJurisprudencia)
class SugestaoJurisprudenciaAdmin(admin.ModelAdmin):
    list_display = ('analise', 'documento', 'score_relevancia')
    search_fields = ('analise__processo__numero', 'documento__titulo')
