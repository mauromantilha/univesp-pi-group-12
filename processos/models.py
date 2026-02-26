from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Comarca(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Nome')
    estado = models.CharField(max_length=2, verbose_name='Estado (UF)')

    class Meta:
        verbose_name = 'Comarca'
        verbose_name_plural = 'Comarcas'
        ordering = ['estado', 'nome']

    def __str__(self):
        return f'{self.nome}/{self.estado}'


class Vara(models.Model):
    nome = models.CharField(max_length=150, verbose_name='Nome da Vara')
    comarca = models.ForeignKey(Comarca, on_delete=models.CASCADE, related_name='varas', verbose_name='Comarca')

    class Meta:
        verbose_name = 'Vara'
        verbose_name_plural = 'Varas'
        ordering = ['comarca', 'nome']

    def __str__(self):
        return f'{self.nome} - {self.comarca}'


class TipoProcesso(models.Model):
    nome = models.CharField(max_length=100, verbose_name='Tipo')
    descricao = models.TextField(blank=True, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Tipo de Processo'
        verbose_name_plural = 'Tipos de Processo'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    TIPO_CHOICES = [('pf', 'Pessoa Física'), ('pj', 'Pessoa Jurídica')]
    LEAD_ETAPA_CHOICES = [
        ('novo', 'Novo'),
        ('qualificacao', 'Qualificação'),
        ('proposta', 'Proposta'),
        ('contrato', 'Contrato'),
        ('convertido', 'Convertido'),
        ('perdido', 'Perdido'),
    ]
    QUALIFICACAO_STATUS_CHOICES = [
        ('nao_iniciado', 'Não Iniciado'),
        ('em_analise', 'Em Análise'),
        ('qualificado', 'Qualificado'),
        ('desqualificado', 'Desqualificado'),
    ]
    CONFLITO_STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]

    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='pf', verbose_name='Tipo')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    nome = models.CharField(max_length=200, verbose_name='Nome / Razão Social')
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_responsavel',
        limit_choices_to={'papel__in': ['advogado', 'administrador']},
        verbose_name='Responsável',
    )
    lead_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_lead_responsavel',
        limit_choices_to={'papel__in': ['advogado', 'administrador']},
        verbose_name='Responsável do Lead',
    )
    lead_origem = models.CharField(max_length=120, blank=True, null=True, verbose_name='Origem do Lead')
    lead_campanha = models.CharField(max_length=160, blank=True, null=True, verbose_name='Campanha')
    lead_etapa = models.CharField(
        max_length=30,
        choices=LEAD_ETAPA_CHOICES,
        default='novo',
        verbose_name='Etapa do Lead',
    )
    lead_sla_resposta_em = models.DateTimeField(blank=True, null=True, verbose_name='SLA de Resposta')
    lead_ultimo_contato_em = models.DateTimeField(blank=True, null=True, verbose_name='Último Contato')

    formulario_qualificacao = models.JSONField(blank=True, null=True, verbose_name='Formulário de Qualificação')
    qualificacao_status = models.CharField(
        max_length=30,
        choices=QUALIFICACAO_STATUS_CHOICES,
        default='nao_iniciado',
        verbose_name='Status da Qualificação',
    )
    qualificacao_score = models.PositiveSmallIntegerField(default=0, verbose_name='Score da Qualificação')
    conflito_interesses_status = models.CharField(
        max_length=20,
        choices=CONFLITO_STATUS_CHOICES,
        default='pendente',
        verbose_name='Status de Conflito de Interesses',
    )
    conflito_interesses_observacoes = models.TextField(blank=True, null=True, verbose_name='Observações de Conflito')

    cpf_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name='CPF / CNPJ')
    email = models.EmailField(blank=True, null=True, verbose_name='E-mail')
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    endereco = models.TextField(blank=True, null=True, verbose_name='Endereço')
    demanda = models.TextField(blank=True, null=True, verbose_name='Demanda do Cliente')
    processos_possiveis = models.ManyToManyField(
        'TipoProcesso',
        related_name='clientes_interessados',
        blank=True,
        verbose_name='Processos Possíveis',
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ClienteAutomacao(models.Model):
    CANAL_CHOICES = [
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
    ]
    TIPO_CHOICES = [
        ('mensagem', 'Mensagem'),
        ('followup', 'Follow-up'),
        ('agendamento', 'Agendamento'),
    ]
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('enviado', 'Enviado'),
        ('falha', 'Falha'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='automacoes',
        verbose_name='Cliente',
    )
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES, verbose_name='Canal')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='mensagem', verbose_name='Tipo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendado', verbose_name='Status')
    mensagem = models.TextField(blank=True, null=True, verbose_name='Mensagem')
    agendado_em = models.DateTimeField(blank=True, null=True, verbose_name='Agendado para')
    enviado_em = models.DateTimeField(blank=True, null=True, verbose_name='Enviado em')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automacoes_cliente_criadas',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Automação de Cliente'
        verbose_name_plural = 'Automações de Cliente'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.get_canal_display()} - {self.cliente}'


