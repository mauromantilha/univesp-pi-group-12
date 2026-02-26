from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class Usuario(AbstractUser):
    PAPEL_CHOICES = [
        ('administrador', 'Administrador'),
        ('advogado', 'Advogado'),
        ('estagiario', 'Estagiário'),
        ('assistente', 'Assistente'),
    ]
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default='advogado', verbose_name='Papel')
    oab = models.CharField(max_length=20, blank=True, null=True, verbose_name='OAB')
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    foto = models.ImageField(upload_to='fotos_usuarios/', blank=True, null=True, verbose_name='Foto')
    responsavel_advogado = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipe',
        verbose_name='Advogado Responsável',
        limit_choices_to={'papel__in': ['advogado', 'administrador']},
    )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_papel_display()})'

    def is_administrador(self):
        return self.papel == 'administrador'

    def is_advogado(self):
        return self.papel == 'advogado'

    def is_estagiario(self):
        return self.papel == 'estagiario'

    def is_assistente(self):
        return self.papel == 'assistente'

    def is_colaborador_junior(self):
        return self.papel in {'estagiario', 'assistente'}

    def clean(self):
        super().clean()
        if self.is_colaborador_junior():
            if not self.responsavel_advogado_id:
                raise ValidationError({'responsavel_advogado': 'Estagiário/assistente deve possuir advogado responsável.'})
            if self.responsavel_advogado_id == self.id:
                raise ValidationError({'responsavel_advogado': 'Usuário não pode ser responsável por si próprio.'})
            if not (
                self.responsavel_advogado
                and self.responsavel_advogado.papel in {'advogado', 'administrador'}
            ):
                raise ValidationError({'responsavel_advogado': 'Responsável deve ser advogado ou administrador.'})
        elif self.responsavel_advogado_id:
            self.responsavel_advogado = None

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class UsuarioAtividadeLog(models.Model):
    ACAO_CHOICES = [
        ('login_web', 'Login Web'),
        ('login_api', 'Login API'),
        ('logout', 'Logout'),
        ('gestao_usuarios', 'Acesso à Gestão de Usuários'),
        ('usuario_criado', 'Usuário Criado'),
        ('usuario_editado', 'Usuário Editado'),
        ('perfil_atualizado', 'Perfil Atualizado'),
        ('acesso_portal', 'Acesso ao Portal'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atividades_recebidas',
        verbose_name='Usuário de Referência',
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atividades_executadas',
        verbose_name='Autor da Ação',
    )
    acao = models.CharField(max_length=40, choices=ACAO_CHOICES, verbose_name='Ação')
    detalhes = models.TextField(blank=True, verbose_name='Detalhes')
    rota = models.CharField(max_length=255, blank=True, verbose_name='Rota')
    ip_endereco = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')
    dados_extra = models.JSONField(blank=True, null=True, verbose_name='Dados Extras')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Atividade de Usuário'
        verbose_name_plural = 'Logs de Atividade de Usuários'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.get_acao_display()} - {self.criado_em:%d/%m/%Y %H:%M}'
