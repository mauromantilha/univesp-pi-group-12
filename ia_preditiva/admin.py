from django.contrib import admin
from .models import AnaliseRisco


@admin.register(AnaliseRisco)
class AnaliseRiscoAdmin(admin.ModelAdmin):
    list_display = ('processo', 'probabilidade_exito', 'processos_similares', 'vitorias_similares', 'atualizado_em')
    readonly_fields = ('atualizado_em',)
