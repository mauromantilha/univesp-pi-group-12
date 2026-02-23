from django.contrib import admin
from .models import Documento

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'tribunal', 'resultado', 'data_julgamento', 'adicionado_por')
    list_filter = ('tipo', 'resultado', 'data_julgamento')
    search_fields = ('titulo', 'tribunal', 'assunto', 'tags')
    raw_id_fields = ('adicionado_por',)
