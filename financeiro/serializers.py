from rest_framework import serializers
from .models import ContaBancaria, PlanoContas, LancamentoFinanceiro


class ContaBancariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContaBancaria
        fields = "__all__"


class PlanoContasSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanoContas
        fields = "__all__"


class LancamentoFinanceiroSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.SerializerMethodField()
    processo_numero = serializers.SerializerMethodField()
    categoria_nome = serializers.SerializerMethodField()
    conta_bancaria_nome = serializers.SerializerMethodField()

    class Meta:
        model = LancamentoFinanceiro
        fields = [
            "id", "tipo", "descricao", "valor", "data_vencimento",
            "data_pagamento", "status", "processo", "processo_numero",
            "cliente", "cliente_nome", "conta_bancaria", "conta_bancaria_nome",
            "categoria", "categoria_nome", "observacoes", "criado_em",
        ]

    def get_cliente_nome(self, obj):
        return obj.cliente.nome if obj.cliente else None

    def get_processo_numero(self, obj):
        return obj.processo.numero if obj.processo else None

    def get_categoria_nome(self, obj):
        return obj.categoria.nome if obj.categoria else None

    def get_conta_bancaria_nome(self, obj):
        return str(obj.conta_bancaria) if obj.conta_bancaria else None

    def create(self, validated_data):
        validated_data["criado_por"] = self.context["request"].user
        return super().create(validated_data)
