from rest_framework import generics, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Usuario
from .serializers import UsuarioSerializer, RegistroSerializer, DashboardSerializer


class RegistroView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        from processos.models import Processo
        from agenda.models import Evento
        hoje = timezone.now().date()
        proximos_7 = timezone.now() + timezone.timedelta(days=7)

        data = {
            'usuario': request.user,
            'total_processos': Processo.objects.filter(advogado_responsavel=request.user).count(),
            'processos_em_andamento': Processo.objects.filter(
                advogado_responsavel=request.user, status='em_andamento'
            ).count(),
            'eventos_hoje': Evento.objects.filter(
                responsavel=request.user,
                data_inicio__date=hoje
            ).count(),
            'prazos_proximos': Evento.objects.filter(
                responsavel=request.user,
                tipo='prazo',
                data_inicio__lte=proximos_7,
                concluido=False
            ).count(),
        }
        serializer = DashboardSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='carga-trabalho')
    def carga_trabalho(self, request):
        from processos.models import Processo
        from django.db.models import Count
        dados = Usuario.objects.filter(
            papel__in=['advogado', 'administrador']
        ).annotate(
            processos_ativos=Count('processos_responsavel', filter=Processo.objects.filter(
                status='em_andamento'
            ).values('advogado_responsavel'))
        ).values('id', 'first_name', 'last_name', 'oab', 'processos_ativos')
        return Response(list(dados))
