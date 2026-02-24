from rest_framework import serializers
from .models import Tribunal, ConsultaProcesso, PerguntaProcesso


class TribunalSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Tribunal
        fields = ['id', 'nome', 'sigla', 'tipo', 'tipo_display', 
                  'regiao', 'ativo']
        # Não expõe API key por segurança


class PerguntaProcessoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = PerguntaProcesso
        fields = ['id', 'pergunta', 'resposta', 'data_pergunta', 
                  'usuario', 'usuario_nome']


class ConsultaProcessoSerializer(serializers.ModelSerializer):
    tribunal_nome = serializers.CharField(source='tribunal.nome', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    perguntas = PerguntaProcessoSerializer(many=True, read_only=True)
    dados_formatados = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsultaProcesso
        fields = ['id', 'tribunal', 'tribunal_nome', 'numero_processo',
                  'usuario', 'usuario_nome', 'processo_vinculado',
                  'status', 'status_display', 'data_consulta',
                  'dados_processo', 'dados_formatados', 'erro_mensagem',
                  'analise_ia', 'analise_atualizada_em', 'perguntas']
    
    def get_dados_formatados(self, obj):
        """Retorna dados formatados para exibição"""
        if not obj.dados_processo:
            return None
        
        from .services.datajud_service import formatar_dados_processo
        return formatar_dados_processo(obj.dados_processo)


class ConsultaProcessoCreateSerializer(serializers.Serializer):
    """Serializer para criar nova consulta"""
    tribunal_id = serializers.IntegerField()
    numero_processo = serializers.CharField(max_length=50)
    processo_vinculado_id = serializers.IntegerField(required=False, allow_null=True)
    analisar_com_ia = serializers.BooleanField(default=True)
