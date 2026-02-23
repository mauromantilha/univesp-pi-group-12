from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'papel', 'oab', 'is_active')
    list_filter = ('papel', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'oab')
    fieldsets = UserAdmin.fieldsets + (
        ('Dados Profissionais', {'fields': ('papel', 'oab', 'telefone', 'foto', 'bio')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados Profissionais', {'fields': ('papel', 'oab', 'telefone')}),
    )
