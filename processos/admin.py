from django.contrib import admin
from .models import Cliente, Vara, TipoProcesso, Processo, Movimentacao

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf_cnpj', 'email', 'telefone', 'criado_em')
    search_fields = ('nome', 'cpf_cnpj', 'email')
    list_filter = ('criado_em',)

@admin.register(Vara)
class VaraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'comarca', 'tribunal')
    search_fields = ('nome', 'comarca', 'tribunal')

@admin.register(TipoProcesso)
class TipoProcessoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'advogado_responsavel', 'status', 'tipo', 'criado_em')
    list_filter = ('status', 'polo_cliente', 'tipo')
    search_fields = ('numero', 'cliente__nome', 'advogado_responsavel__username')
    raw_id_fields = ('cliente', 'advogado_responsavel', 'vara')
    date_hierarchy = 'criado_em'

@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('processo', 'tipo', 'data', 'usuario')
    list_filter = ('tipo', 'data')
    search_fields = ('processo__numero', 'descricao')
    raw_id_fields = ('processo', 'usuario')