class ClienteTarefa(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='tarefas',
        verbose_name='Cliente',
    )
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name='Status')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media', verbose_name='Prioridade')
    prazo_em = models.DateTimeField(blank=True, null=True, verbose_name='Prazo')
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_cliente_responsavel',
        limit_choices_to={'papel__in': ['advogado', 'administrador']},
        verbose_name='Responsável',
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_cliente_criadas',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tarefa de Cliente'
        verbose_name_plural = 'Tarefas de Cliente'
        ordering = ['status', 'prazo_em', '-criado_em']

    def __str__(self):
        return f'{self.titulo} - {self.cliente}'


class ClienteContrato(models.Model):
    TIPO_CHOICES = [
        ('contrato', 'Contrato'),
        ('procuracao', 'Procuração'),
    ]
    STATUS_ASSINATURA_CHOICES = [
        ('pendente', 'Pendente'),
        ('enviado', 'Enviado'),
        ('assinado', 'Assinado'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='contratos',
        verbose_name='Cliente',
    )
    tipo_documento = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo do Documento')
    titulo = models.CharField(max_length=180, verbose_name='Título')
    arquivo = models.FileField(upload_to='clientes/contratos/', blank=True, null=True, verbose_name='Arquivo')
    status_assinatura = models.CharField(
        max_length=20,
        choices=STATUS_ASSINATURA_CHOICES,
        default='pendente',
        verbose_name='Status da Assinatura',
    )
    assinatura_provedor = models.CharField(max_length=80, blank=True, null=True, verbose_name='Provedor de Assinatura')
    assinatura_envelope_id = models.CharField(max_length=120, blank=True, null=True, verbose_name='Envelope ID')
    assinatura_link = models.URLField(blank=True, null=True, verbose_name='Link de Assinatura')
    assinado_em = models.DateTimeField(blank=True, null=True, verbose_name='Assinado em')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contratos_cliente_criados',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contrato de Cliente'
        verbose_name_plural = 'Contratos de Cliente'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.titulo} - {self.cliente}'


class Processo(models.Model):
    STATUS_CHOICES = [
        ('em_andamento', 'Em Andamento'),
        ('suspenso', 'Suspenso'),
        ('finalizado', 'Finalizado'),
        ('arquivado', 'Arquivado'),
    ]
    TIPO_CASO_CHOICES = [
        ('contencioso', 'Contencioso'),
        ('consultivo', 'Consultivo'),
        ('massificado', 'Massificado'),
    ]
    ETAPA_WORKFLOW_CHOICES = [
        ('triagem', 'Triagem'),
        ('estrategia', 'Estratégia'),
        ('instrucao', 'Instrução'),
        ('negociacao', 'Negociação'),
        ('execucao', 'Execução'),
        ('monitoramento', 'Monitoramento'),
        ('encerramento', 'Encerramento'),
    ]
    STATUS_TRANSITIONS = {
        'em_andamento': {'suspenso', 'finalizado', 'arquivado'},
        'suspenso': {'em_andamento', 'finalizado', 'arquivado'},
        'finalizado': {'arquivado'},
        'arquivado': set(),
    }
    numero = models.CharField(max_length=30, unique=True, verbose_name='Número do Processo')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='processos', verbose_name='Cliente')
    advogado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processos',
        verbose_name='Advogado Responsável',
        limit_choices_to={'papel__in': ['advogado', 'administrador']},
    )
    tipo = models.ForeignKey(TipoProcesso, on_delete=models.SET_NULL, null=True, verbose_name='Tipo')
    vara = models.ForeignKey(Vara, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Vara')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento', verbose_name='Status')
    tipo_caso = models.CharField(
        max_length=20,
        choices=TIPO_CASO_CHOICES,
        default='contencioso',
        verbose_name='Tipo de Caso',
    )
    etapa_workflow = models.CharField(
        max_length=20,
        choices=ETAPA_WORKFLOW_CHOICES,
        default='triagem',
        verbose_name='Etapa do Workflow',
    )
    valor_causa = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Valor da Causa (R$)')
    objeto = models.TextField(verbose_name='Objeto / Descrição')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Processo'
        verbose_name_plural = 'Processos'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.numero} - {self.cliente}'

    def pode_transicionar(self, novo_status):
        if novo_status == self.status:
            return True
        return novo_status in self.STATUS_TRANSITIONS.get(self.status, set())

    def validar_transicao_status(self, novo_status):
        if not self.pode_transicionar(novo_status):
            raise ValidationError(
                f'Transição de status inválida: {self.status} -> {novo_status}.'
            )


