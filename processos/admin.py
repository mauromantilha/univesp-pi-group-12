from django.contrib import admin
from .models import Cliente, Processo, Movimentacao, Comarca, Vara, TipoProcesso


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'cpf_cnpj', 'email', 'telefone')
    search_fields = ('nome', 'cpf_cnpj', 'email')
    list_filter = ('tipo',)


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'advogado', 'tipo', 'vara', 'status', 'criado_em')
    list_filter = ('status', 'tipo', 'advogado')
    search_fields = ('numero', 'cliente__nome')


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('processo', 'data', 'titulo', 'autor')
    list_filter = ('data',)


admin.site.register(Comarca)
admin.site.register(Vara)
admin.site.register(TipoProcesso)
