from rest_framework import serializers
from .models import AnaliseRisco, SugestaoJurisprudencia


class AnaliseRiscoSerializer(serializers.ModelSerializer):
    processo_numero = serializers.StringRelatedField(source='processo')
    probabilidade_percentual = serializers.SerializerMethodField()

    class Meta:
        model = AnaliseRisco
        fields = '__all__'

    def get_probabilidade_percentual(self, obj):
        if obj.probabilidade_exito is not None:
            return round(obj.probabilidade_exito * 100, 1)
        return None


class SugestaoJurisprudenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SugestaoJurisprudencia
        fields = '__all__'