class ProcessoParte(models.Model):
    TIPO_PARTE_CHOICES = [
        ('autor', 'Autor'),
        ('reu', 'Réu'),
        ('terceiro', 'Terceiro Interessado'),
        ('assistente', 'Assistente'),
        ('testemunha', 'Testemunha'),
        ('outro', 'Outro'),
    ]

    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='partes',
        verbose_name='Processo',
    )
    tipo_parte = models.CharField(max_length=20, choices=TIPO_PARTE_CHOICES, default='autor', verbose_name='Tipo da Parte')
    nome = models.CharField(max_length=220, verbose_name='Nome')
    documento = models.CharField(max_length=20, blank=True, null=True, verbose_name='CPF/CNPJ')
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Parte do Processo'
        verbose_name_plural = 'Partes do Processo'
        ordering = ['nome']

    def __str__(self):
        return f'{self.get_tipo_parte_display()} - {self.nome}'


class ProcessoResponsavel(models.Model):
    PAPEL_CHOICES = [
        ('principal', 'Principal'),
        ('apoio', 'Apoio'),
        ('estagiario', 'Estagiário'),
    ]

    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='responsaveis',
        verbose_name='Processo',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='responsabilidades_processo',
        limit_choices_to={'papel__in': ['advogado', 'administrador', 'estagiario']},
        verbose_name='Usuário',
    )
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default='apoio', verbose_name='Papel')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Responsável do Processo'
        verbose_name_plural = 'Responsáveis do Processo'
        ordering = ['-ativo', 'papel', '-criado_em']
        constraints = [
            models.UniqueConstraint(fields=['processo', 'usuario'], name='uniq_processo_usuario_responsavel'),
        ]

    def __str__(self):
        return f'{self.usuario} - {self.processo.numero}'


class ProcessoTarefa(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='tarefas',
        verbose_name='Processo',
    )
    titulo = models.CharField(max_length=220, verbose_name='Título')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name='Status')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media', verbose_name='Prioridade')
    prazo_em = models.DateTimeField(blank=True, null=True, verbose_name='Prazo')
    concluido_em = models.DateTimeField(blank=True, null=True, verbose_name='Concluído em')
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_processo_responsavel',
        limit_choices_to={'papel__in': ['advogado', 'administrador', 'estagiario']},
        verbose_name='Responsável',
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tarefas_processo_criadas',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tarefa de Processo'
        verbose_name_plural = 'Tarefas de Processo'
        ordering = ['status', 'prazo_em', '-criado_em']

    def __str__(self):
        return f'{self.titulo} - {self.processo.numero}'


class DocumentoTemplate(models.Model):
    TIPO_ALVO_CHOICES = [
        ('cliente', 'Cliente'),
        ('processo', 'Processo'),
    ]

    nome = models.CharField(max_length=150, verbose_name='Nome')
    tipo_alvo = models.CharField(max_length=20, choices=TIPO_ALVO_CHOICES, verbose_name='Tipo de Alvo')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    conteudo_base = models.TextField(blank=True, null=True, verbose_name='Conteúdo Base')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='templates_documento_criados',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Template de Documento'
        verbose_name_plural = 'Templates de Documento'
        ordering = ['tipo_alvo', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['tipo_alvo', 'nome'], name='uniq_template_documento_alvo_nome'),
        ]

    def __str__(self):
        return f'{self.get_tipo_alvo_display()} - {self.nome}'


