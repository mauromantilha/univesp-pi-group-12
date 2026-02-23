from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Documento
from .serializers import DocumentoSerializer


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'tipo_processo', 'vara', 'resultado']
    search_fields = ['titulo', 'conteudo', 'resumo', 'tags', 'juiz', 'numero_processo']
    ordering_fields = ['data_decisao', 'criado_em', 'titulo']

    def perform_create(self, serializer):
        serializer.save(adicionado_por=self.request.user)
