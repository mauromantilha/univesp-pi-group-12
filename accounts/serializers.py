from rest_framework import serializers
from .models import Usuario, UsuarioAtividadeLog


class UsuarioSerializer(serializers.ModelSerializer):
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)
    
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'papel', 'papel_display', 'foto', 'telefone', 'is_active']
        read_only_fields = ['id']


class UsuarioSelfUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefone', 'foto']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                  'papel', 'telefone']
    
    def create(self, validated_data):
        user = Usuario.objects.create_user(**validated_data)
        return user


class UsuarioAtividadeLogSerializer(serializers.ModelSerializer):
    acao_display = serializers.CharField(source='get_acao_display', read_only=True)
    autor_nome = serializers.SerializerMethodField()
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model = UsuarioAtividadeLog
        fields = [
            'id',
            'acao',
            'acao_display',
            'detalhes',
            'rota',
            'ip_endereco',
            'dados_extra',
            'criado_em',
            'autor',
            'autor_nome',
            'usuario',
            'usuario_nome',
        ]

    def _nome_usuario(self, obj):
        if obj is None:
            return None
        nome = obj.get_full_name()
        return nome or obj.username

    def get_autor_nome(self, obj):
        return self._nome_usuario(obj.autor)

    def get_usuario_nome(self, obj):
        return self._nome_usuario(obj.usuario)
