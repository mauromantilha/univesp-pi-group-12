from rest_framework import serializers
from .models import Evento


class EventoSerializer(serializers.ModelSerializer):
    responsavel_nome = serializers.StringRelatedField(source='responsavel')
    processo_numero = serializers.StringRelatedField(source='processo')

    class Meta:
        model = Evento
        fields = '__all__'
        read_only_fields = ['criado_em']
