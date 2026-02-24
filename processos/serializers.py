from rest_framework import serializers
from .models import Comarca, Vara, TipoProcesso, Cliente, Processo, Movimentacao


class ComarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comarca
        fields = ['id', 'nome', 'estado']


class VaraSerializer(serializers.ModelSerializer):
    comarca_nome = serializers.CharField(source='comarca.__str__', read_only=True)
    
    class Meta:
        model = Vara
        fields = ['id', 'nome', 'comarca', 'comarca_nome']


class TipoProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProcesso
        fields = ['id', 'nome', 'descricao']


class ClienteSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Cliente
        fields = ['id', 'tipo', 'tipo_display', 'nome', 'cpf_cnpj', 
                  'email', 'telefone', 'endereco']


class MovimentacaoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = Movimentacao
        fields = ['id', 'processo', 'data', 'descricao', 'usuario', 'usuario_nome']


class ProcessoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    advogado_nome = serializers.CharField(source='advogado.get_full_name', read_only=True)
    tipo_nome = serializers.CharField(source='tipo.nome', read_only=True)
    vara_nome = serializers.CharField(source='vara.__str__', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    movimentacoes = MovimentacaoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Processo
        fields = ['id', 'numero', 'cliente', 'cliente_nome', 
                  'advogado', 'advogado_nome', 
                  'tipo', 'tipo_nome', 'vara', 'vara_nome',
                  'status', 'status_display', 'objeto', 'valor_causa',
                  'data_distribuicao', 'data_ultima_movimentacao',
                  'observacoes', 'movimentacoes']


class ProcessoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem"""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    advogado_nome = serializers.CharField(source='advogado.get_full_name', read_only=True)
    tipo_nome = serializers.CharField(source='tipo.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Processo
        fields = ['id', 'numero', 'cliente_nome', 'advogado_nome', 
                  'tipo_nome', 'status', 'status_display', 
                  'data_distribuicao', 'data_ultima_movimentacao']
