from rest_framework import serializers
from .models import Documento


class DocumentoSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    adicionado_por_nome = serializers.CharField(source='adicionado_por.get_full_name', read_only=True, allow_null=True)
    processo_numero = serializers.CharField(source='processo_referencia.numero', read_only=True, allow_null=True)
    tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = ['id', 'titulo', 'categoria', 'categoria_display', 'tribunal',
                  'processo_referencia', 'processo_numero', 'conteudo', 'arquivo',
                  'tags', 'tags_list', 'adicionado_por', 'adicionado_por_nome',
                  'data_decisao', 'criado_em']
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()
