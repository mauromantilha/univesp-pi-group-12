from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from accounts.permissions import IsAdvogadoOuAdministradorWrite
from .models import Compromisso
from .serializers import CompromissoSerializer


class CompromissoViewSet(viewsets.ModelViewSet):
    queryset = Compromisso.objects.select_related('advogado', 'processo').all()
    serializer_class = CompromissoSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]
    ordering_fields = ['data', 'hora', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_administrador():
            return queryset
        return queryset.filter(
            Q(advogado=self.request.user)
            | Q(processo__responsaveis__usuario=self.request.user, processo__responsaveis__ativo=True)
        ).distinct()

    def perform_create(self, serializer):
        processo = serializer.validated_data.get('processo')
        if (
            processo
            and not self.request.user.is_administrador()
            and processo.advogado_id != self.request.user.id
            and not processo.responsaveis.filter(usuario=self.request.user, ativo=True).exists()
        ):
            raise PermissionDenied('Você não pode vincular compromisso a processo de outro advogado.')
        if self.request.user.is_administrador():
            serializer.save()
            return
        serializer.save(advogado=self.request.user)

    def perform_update(self, serializer):
        processo = serializer.validated_data.get('processo', serializer.instance.processo)
        if (
            processo
            and not self.request.user.is_administrador()
            and processo.advogado_id != self.request.user.id
            and not processo.responsaveis.filter(usuario=self.request.user, ativo=True).exists()
        ):
            raise PermissionDenied('Você não pode vincular compromisso a processo de outro advogado.')
        if self.request.user.is_administrador():
            serializer.save()
            return
        serializer.save(advogado=self.request.user)

    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """Retorna compromissos dos próximos 7 dias"""
        hoje = datetime.now().date()
        proximos_7_dias = hoje + timedelta(days=7)
        compromissos = self.get_queryset().filter(
            data__gte=hoje,
            data__lte=proximos_7_dias,
            status='pendente'
        )
        serializer = self.get_serializer(compromissos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='prazos-proximos')
    def prazos_proximos(self, request):
        """Retorna compromissos do tipo prazo nos próximos 7 dias"""
        hoje = timezone.now().date()
        proximos_7_dias = hoje + timedelta(days=7)
        compromissos = self.get_queryset().filter(
            data__gte=hoje,
            data__lte=proximos_7_dias,
            status='pendente',
            tipo='prazo',
        ).order_by('data')
        serializer = self.get_serializer(compromissos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mes(self, request):
        """Retorna compromissos do mês atual"""
        ano = request.query_params.get('ano')
        mes = request.query_params.get('mes')
        if not ano or not mes:
            hoje = datetime.now().date()
            ano = hoje.year
            mes = hoje.month
        compromissos = self.get_queryset().filter(
            data__year=ano,
            data__month=mes
        )
        serializer = self.get_serializer(compromissos, many=True)
        return Response(serializer.data)
