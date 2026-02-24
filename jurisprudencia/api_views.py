from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Documento
from .serializers import DocumentoSerializer


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.select_related('adicionado_por', 'processo_referencia').all()
    serializer_class = DocumentoSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ['criado_em', 'data_decisao', 'titulo']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Busca textual
        q = self.request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(titulo__icontains=q) |
                Q(conteudo__icontains=q) |
                Q(tags__icontains=q)
            )
        
        # Filtro por categoria
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        # Filtro por tribunal
        tribunal = self.request.query_params.get('tribunal')
        if tribunal:
            queryset = queryset.filter(tribunal__icontains=tribunal)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def categorias(self, request):
        """Retorna lista de categorias disponíveis"""
        return Response([
            {'value': c[0], 'label': c[1]}
            for c in Documento.CATEGORIA_CHOICES
        ])
