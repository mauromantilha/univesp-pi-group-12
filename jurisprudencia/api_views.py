from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db.models import Q
from accounts.permissions import IsAdvogadoOuAdministradorWrite
from accounts.rbac import processos_visiveis_queryset, usuario_pode_entrar_processo
from processos.models import Processo
from .models import Documento
from .serializers import DocumentoSerializer


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.select_related('adicionado_por', 'processo_referencia').all()
    serializer_class = DocumentoSerializer
    permission_classes = [IsAdvogadoOuAdministradorWrite]
    ordering_fields = ['criado_em', 'data_decisao', 'titulo']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_administrador():
            processos_ids = processos_visiveis_queryset(
                Processo.objects.all(),
                self.request.user,
            ).values_list('id', flat=True)
            queryset = queryset.filter(
                Q(adicionado_por=self.request.user)
                | Q(processo_referencia_id__in=processos_ids)
            ).distinct()
        
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

    def perform_create(self, serializer):
        processo_referencia = serializer.validated_data.get('processo_referencia')
        if (
            processo_referencia
            and not self.request.user.is_administrador()
            and not usuario_pode_entrar_processo(processo_referencia, self.request.user)
        ):
            raise PermissionDenied('Você não pode vincular documento a processo de outro advogado.')
        serializer.save(adicionado_por=self.request.user)

    def perform_update(self, serializer):
        if not self.request.user.is_administrador() and serializer.instance.adicionado_por_id != self.request.user.id:
            raise PermissionDenied('Você não tem permissão para editar este documento.')
        processo_referencia = serializer.validated_data.get('processo_referencia', serializer.instance.processo_referencia)
        if (
            processo_referencia
            and not self.request.user.is_administrador()
            and not usuario_pode_entrar_processo(processo_referencia, self.request.user)
        ):
            raise PermissionDenied('Você não pode vincular documento a processo de outro advogado.')
        serializer.save(adicionado_por=serializer.instance.adicionado_por)

    def perform_destroy(self, instance):
        if not self.request.user.is_administrador() and instance.adicionado_por_id != self.request.user.id:
            raise PermissionDenied('Você não tem permissão para excluir este documento.')
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def categorias(self, request):
        """Retorna lista de categorias disponíveis"""
        return Response([
            {'value': c[0], 'label': c[1]}
            for c in Documento.CATEGORIA_CHOICES
        ])
