from django.contrib import admin
from .models import (
    Cliente,
    ClienteAutomacao,
    ClienteTarefa,
    ClienteContrato,
    Processo,
    ProcessoArquivo,
    ProcessoPeca,
    ClienteArquivo,
    Movimentacao,
    Comarca,
    Vara,
    TipoProcesso,
)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'lead_etapa', 'qualificacao_score', 'conflito_interesses_status', 'responsavel', 'cpf_cnpj')
    search_fields = ('nome', 'cpf_cnpj', 'email', 'demanda', 'lead_origem', 'lead_campanha')
    list_filter = ('tipo', 'lead_etapa', 'qualificacao_status', 'conflito_interesses_status', 'responsavel')


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'advogado', 'tipo', 'vara', 'status', 'segredo_justica', 'criado_em')
    list_filter = ('status', 'tipo', 'advogado', 'segredo_justica')
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


@admin.register(ProcessoPeca)
class ProcessoPecaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'processo', 'tipo_peca', 'status', 'versao', 'criado_por', 'atualizado_em')
    list_filter = ('tipo_peca', 'status')
    search_fields = ('titulo', 'processo__numero', 'conteudo')


@admin.register(ClienteArquivo)
class ClienteArquivoAdmin(admin.ModelAdmin):
    list_display = ('nome_original', 'cliente', 'enviado_por', 'criado_em')
    list_filter = ('criado_em',)
    search_fields = ('nome_original', 'cliente__nome')


@admin.register(ClienteAutomacao)
class ClienteAutomacaoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'canal', 'tipo', 'status', 'agendado_em', 'enviado_em', 'criado_em')
    list_filter = ('canal', 'tipo', 'status')
    search_fields = ('cliente__nome', 'mensagem')


@admin.register(ClienteTarefa)
class ClienteTarefaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'titulo', 'status', 'prioridade', 'prazo_em', 'responsavel')
    list_filter = ('status', 'prioridade')
    search_fields = ('cliente__nome', 'titulo', 'descricao')


@admin.register(ClienteContrato)
class ClienteContratoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'titulo', 'tipo_documento', 'status_assinatura', 'assinatura_provedor', 'assinado_em')
    list_filter = ('tipo_documento', 'status_assinatura')
    search_fields = ('cliente__nome', 'titulo', 'assinatura_envelope_id')


admin.site.register(Comarca)
admin.site.register(Vara)
admin.site.register(TipoProcesso)
