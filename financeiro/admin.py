from django.contrib import admin
from .models import CategoriaFinanceira, ContaBancaria, Lancamento, LancamentoArquivo


@admin.register(CategoriaFinanceira)
class CategoriaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'ativo', 'criado_por')
    list_filter = ('tipo', 'ativo')
    search_fields = ('nome',)


@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'banco', 'agencia', 'conta_numero', 'saldo_inicial', 'criado_por')
    search_fields = ('nome', 'banco', 'agencia', 'conta_numero')


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = (
        'descricao', 'tipo', 'cliente', 'processo', 'categoria',
        'conta_bancaria', 'valor', 'data_vencimento', 'status'
    )
    list_filter = ('tipo', 'status')
    search_fields = ('descricao', 'cliente__nome')
    autocomplete_fields = []
    date_hierarchy = 'data_vencimento'


@admin.register(LancamentoArquivo)
class LancamentoArquivoAdmin(admin.ModelAdmin):
    list_display = ('nome_original', 'lancamento', 'enviado_por', 'criado_em')
    list_filter = ('criado_em',)
    search_fields = ('nome_original', 'lancamento__descricao', 'lancamento__cliente__nome')
