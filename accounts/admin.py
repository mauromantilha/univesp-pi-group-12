from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'papel', 'oab', 'is_active')
    list_filter = ('papel', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Dados do Escritório', {'fields': ('papel', 'oab', 'telefone', 'foto')}),
    )
