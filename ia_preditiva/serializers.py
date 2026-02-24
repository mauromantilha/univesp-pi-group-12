from rest_framework import serializers
from .models import AnaliseRisco


class AnaliseRiscoSerializer(serializers.ModelSerializer):
    processo_numero = serializers.CharField(source='processo.numero', read_only=True)
    
    class Meta:
        model = AnaliseRisco
        fields = ['id', 'processo', 'processo_numero', 'probabilidade_exito',
                  'justificativa', 'processos_similares', 'vitorias_similares',
                  'atualizado_em']
