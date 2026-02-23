from rest_framework import serializers
from .models import Documento


class DocumentoSerializer(serializers.ModelSerializer):
    adicionado_por_nome = serializers.StringRelatedField(source='adicionado_por')
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = Documento
        fields = '__all__'
        read_only_fields = ['adicionado_por', 'criado_em', 'atualizado_em']
