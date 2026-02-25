from rest_framework import serializers
from .models import Lancamento, CategoriaFinanceira, ContaBancaria


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
            'status', 'status_display', 'observacoes',
            'criado_em', 'atualizado_em',
        ]
