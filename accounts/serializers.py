from rest_framework import serializers
from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)
    
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'papel', 'papel_display', 'foto', 'telefone', 'is_active']
        read_only_fields = ['id']


class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                  'papel', 'telefone']
    
    def create(self, validated_data):
        user = Usuario.objects.create_user(**validated_data)
        return user
