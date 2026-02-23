from django.contrib import admin
from .models import Compromisso


@admin.register(Compromisso)
class CompromissoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'data', 'hora', 'advogado', 'status')
    list_filter = ('tipo', 'status', 'advogado')
    search_fields = ('titulo',)
