from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Usuario, UsuarioAtividadeLog
from .activity import registrar_atividade
from .rbac import processos_visiveis_queryset
from .serializers import (
    UsuarioSerializer,
    UsuarioCreateSerializer,
    UsuarioSelfUpdateSerializer,
    UsuarioAtividadeLogSerializer,
)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_administrador():
            return Usuario.objects.all()
        if self.request.user.is_advogado():
            return Usuario.objects.filter(
                Q(pk=self.request.user.pk)
                | Q(responsavel_advogado=self.request.user)
            ).distinct()
        return Usuario.objects.filter(pk=self.request.user.pk)

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        if self.action in ['update', 'partial_update'] and not self.request.user.is_administrador():
            return UsuarioSelfUpdateSerializer
        return UsuarioSerializer

    def perform_create(self, serializer):
        if not self.request.user.is_administrador():
            raise PermissionDenied('Apenas administradores podem criar usuários.')
        usuario = serializer.save()
        registrar_atividade(
            acao='usuario_criado',
            request=self.request,
            usuario=usuario,
            autor=self.request.user,
            detalhes=f'Usuário {usuario.username} criado com papel {usuario.papel}.',
            dados_extra={
                'papel': usuario.papel,
                'responsavel_advogado_id': usuario.responsavel_advogado_id,
            },
        )

    def perform_update(self, serializer):
        if not self.request.user.is_administrador() and serializer.instance.pk != self.request.user.pk:
            raise PermissionDenied('Você só pode alterar seu próprio perfil.')
        antes_ativo = serializer.instance.is_active
        usuario = serializer.save()
        if self.request.user.is_administrador():
            detalhes = f'Usuário {usuario.username} atualizado.'
            if antes_ativo != usuario.is_active:
                detalhes = (
                    f'Acesso de {usuario.username} {"reativado" if usuario.is_active else "revogado"} por administrador.'
                )
            registrar_atividade(
                acao='usuario_editado',
                request=self.request,
                usuario=usuario,
                autor=self.request.user,
                detalhes=detalhes,
                dados_extra={
                    'is_active': usuario.is_active,
                    'papel': usuario.papel,
                    'responsavel_advogado_id': usuario.responsavel_advogado_id,
                },
            )

    def perform_destroy(self, instance):
        if not self.request.user.is_administrador():
            raise PermissionDenied('Apenas administradores podem excluir usuários.')
        instance.delete()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna dados do usuário autenticado"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Resumo do dashboard para o usuário logado"""
        from processos.models import Processo, Cliente
        from agenda.models import Compromisso
        hoje = timezone.now().date()
        limite = hoje + timedelta(days=7)

        if request.user.is_administrador():
            processos_qs = Processo.objects.all()
            clientes_qs = Cliente.objects.all()
            compromissos_qs = Compromisso.objects.all()
        else:
            processos_qs = processos_visiveis_queryset(Processo.objects.all(), request.user)
            clientes_qs = Cliente.objects.filter(
                Q(processos__advogado=request.user)
                | Q(processos__responsaveis__usuario=request.user, processos__responsaveis__ativo=True)
            ).distinct()
            compromissos_qs = Compromisso.objects.filter(
                Q(advogado=request.user)
                | Q(processo__responsaveis__usuario=request.user, processo__responsaveis__ativo=True)
            ).distinct()

        total_processos = processos_qs.count()
        total_clientes = clientes_qs.count()
        eventos_hoje = compromissos_qs.filter(
            data=hoje,
            status='pendente',
        ).exclude(tipo='prazo').count()
        prazos_proximos = compromissos_qs.filter(
            data__gte=hoje,
            data__lte=limite,
            status='pendente',
            tipo='prazo',
        ).count()

        return Response({
            # Mantido por compatibilidade do frontend SPA:
            # card com label "Processos Ativos" usa esse campo.
            'processos_ativos': total_processos,
            'total_processos': total_processos,
            'total_clientes': total_clientes,
            'eventos_hoje': eventos_hoje,
            'prazos_proximos': prazos_proximos,
            # chaves legadas:
            'compromissos_hoje': eventos_hoje,
            'prazos_proximos_7_dias': prazos_proximos,
            'usuario': UsuarioSerializer(request.user).data,
        })

    @action(detail=False, methods=['get'])
    def atividades(self, request):
        """Atividades recentes para gestão de usuários."""
        try:
            limit = int(request.query_params.get('limit', 60))
        except (TypeError, ValueError):
            limit = 60
        limit = max(1, min(limit, 300))

        qs = UsuarioAtividadeLog.objects.select_related('autor', 'usuario')
        if not request.user.is_administrador():
            qs = qs.filter(Q(usuario=request.user) | Q(autor=request.user))

        serializer = UsuarioAtividadeLogSerializer(qs[:limit], many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def equipe(self, request):
        if request.user.is_administrador():
            qs = Usuario.objects.filter(papel__in=['estagiario', 'assistente']).select_related('responsavel_advogado')
        elif request.user.is_advogado():
            qs = Usuario.objects.filter(responsavel_advogado=request.user).select_related('responsavel_advogado')
        else:
            qs = Usuario.objects.none()
        serializer = UsuarioSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='revogar-acesso')
    def revogar_acesso(self, request, pk=None):
        if not request.user.is_administrador():
            raise PermissionDenied('Somente administradores podem revogar acessos.')
        usuario = self.get_object()
        if usuario.is_administrador() and Usuario.objects.filter(papel='administrador', is_active=True).count() <= 1:
            return Response({'detail': 'Não é permitido revogar o último administrador ativo.'}, status=400)
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        registrar_atividade(
            acao='usuario_editado',
            request=request,
            usuario=usuario,
            autor=request.user,
            detalhes=f'Acesso do usuário {usuario.username} revogado.',
            dados_extra={'is_active': False},
        )
        return Response(UsuarioSerializer(usuario).data)

    @action(detail=True, methods=['post'], url_path='restaurar-acesso')
    def restaurar_acesso(self, request, pk=None):
        if not request.user.is_administrador():
            raise PermissionDenied('Somente administradores podem restaurar acessos.')
        usuario = self.get_object()
        usuario.is_active = True
        usuario.save(update_fields=['is_active'])
        registrar_atividade(
            acao='usuario_editado',
            request=request,
            usuario=usuario,
            autor=request.user,
            detalhes=f'Acesso do usuário {usuario.username} restaurado.',
            dados_extra={'is_active': True},
        )
        return Response(UsuarioSerializer(usuario).data)

    @action(detail=False, methods=['get'])
    def auditoria(self, request):
        """Logs de auditoria (admin vê tudo; demais usuários, apenas seus registros)."""
        try:
            limit = int(request.query_params.get('limit', 200))
        except (TypeError, ValueError):
            limit = 200
        limit = max(1, min(limit, 500))

        qs = UsuarioAtividadeLog.objects.select_related('autor', 'usuario')
        if not request.user.is_administrador():
            qs = qs.filter(Q(usuario=request.user) | Q(autor=request.user))

        serializer = UsuarioAtividadeLogSerializer(qs[:limit], many=True)
        return Response(serializer.data)
