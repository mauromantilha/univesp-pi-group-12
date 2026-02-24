from rest_framework import serializers
from .models import Compromisso


class CompromissoSerializer(serializers.ModelSerializer):
    advogado_nome = serializers.CharField(source='advogado.get_full_name', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero', read_only=True, allow_null=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Compromisso
        fields = ['id', 'titulo', 'tipo', 'tipo_display', 'data', 'hora',
                  'advogado', 'advogado_nome', 'processo', 'processo_numero',
                  'descricao', 'status', 'status_display', 'criado_em']
