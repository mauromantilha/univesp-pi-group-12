from rest_framework import serializers
from .models import Evento


class EventoSerializer(serializers.ModelSerializer):
    responsavel_nome = serializers.StringRelatedField(source='responsavel')
    processo_numero  = serializers.StringRelatedField(source='processo')
    tipo_processo_nome = serializers.SerializerMethodField()

    class Meta:
        model = Evento
        fields = '__all__'
        read_only_fields = ['criado_em']

    def get_tipo_processo_nome(self, obj):
        if obj.processo and hasattr(obj.processo, 'tipo_processo') and obj.processo.tipo_processo:
            return obj.processo.tipo_processo.nome
        return None
