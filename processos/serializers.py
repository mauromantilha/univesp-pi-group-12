from rest_framework import serializers
from accounts.rbac import validar_vinculo_junior_no_processo
from core.security import decrypt_pii, encrypt_pii, validate_upload_file
from .models import (
    Comarca,
    Vara,
    TipoProcesso,
    Cliente,
    ClienteAutomacao,
    ClienteTarefa,
    ClienteContrato,
    Processo,
    ProcessoParte,
    ProcessoResponsavel,
    ProcessoTarefa,
    DocumentoTemplate,
    Movimentacao,
    ClienteArquivo,
    ProcessoArquivo,
    ProcessoPeca,
)


class ComarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comarca
        fields = ['id', 'nome', 'estado']


class VaraSerializer(serializers.ModelSerializer):
    comarca_nome = serializers.CharField(source='comarca.__str__', read_only=True)
    
    class Meta:
        model = Vara
        fields = ['id', 'nome', 'comarca', 'comarca_nome']


class TipoProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoProcesso
        fields = ['id', 'nome', 'descricao']


class ClienteSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    lead_responsavel_nome = serializers.CharField(source='lead_responsavel.get_full_name', read_only=True)
    lead_etapa_display = serializers.CharField(source='get_lead_etapa_display', read_only=True)
    qualificacao_status_display = serializers.CharField(source='get_qualificacao_status_display', read_only=True)
    conflito_interesses_status_display = serializers.CharField(source='get_conflito_interesses_status_display', read_only=True)
    processos_possiveis_nomes = serializers.SerializerMethodField()
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'ativo',
            'nome',
            'responsavel',
            'responsavel_nome',
            'lead_responsavel',
            'lead_responsavel_nome',
            'lead_origem',
            'lead_campanha',
            'lead_etapa',
            'lead_etapa_display',
            'lead_sla_resposta_em',
            'lead_ultimo_contato_em',
            'formulario_qualificacao',
            'qualificacao_status',
            'qualificacao_status_display',
            'qualificacao_score',
            'conflito_interesses_status',
            'conflito_interesses_status_display',
            'conflito_interesses_observacoes',
            'cpf_cnpj',
            'email',
            'telefone',
            'endereco',
            'demanda',
            'processos_possiveis',
            'processos_possiveis_nomes',
            'observacoes',
            'criado_em',
        ]

    def get_processos_possiveis_nomes(self, obj):
        return [tipo.nome for tipo in obj.processos_possiveis.all()]

    def validate_cpf_cnpj(self, value):
        return encrypt_pii(value)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['cpf_cnpj'] = decrypt_pii(data.get('cpf_cnpj'))
        return data


class ClienteAutomacaoSerializer(serializers.ModelSerializer):
    canal_display = serializers.CharField(source='get_canal_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)

    class Meta:
        model = ClienteAutomacao
        fields = [
            'id',
            'cliente',
            'canal',
            'canal_display',
            'tipo',
            'tipo_display',
            'status',
            'status_display',
            'mensagem',
            'agendado_em',
            'enviado_em',
            'criado_por',
            'criado_por_nome',
            'criado_em',
        ]


class ClienteTarefaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)

    class Meta:
        model = ClienteTarefa
        fields = [
            'id',
            'cliente',
            'titulo',
            'descricao',
            'status',
            'status_display',
            'prioridade',
            'prioridade_display',
            'prazo_em',
            'responsavel',
            'responsavel_nome',
            'criado_por',
            'criado_por_nome',
            'criado_em',
            'atualizado_em',
        ]


