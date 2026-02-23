from django.contrib import admin
from .models import Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'tribunal', 'data_decisao', 'adicionado_por')
    list_filter = ('categoria',)
    search_fields = ('titulo', 'conteudo', 'tags')
