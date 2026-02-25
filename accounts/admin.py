from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, UsuarioAtividadeLog


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'papel', 'oab', 'is_active')
    list_filter = ('papel', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Dados do Escritório', {'fields': ('papel', 'oab', 'telefone', 'foto')}),
    )


@admin.register(UsuarioAtividadeLog)
class UsuarioAtividadeLogAdmin(admin.ModelAdmin):
    list_display = ('criado_em', 'acao', 'autor', 'usuario', 'ip_endereco')
    list_filter = ('acao', 'criado_em')
    search_fields = ('detalhes', 'autor__username', 'usuario__username', 'rota', 'ip_endereco')
    readonly_fields = ('criado_em',)
