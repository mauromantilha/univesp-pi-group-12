from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    nome_completo = serializers.ReadOnlyField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'nome_completo', 'papel', 'oab', 'telefone', 'foto', 'bio', 'is_active']
        read_only_fields = ['id']


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name',
                  'papel', 'oab', 'telefone', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'As senhas não coincidem.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = Usuario.objects.create_user(**validated_data)
        return user


class DashboardSerializer(serializers.Serializer):
    usuario = UsuarioSerializer()
    total_processos = serializers.IntegerField()
    processos_em_andamento = serializers.IntegerField()
    eventos_hoje = serializers.IntegerField()
    prazos_proximos = serializers.IntegerField()
