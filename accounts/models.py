from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    PAPEL_CHOICES = [
        ('administrador', 'Administrador'),
        ('advogado', 'Advogado'),
        ('estagiario', 'Estagiário'),
    ]
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default='advogado', verbose_name='Papel')
    oab = models.CharField(max_length=20, blank=True, null=True, verbose_name='OAB')
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    foto = models.ImageField(upload_to='fotos_usuarios/', blank=True, null=True, verbose_name='Foto')

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
