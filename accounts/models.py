from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    PAPEL_CHOICES = [
        ('administrador', 'Administrador'),
        ('advogado', 'Advogado'),
        ('estagiario', 'Estagiário'),
    ]
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default='advogado')
    oab = models.CharField(max_length=20, blank=True, null=True, verbose_name='Número OAB')
    telefone = models.CharField(max_length=20, blank=True, null=True)
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_papel_display()})'

    @property
    def nome_completo(self):
        return self.get_full_name() or self.username
