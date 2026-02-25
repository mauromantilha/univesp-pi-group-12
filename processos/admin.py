from django.contrib import admin
from .models import Cliente, Processo, ProcessoArquivo, ClienteArquivo, Movimentacao, Comarca, Vara, TipoProcesso


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'responsavel', 'cpf_cnpj', 'email', 'telefone')
    search_fields = ('nome', 'cpf_cnpj', 'email', 'demanda')
    list_filter = ('tipo', 'responsavel')


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'advogado', 'tipo', 'vara', 'status', 'criado_em')
    list_filter = ('status', 'tipo', 'advogado')
    search_fields = ('numero', 'cliente__nome')


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('processo', 'data', 'titulo', 'autor')
    list_filter = ('data',)


@admin.register(ProcessoArquivo)
class ProcessoArquivoAdmin(admin.ModelAdmin):
    list_display = ('nome_original', 'processo', 'enviado_por', 'criado_em')
    list_filter = ('criado_em',)
    search_fields = ('nome_original', 'processo__numero')


@admin.register(ClienteArquivo)
class ClienteArquivoAdmin(admin.ModelAdmin):
    list_display = ('nome_original', 'cliente', 'enviado_por', 'criado_em')
    list_filter = ('criado_em',)
    search_fields = ('nome_original', 'cliente__nome')


admin.site.register(Comarca)
admin.site.register(Vara)
admin.site.register(TipoProcesso)
