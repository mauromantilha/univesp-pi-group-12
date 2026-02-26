# Generated manually for reminder controls in compromissos
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agenda', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='compromisso',
            name='alerta_dias_antes',
            field=models.PositiveSmallIntegerField(default=1, verbose_name='Dias de Antecedência do Alerta'),
        ),
        migrations.AddField(
            model_name='compromisso',
            name='alerta_horas_antes',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Horas de Antecedência do Alerta'),
        ),
    ]