class ClienteContratoSerializer(serializers.ModelSerializer):
    tipo_documento_display = serializers.CharField(source='get_tipo_documento_display', read_only=True)
    status_assinatura_display = serializers.CharField(source='get_status_assinatura_display', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)
    arquivo_url = serializers.SerializerMethodField()

    class Meta:
        model = ClienteContrato
        fields = [
            'id',
            'cliente',
            'tipo_documento',
            'tipo_documento_display',
            'titulo',
            'arquivo',
            'arquivo_url',
            'status_assinatura',
            'status_assinatura_display',
            'assinatura_provedor',
            'assinatura_envelope_id',
            'assinatura_link',
            'assinado_em',
            'criado_por',
            'criado_por_nome',
            'criado_em',
        ]

    def get_arquivo_url(self, obj):
        request = self.context.get('request')
        if not obj.arquivo:
            return None
        if request:
            return request.build_absolute_uri(obj.arquivo.url)
        return obj.arquivo.url

    def validate_arquivo(self, value):
        return validate_upload_file(value)


class ProcessoParteSerializer(serializers.ModelSerializer):
    tipo_parte_display = serializers.CharField(source='get_tipo_parte_display', read_only=True)

    class Meta:
        model = ProcessoParte
        fields = [
            'id',
            'processo',
            'tipo_parte',
            'tipo_parte_display',
            'nome',
            'documento',
            'observacoes',
            'ativo',
            'criado_em',
        ]


class ProcessoResponsavelSerializer(serializers.ModelSerializer):
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = ProcessoResponsavel
        fields = [
            'id',
            'processo',
            'usuario',
            'usuario_nome',
            'papel',
            'papel_display',
            'ativo',
            'criado_em',
        ]

    def validate(self, attrs):
        processo = attrs.get('processo') or getattr(self.instance, 'processo', None)
        usuario = attrs.get('usuario') or getattr(self.instance, 'usuario', None)
        if not processo or not usuario:
            return attrs
        erro = validar_vinculo_junior_no_processo(processo, usuario)
        if erro:
            raise serializers.ValidationError({'usuario': erro})
        return attrs


class ProcessoTarefaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)

    class Meta:
        model = ProcessoTarefa
        fields = [
            'id',
            'processo',
            'titulo',
            'descricao',
            'status',
            'status_display',
            'prioridade',
            'prioridade_display',
            'prazo_em',
            'concluido_em',
            'responsavel',
            'responsavel_nome',
            'criado_por',
            'criado_por_nome',
            'criado_em',
            'atualizado_em',
        ]


class DocumentoTemplateSerializer(serializers.ModelSerializer):
    tipo_alvo_display = serializers.CharField(source='get_tipo_alvo_display', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)

    class Meta:
        model = DocumentoTemplate
        fields = [
            'id',
            'nome',
            'tipo_alvo',
            'tipo_alvo_display',
            'descricao',
            'conteudo_base',
            'ativo',
            'criado_por',
            'criado_por_nome',
            'criado_em',
        ]


class ClienteArquivoSerializer(serializers.ModelSerializer):
    arquivo_url = serializers.SerializerMethodField()
    enviado_por_nome = serializers.CharField(source='enviado_por.get_full_name', read_only=True)
    template_nome_resolvido = serializers.SerializerMethodField()

    class Meta:
        model = ClienteArquivo
        fields = [
            'id',
            'cliente',
            'arquivo',
            'arquivo_url',
            'nome_original',
            'titulo',
            'documento_referencia',
            'versao',
            'template',
            'template_nome',
            'template_nome_resolvido',
            'categoria',
            'descricao',
            'enviado_por',
            'enviado_por_nome',
            'criado_em',
        ]

    def get_arquivo_url(self, obj):
        request = self.context.get('request')
        if not obj.arquivo:
            return None
        if request:
            return request.build_absolute_uri(obj.arquivo.url)
        return obj.arquivo.url

    def get_template_nome_resolvido(self, obj):
        if obj.template:
            return obj.template.nome
        return obj.template_nome

    def validate_arquivo(self, value):
        return validate_upload_file(value)


class MovimentacaoSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.get_full_name', read_only=True)

    class Meta:
        model = Movimentacao
        fields = ['id', 'processo', 'data', 'titulo', 'descricao', 'autor', 'autor_nome']


class ProcessoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    advogado_nome = serializers.CharField(source='advogado.get_full_name', read_only=True)
    tipo_nome = serializers.CharField(source='tipo.nome', read_only=True)
    vara_nome = serializers.CharField(source='vara.__str__', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_caso_display = serializers.CharField(source='get_tipo_caso_display', read_only=True)
    etapa_workflow_display = serializers.CharField(source='get_etapa_workflow_display', read_only=True)
    movimentacoes = MovimentacaoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Processo
        fields = ['id', 'numero', 'cliente', 'cliente_nome',
                  'advogado', 'advogado_nome',
                  'tipo', 'tipo_nome', 'vara', 'vara_nome',
                  'status', 'status_display',
                  'segredo_justica',
                  'tipo_caso', 'tipo_caso_display',
                  'etapa_workflow', 'etapa_workflow_display',
                  'objeto', 'valor_causa',
                  'criado_em', 'atualizado_em',
                  'movimentacoes']

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        novo_status = attrs.get('status')
        if instance and novo_status and novo_status != instance.status:
            if not instance.pode_transicionar(novo_status):
                raise serializers.ValidationError({
                    'status': f'Transição de status inválida: {instance.status} -> {novo_status}.'
                })
        return attrs


class ProcessoArquivoSerializer(serializers.ModelSerializer):
    arquivo_url = serializers.SerializerMethodField()
    enviado_por_nome = serializers.CharField(source='enviado_por.get_full_name', read_only=True)
    template_nome_resolvido = serializers.SerializerMethodField()

    class Meta:
        model = ProcessoArquivo
        fields = [
            'id',
            'processo',
            'arquivo',
            'arquivo_url',
            'nome_original',
            'titulo',
            'documento_referencia',
            'versao',
            'template',
            'template_nome',
            'template_nome_resolvido',
            'categoria',
            'descricao',
            'enviado_por',
            'enviado_por_nome',
            'criado_em',
        ]

    def get_arquivo_url(self, obj):
        request = self.context.get('request')
        if not obj.arquivo:
            return None
        if request:
            return request.build_absolute_uri(obj.arquivo.url)
        return obj.arquivo.url

    def get_template_nome_resolvido(self, obj):
        if obj.template:
            return obj.template.nome
        return obj.template_nome

    def validate_arquivo(self, value):
        return validate_upload_file(value)


class ProcessoPecaSerializer(serializers.ModelSerializer):
    tipo_peca_display = serializers.CharField(source='get_tipo_peca_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    criado_por_nome = serializers.CharField(source='criado_por.get_full_name', read_only=True)
    atualizado_por_nome = serializers.CharField(source='atualizado_por.get_full_name', read_only=True)

    class Meta:
        model = ProcessoPeca
        fields = [
            'id',
            'processo',
            'titulo',
            'tipo_peca',
            'tipo_peca_display',
            'status',
            'status_display',
            'conteudo',
            'versao',
            'ia_score_qualidade',
            'ia_revisao',
            'criado_por',
            'criado_por_nome',
            'atualizado_por',
            'atualizado_por_nome',
            'criado_em',
            'atualizado_em',
        ]


class ProcessoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem"""
    cliente = serializers.IntegerField(source='cliente_id', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    tipo = serializers.IntegerField(source='tipo_id', read_only=True)
    advogado_nome = serializers.CharField(source='advogado.get_full_name', read_only=True)
    tipo_nome = serializers.CharField(source='tipo.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_caso_display = serializers.CharField(source='get_tipo_caso_display', read_only=True)
    etapa_workflow_display = serializers.CharField(source='get_etapa_workflow_display', read_only=True)
    
    class Meta:
        model = Processo
        fields = ['id', 'numero', 'cliente', 'cliente_nome',
                  'tipo', 'tipo_nome', 'valor_causa', 'objeto', 'vara',
                  'advogado_nome',
                  'segredo_justica',
                  'tipo_caso', 'tipo_caso_display',
                  'etapa_workflow', 'etapa_workflow_display',
                  'status', 'status_display',
                  'criado_em', 'atualizado_em']
