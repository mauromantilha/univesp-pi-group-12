from decimal import Decimal

from rest_framework import serializers
from core.security import decrypt_pii, encrypt_pii, validate_upload_file

from .models import (
    Lancamento,
    CategoriaFinanceira,
    ContaBancaria,
    LancamentoArquivo,
    RegraCobranca,
    ApontamentoTempo,
    Fatura,
    FaturaItem,
)


class CategoriaFinanceiraSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaFinanceira
        fields = ['id', 'nome', 'tipo', 'ativo']


class ContaBancariaSerializer(serializers.ModelSerializer):
    saldo = serializers.SerializerMethodField()

    class Meta:
        model = ContaBancaria
        fields = [
            'id', 'nome', 'banco', 'agencia', 'conta_numero',
            'saldo_inicial', 'saldo', 'criado_em', 'atualizado_em',
        ]

    def get_saldo(self, obj):
        return float(obj.saldo or 0)

    def validate_agencia(self, value):
        return encrypt_pii(value)

    def validate_conta_numero(self, value):
        return encrypt_pii(value)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['agencia'] = decrypt_pii(data.get('agencia'))
        data['conta_numero'] = decrypt_pii(data.get('conta_numero'))
        return data


class LancamentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero', read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    conta_bancaria_nome = serializers.CharField(source='conta_bancaria.nome', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    conta_bancaria_id = serializers.PrimaryKeyRelatedField(
        source='conta_bancaria',
        queryset=ContaBancaria.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    def to_internal_value(self, data):
        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        for field in ['cliente', 'processo', 'categoria', 'conta_bancaria', 'conta_bancaria_id']:
            if mutable.get(field) == '':
                mutable[field] = None
        return super().to_internal_value(mutable)

    def validate_tipo(self, value):
        return Lancamento.normalizar_tipo(value)

    def validate(self, attrs):
        cliente = attrs.get('cliente')
        processo = attrs.get('processo')
        if not cliente and processo:
            attrs['cliente'] = processo.cliente
        if not attrs.get('cliente'):
            raise serializers.ValidationError({'cliente': 'Informe um cliente ou selecione um processo vinculado.'})
        return attrs

    class Meta:
        model = Lancamento
        fields = [
            'id', 'cliente', 'cliente_nome', 'processo', 'processo_numero',
            'categoria', 'categoria_nome',
            'conta_bancaria', 'conta_bancaria_nome', 'conta_bancaria_id',
            'tipo', 'tipo_display', 'descricao', 'valor',
            'data_vencimento', 'data_pagamento',
            'status', 'status_display',
            'reembolsavel_cliente', 'faturado_em',
            'observacoes',
            'criado_em', 'atualizado_em',
        ]


class RegraCobrancaSerializer(serializers.ModelSerializer):
    tipo_cobranca_display = serializers.CharField(source='get_tipo_cobranca_display', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero', read_only=True)

    class Meta:
        model = RegraCobranca
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'processo',
            'processo_numero',
            'titulo',
            'tipo_cobranca',
            'tipo_cobranca_display',
            'valor_hora',
            'percentual_exito',
            'valor_pacote',
            'valor_recorrente',
            'dia_vencimento_recorrencia',
            'ativo',
            'observacoes',
            'criado_em',
            'atualizado_em',
        ]

    def validate(self, attrs):
        tipo = attrs.get('tipo_cobranca') or getattr(self.instance, 'tipo_cobranca', None)
        valor_hora = attrs.get('valor_hora', getattr(self.instance, 'valor_hora', None))
        percentual_exito = attrs.get('percentual_exito', getattr(self.instance, 'percentual_exito', None))
        valor_pacote = attrs.get('valor_pacote', getattr(self.instance, 'valor_pacote', None))
        valor_recorrente = attrs.get('valor_recorrente', getattr(self.instance, 'valor_recorrente', None))

        if tipo == 'hora' and not valor_hora:
            raise serializers.ValidationError({'valor_hora': 'Informe o valor/hora para cobrança por hora.'})
        if tipo == 'exito' and not percentual_exito:
            raise serializers.ValidationError({'percentual_exito': 'Informe o percentual de êxito.'})
        if tipo == 'pacote' and not valor_pacote:
            raise serializers.ValidationError({'valor_pacote': 'Informe o valor do pacote.'})
        if tipo == 'recorrencia' and not valor_recorrente:
            raise serializers.ValidationError({'valor_recorrente': 'Informe o valor recorrente.'})

        return attrs


class ApontamentoTempoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    regra_titulo = serializers.CharField(source='regra_cobranca.titulo', read_only=True)
    horas = serializers.SerializerMethodField()
    valor_estimado = serializers.SerializerMethodField()

    class Meta:
        model = ApontamentoTempo
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'processo',
            'processo_numero',
            'responsavel',
            'responsavel_nome',
            'regra_cobranca',
            'regra_titulo',
            'data',
            'descricao',
            'minutos',
            'horas',
            'valor_hora',
            'valor_estimado',
            'faturado_em',
            'ativo',
            'criado_em',
            'atualizado_em',
        ]

    def get_horas(self, obj):
        return float(obj.horas or 0)

    def get_valor_estimado(self, obj):
        valor_hora = obj.valor_hora
        if not valor_hora and obj.regra_cobranca and obj.regra_cobranca.valor_hora:
            valor_hora = obj.regra_cobranca.valor_hora
        if not valor_hora:
            return 0.0
        return float((obj.horas or Decimal('0')) * valor_hora)

    def validate(self, attrs):
        cliente = attrs.get('cliente')
        processo = attrs.get('processo')
        if processo and cliente and processo.cliente_id != cliente.id:
            raise serializers.ValidationError({'processo': 'O processo selecionado não pertence ao cliente informado.'})
        if processo and not cliente:
            attrs['cliente'] = processo.cliente
        return attrs


class FaturaItemSerializer(serializers.ModelSerializer):
    tipo_item_display = serializers.CharField(source='get_tipo_item_display', read_only=True)

    class Meta:
        model = FaturaItem
        fields = [
            'id',
            'fatura',
            'tipo_item',
            'tipo_item_display',
            'descricao',
            'quantidade',
            'valor_unitario',
            'valor_total',
            'apontamento',
            'lancamento_despesa',
            'criado_em',
        ]


class FaturaSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    processo_numero = serializers.CharField(source='processo.numero', read_only=True)
    regra_titulo = serializers.CharField(source='regra_cobranca.titulo', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    online_status_display = serializers.CharField(source='get_online_status_display', read_only=True)
    gateway_display = serializers.CharField(source='get_gateway_display', read_only=True)
    itens = FaturaItemSerializer(many=True, read_only=True)
    lancamento_receber_id = serializers.IntegerField(source='lancamento_receber.id', read_only=True)

    class Meta:
        model = Fatura
        fields = [
            'id',
            'numero',
            'cliente',
            'cliente_nome',
            'processo',
            'processo_numero',
            'regra_cobranca',
            'regra_titulo',
            'periodo_inicio',
            'periodo_fim',
            'data_emissao',
            'data_vencimento',
            'status',
            'status_display',
            'subtotal_tempo',
            'subtotal_despesas',
            'subtotal_outros',
            'total',
            'gateway',
            'gateway_display',
            'online_status',
            'online_status_display',
            'online_external_id',
            'online_url',
            'data_recebimento_online',
            'lancamento_receber_id',
            'observacoes',
            'itens',
            'criado_em',
            'atualizado_em',
        ]

    read_only_fields = [
        'numero',
        'subtotal_tempo',
        'subtotal_despesas',
        'subtotal_outros',
        'total',
    ]


class LancamentoArquivoSerializer(serializers.ModelSerializer):
    arquivo_url = serializers.SerializerMethodField()
    enviado_por_nome = serializers.CharField(source='enviado_por.get_full_name', read_only=True)

    class Meta:
        model = LancamentoArquivo
        fields = [
            'id',
            'lancamento',
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

    def validate_arquivo(self, value):
        return validate_upload_file(value)
