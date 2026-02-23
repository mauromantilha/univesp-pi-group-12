from django.contrib import admin
from .models import Evento

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'data_hora', 'processo', 'responsavel', 'concluido')
    list_filter = ('tipo', 'concluido', 'data_hora')
    search_fields = ('titulo', 'descricao', 'processo__numero', 'responsavel__username')
    raw_id_fields = ('processo', 'responsavel')
    date_hierarchy = 'data_hora'
