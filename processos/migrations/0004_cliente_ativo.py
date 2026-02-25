from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processos', '0003_cliente_demanda_cliente_processos_possiveis_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='ativo',
            field=models.BooleanField(default=True, verbose_name='Ativo'),
        ),
    ]
