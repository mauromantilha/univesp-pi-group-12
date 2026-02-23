from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Evento
from .serializers import EventoSerializer


class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.select_related('responsavel', 'processo').all()
    serializer_class = EventoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'responsavel', 'processo', 'concluido']
    search_fields = ['titulo', 'descricao', 'local']
    ordering_fields = ['data_inicio']

    @action(detail=False, methods=['get'], url_path='meus-eventos')
    def meus_eventos(self, request):
        qs = self.queryset.filter(responsavel=request.user)
        serializer = EventoSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='prazos-proximos')
    def prazos_proximos(self, request):
        dias = int(request.query_params.get('dias', 7))
        limite = timezone.now() + timezone.timedelta(days=dias)
        qs = self.queryset.filter(
            responsavel=request.user,
            tipo='prazo',
            data_inicio__lte=limite,
            concluido=False
        )
        serializer = EventoSerializer(qs, many=True)
        return Response(serializer.data)
