from rest_framework import serializers
from .models import Cliente, Vara, TipoProcesso, Processo, Movimentacao


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'


class VaraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vara
        fields = '__all__'


class TipoProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProcesso
        fields = '__all__'


class MovimentacaoSerializer(serializers.ModelSerializer):
    autor_nome = serializers.StringRelatedField(source='autor')

    class Meta:
        model = Movimentacao
        fields = '__all__'
        read_only_fields = ['autor', 'criado_em']


class ProcessoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.StringRelatedField(source='cliente')
    advogado_nome = serializers.StringRelatedField(source='advogado_responsavel')
    vara_nome = serializers.StringRelatedField(source='vara')
    tipo_nome = serializers.StringRelatedField(source='tipo_processo')
    total_movimentacoes = serializers.SerializerMethodField()

    class Meta:
        model = Processo
        fields = '__all__'

    def get_total_movimentacoes(self, obj):
        return obj.movimentacoes.count()


class ProcessoDetalheSerializer(ProcessoSerializer):
    movimentacoes = MovimentacaoSerializer(many=True, read_only=True)

    class Meta(ProcessoSerializer.Meta):
        pass