class ProcessoArquivo(models.Model):
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='arquivos',
        verbose_name='Processo',
    )
    arquivo = models.FileField(upload_to='processos/arquivos/', verbose_name='Arquivo')
    nome_original = models.CharField(max_length=255, blank=True, verbose_name='Nome Original')
    titulo = models.CharField(max_length=220, blank=True, null=True, verbose_name='Título')
    documento_referencia = models.CharField(max_length=160, blank=True, null=True, verbose_name='Referência do Documento')
    versao = models.PositiveIntegerField(default=1, verbose_name='Versão')
    template = models.ForeignKey(
        DocumentoTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arquivos_processo',
        limit_choices_to={'tipo_alvo': 'processo'},
        verbose_name='Template',
    )
    template_nome = models.CharField(max_length=150, blank=True, null=True, verbose_name='Nome do Template')
    categoria = models.CharField(max_length=120, blank=True, null=True, verbose_name='Categoria')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arquivos_processo_enviados',
        verbose_name='Enviado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Arquivo do Processo'
        verbose_name_plural = 'Arquivos do Processo'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_original or self.arquivo.name


class ProcessoPeca(models.Model):
    TIPO_PECA_CHOICES = [
        ('defesa', 'Peça de Defesa'),
        ('recurso', 'Recurso'),
        ('peticao', 'Petição'),
        ('manifestacao', 'Manifestação'),
        ('outro', 'Outra Peça'),
    ]
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('em_revisao', 'Em Revisão'),
        ('finalizada', 'Finalizada'),
        ('protocolada', 'Protocolada'),
    ]

    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='pecas',
        verbose_name='Processo',
    )
    titulo = models.CharField(max_length=220, verbose_name='Título')
    tipo_peca = models.CharField(max_length=20, choices=TIPO_PECA_CHOICES, default='peticao', verbose_name='Tipo da Peça')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho', verbose_name='Status')
    conteudo = models.TextField(verbose_name='Conteúdo')
    versao = models.PositiveIntegerField(default=1, verbose_name='Versão')
    ia_score_qualidade = models.PositiveSmallIntegerField(default=0, verbose_name='Score IA de Qualidade')
    ia_revisao = models.JSONField(blank=True, null=True, verbose_name='Revisão IA')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pecas_processo_criadas',
        verbose_name='Criado por',
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pecas_processo_atualizadas',
        verbose_name='Atualizado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Peça do Processo'
        verbose_name_plural = 'Peças do Processo'
        ordering = ['-atualizado_em']

    def __str__(self):
        return f'{self.processo.numero} - {self.titulo} (v{self.versao})'


class ClienteArquivo(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='arquivos',
        verbose_name='Cliente',
    )
    arquivo = models.FileField(upload_to='clientes/arquivos/', verbose_name='Arquivo')
    nome_original = models.CharField(max_length=255, blank=True, verbose_name='Nome Original')
    titulo = models.CharField(max_length=220, blank=True, null=True, verbose_name='Título')
    documento_referencia = models.CharField(max_length=160, blank=True, null=True, verbose_name='Referência do Documento')
    versao = models.PositiveIntegerField(default=1, verbose_name='Versão')
    template = models.ForeignKey(
        DocumentoTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arquivos_cliente',
        limit_choices_to={'tipo_alvo': 'cliente'},
        verbose_name='Template',
    )
    template_nome = models.CharField(max_length=150, blank=True, null=True, verbose_name='Nome do Template')
    categoria = models.CharField(max_length=120, blank=True, null=True, verbose_name='Categoria')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arquivos_cliente_enviados',
        verbose_name='Enviado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Arquivo do Cliente'
        verbose_name_plural = 'Arquivos do Cliente'
        ordering = ['-criado_em']

    def __str__(self):
        return self.nome_original or self.arquivo.name


class Movimentacao(models.Model):
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name='movimentacoes', verbose_name='Processo')
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Autor',
    )
    data = models.DateField(verbose_name='Data')
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descricao = models.TextField(verbose_name='Descrição')
    documento = models.FileField(upload_to='movimentacoes/', blank=True, null=True, verbose_name='Documento Anexo')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        ordering = ['-data', '-criado_em']

    def __str__(self):
        return f'{self.data} - {self.titulo}'
