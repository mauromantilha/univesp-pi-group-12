from rest_framework import serializers
from .models import (
    Comarca,
    Vara,
    TipoProcesso,
    Cliente,
    Processo,
    Movimentacao,
    ClienteArquivo,
    ProcessoArquivo,
)


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
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    processos_possiveis_nomes = serializers.SerializerMethodField()
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'ativo',
            'nome',
            'responsavel',
            'responsavel_nome',
            'cpf_cnpj',
            'email',
            'telefone',
            'endereco',
            'demanda',
            'processos_possiveis',
            'processos_possiveis_nomes',
            'observacoes',
            'criado_em',
        ]

    def get_processos_possiveis_nomes(self, obj):
        return [tipo.nome for tipo in obj.processos_possiveis.all()]


class ClienteArquivoSerializer(serializers.ModelSerializer):
    arquivo_url = serializers.SerializerMethodField()
    enviado_por_nome = serializers.CharField(source='enviado_por.get_full_name', read_only=True)

    class Meta:
        model = ClienteArquivo
        fields = [
            'id',
            'cliente',
            'arquivo',
            'arquivo_url',
            'nome_original',
            'enviado_por',
            'enviado_por_nome',
            'criado_em',
        ]

    def get_arquivo_url(self, obj):
        request = self.context.get('request')
        if not obj.arquivo:
            return None
        if request:
            return request.build_absolute_uri(obj.arquivo.url)
        return obj.arquivo.url


class MovimentacaoSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.get_full_name', read_only=True)

    class Meta:
        model = Movimentacao
        fields = ['id', 'processo', 'data', 'titulo', 'descricao', 'autor', 'autor_nome']


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
                  'criado_em', 'atualizado_em',
                  'movimentacoes']


class ProcessoArquivoSerializer(serializers.ModelSerializer):
    arquivo_url = serializers.SerializerMethodField()
    enviado_por_nome = serializers.CharField(source='enviado_por.get_full_name', read_only=True)

    class Meta:
        model = ProcessoArquivo
        fields = [
            'id',
            'processo',
            'arquivo',
            'arquivo_url',
            'nome_original',
            'enviado_por',
            'enviado_por_nome',
            'criado_em',
        ]

    def get_arquivo_url(self, obj):
        request = self.context.get('request')
        if not obj.arquivo:
            return None
        if request:
            return request.build_absolute_uri(obj.arquivo.url)
        return obj.arquivo.url


class ProcessoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem"""
    cliente = serializers.IntegerField(source='cliente_id', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    tipo = serializers.IntegerField(source='tipo_id', read_only=True)
    advogado_nome = serializers.CharField(source='advogado.get_full_name', read_only=True)
    tipo_nome = serializers.CharField(source='tipo.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Processo
        fields = ['id', 'numero', 'cliente', 'cliente_nome',
                  'tipo', 'tipo_nome', 'valor_causa', 'objeto', 'vara',
                  'advogado_nome',
                  'status', 'status_display',
                  'criado_em', 'atualizado_em']
