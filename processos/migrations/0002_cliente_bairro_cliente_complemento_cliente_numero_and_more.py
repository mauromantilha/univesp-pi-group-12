# Migration histórica mantida apenas para compatibilidade de grafo.
# Não aplicar alterações de schema legadas.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processos', '0004_cliente_ativo'),
    ]

    operations = []
