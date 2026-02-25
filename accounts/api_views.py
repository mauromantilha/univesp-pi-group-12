from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Usuario, UsuarioAtividadeLog
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
        serializer.save()

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
            processos_qs = Processo.objects.filter(advogado=request.user)
            clientes_qs = Cliente.objects.filter(processos__advogado=request.user).distinct()
            compromissos_qs = Compromisso.objects.filter(advogado=request.user)

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
