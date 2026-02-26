from django.contrib import admin
from .models import AnaliseRisco, IAEventoSistema


@admin.register(AnaliseRisco)
class AnaliseRiscoAdmin(admin.ModelAdmin):
    list_display = ('processo', 'probabilidade_exito', 'processos_similares', 'vitorias_similares', 'atualizado_em')
    readonly_fields = ('atualizado_em',)


@admin.register(IAEventoSistema)
class IAEventoSistemaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'severidade', 'mensagem', 'resolvido', 'criado_em')
    list_filter = ('tipo', 'severidade', 'resolvido')
    search_fields = ('mensagem', 'rota')
