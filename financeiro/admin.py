from django.contrib import admin
from .models import ContaBancaria, PlanoContas, LancamentoFinanceiro


@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = ["nome_banco", "agencia", "conta", "saldo_atual", "ativo"]
    list_filter = ["ativo"]


@admin.register(PlanoContas)
class PlanoContasAdmin(admin.ModelAdmin):
    list_display = ["nome", "tipo", "ativo"]
    list_filter = ["tipo", "ativo"]


@admin.register(LancamentoFinanceiro)
class LancamentoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ["descricao", "tipo", "valor", "data_vencimento", "status", "cliente"]
    list_filter = ["tipo", "status", "categoria"]
    search_fields = ["descricao", "cliente__nome", "processo__numero"]
    date_hierarchy = "data_vencimento"
