from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth import authenticate
from accounts.activity import registrar_atividade
from accounts.serializers import UsuarioSerializer
from .jwt_auth import set_jwt_cookies, clear_jwt_cookies


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """Login customizado que retorna JWT tokens"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'detail': 'Username e password são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response(
            {'detail': 'Credenciais inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'detail': 'Usuário inativo'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    refresh = RefreshToken.for_user(user)
    registrar_atividade(
        acao='login_api',
        request=request,
        usuario=user,
        autor=user,
        detalhes='Login realizado via API.',
    )
    
    response = Response({
        'user': UsuarioSerializer(user).data,
        'detail': 'Login realizado com sucesso.',
    })
    set_jwt_cookies(response, access_token=refresh.access_token, refresh_token=refresh)
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def refresh_view(request):
    """Renova o access token a partir do refresh token (cookie httpOnly)."""
    refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
    if not refresh_token:
        return Response({'detail': 'Refresh token ausente.'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
    serializer.is_valid(raise_exception=True)

    response = Response({'detail': 'Token renovado.'}, status=status.HTTP_200_OK)
    set_jwt_cookies(
        response,
        access_token=serializer.validated_data['access'],
        refresh_token=serializer.validated_data.get('refresh'),
    )
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """Encerra sessão removendo cookies JWT."""
    refresh_token = request.COOKIES.get('refresh_token')
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
    response = Response({'detail': 'Logout realizado.'}, status=status.HTTP_200_OK)
    clear_jwt_cookies(response)
    return response
