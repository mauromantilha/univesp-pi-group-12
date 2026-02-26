from rest_framework import serializers
from .models import AnaliseRisco, IAEventoSistema


class AnaliseRiscoSerializer(serializers.ModelSerializer):
    processo_numero = serializers.CharField(source='processo.numero', read_only=True)
    probabilidade_sucesso = serializers.SerializerMethodField()
    nivel_risco = serializers.SerializerMethodField()
    
    class Meta:
        model = AnaliseRisco
        fields = ['id', 'processo', 'processo_numero', 'probabilidade_exito',
                  'probabilidade_sucesso', 'nivel_risco',
                  'justificativa', 'processos_similares', 'vitorias_similares',
                  'atualizado_em']

    def get_probabilidade_sucesso(self, obj):
        if obj.probabilidade_exito is None:
            return None
        return float(obj.probabilidade_exito)

    def get_nivel_risco(self, obj):
        valor = float(obj.probabilidade_exito or 0)
        if valor >= 70:
            return 'baixo'
        if valor >= 40:
            return 'medio'
        return 'alto'


class IAEventoSistemaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    severidade_display = serializers.CharField(source='get_severidade_display', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)

    class Meta:
        model = IAEventoSistema
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'severidade',
            'severidade_display',
            'mensagem',
            'rota',
            'detalhes',
            'resolvido',
            'criado_por',
            'criado_por_nome',
            'criado_em',
            'atualizado_em',
        ]
