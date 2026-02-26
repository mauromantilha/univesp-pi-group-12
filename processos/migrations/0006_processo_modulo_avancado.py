# Generated manually for processos advanced module updates
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('processos', '0005_cliente_pipeline_qualificacao_automacoes_contratos'),
    ]

    operations = [
        migrations.AddField(
            model_name='processo',
            name='etapa_workflow',
            field=models.CharField(
                choices=[
                    ('triagem', 'Triagem'),
                    ('estrategia', 'Estratégia'),
                    ('instrucao', 'Instrução'),
                    ('negociacao', 'Negociação'),
                    ('execucao', 'Execução'),
                    ('monitoramento', 'Monitoramento'),
                    ('encerramento', 'Encerramento'),
                ],
                default='triagem',
                max_length=20,
                verbose_name='Etapa do Workflow',
            ),
        ),
        migrations.AddField(
            model_name='processo',
            name='tipo_caso',
            field=models.CharField(
                choices=[
                    ('contencioso', 'Contencioso'),
                    ('consultivo', 'Consultivo'),
                    ('massificado', 'Massificado'),
                ],
                default='contencioso',
                max_length=20,
                verbose_name='Tipo de Caso',
            ),
        ),
        migrations.CreateModel(
            name='DocumentoTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150, verbose_name='Nome')),
                ('tipo_alvo', models.CharField(choices=[('cliente', 'Cliente'), ('processo', 'Processo')], max_length=20, verbose_name='Tipo de Alvo')),
                ('descricao', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('conteudo_base', models.TextField(blank=True, null=True, verbose_name='Conteúdo Base')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='templates_documento_criados', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
            ],
            options={
                'verbose_name': 'Template de Documento',
                'verbose_name_plural': 'Templates de Documento',
                'ordering': ['tipo_alvo', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='ProcessoParte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_parte', models.CharField(choices=[('autor', 'Autor'), ('reu', 'Réu'), ('terceiro', 'Terceiro Interessado'), ('assistente', 'Assistente'), ('testemunha', 'Testemunha'), ('outro', 'Outro')], default='autor', max_length=20, verbose_name='Tipo da Parte')),
                ('nome', models.CharField(max_length=220, verbose_name='Nome')),
                ('documento', models.CharField(blank=True, max_length=20, null=True, verbose_name='CPF/CNPJ')),
                ('observacoes', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('processo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='partes', to='processos.processo', verbose_name='Processo')),
            ],
            options={
                'verbose_name': 'Parte do Processo',
                'verbose_name_plural': 'Partes do Processo',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='ProcessoResponsavel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('papel', models.CharField(choices=[('principal', 'Principal'), ('apoio', 'Apoio'), ('estagiario', 'Estagiário')], default='apoio', max_length=20, verbose_name='Papel')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('processo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responsaveis', to='processos.processo', verbose_name='Processo')),
                ('usuario', models.ForeignKey(limit_choices_to={'papel__in': ['advogado', 'administrador', 'estagiario']}, on_delete=django.db.models.deletion.CASCADE, related_name='responsabilidades_processo', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Responsável do Processo',
                'verbose_name_plural': 'Responsáveis do Processo',
                'ordering': ['-ativo', 'papel', '-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='ProcessoTarefa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=220, verbose_name='Título')),
                ('descricao', models.TextField(blank=True, null=True, verbose_name='Descrição')),
                ('status', models.CharField(choices=[('pendente', 'Pendente'), ('em_andamento', 'Em Andamento'), ('concluida', 'Concluída'), ('cancelada', 'Cancelada')], default='pendente', max_length=20, verbose_name='Status')),
                ('prioridade', models.CharField(choices=[('baixa', 'Baixa'), ('media', 'Média'), ('alta', 'Alta'), ('urgente', 'Urgente')], default='media', max_length=20, verbose_name='Prioridade')),
                ('prazo_em', models.DateTimeField(blank=True, null=True, verbose_name='Prazo')),
                ('concluido_em', models.DateTimeField(blank=True, null=True, verbose_name='Concluído em')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tarefas_processo_criadas', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
                ('processo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tarefas', to='processos.processo', verbose_name='Processo')),
                ('responsavel', models.ForeignKey(blank=True, limit_choices_to={'papel__in': ['advogado', 'administrador', 'estagiario']}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tarefas_processo_responsavel', to=settings.AUTH_USER_MODEL, verbose_name='Responsável')),
            ],
            options={
                'verbose_name': 'Tarefa de Processo',
                'verbose_name_plural': 'Tarefas de Processo',
                'ordering': ['status', 'prazo_em', '-criado_em'],
            },
        ),
        migrations.AddField(
            model_name='processoarquivo',
            name='categoria',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='Categoria'),
        ),
        migrations.AddField(
            model_name='processoarquivo',
            name='descricao',
            field=models.TextField(blank=True, null=True, verbose_name='Descrição'),
        ),
        migrations.AddField(
            model_name='processoarquivo',
            name='documento_referencia',
            field=models.CharField(blank=True, max_length=160, null=True, verbose_name='Referência do Documento'),
        ),
        migrations.AddField(
            model_name='processoarquivo',
            name='template',
            field=models.ForeignKey(blank=True, limit_choices_to={'tipo_alvo': 'processo'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='arquivos_processo', to='processos.documentotemplate', verbose_name='Template'),
        ),
        migrations.AddField(
            model_name='processoarquivo',
            name='template_nome',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Nome do Template'),
        ),
        migrations.AddField(
            model_name='processoarquivo',
            name='titulo',
            field=models.CharField(blank=True, max_length=220, null=True, verbose_name='Título'),
        ),
        migrations.AddField(
            model_name='processoarquivo',
            name='versao',
            field=models.PositiveIntegerField(default=1, verbose_name='Versão'),
        ),
        migrations.AddField(
            model_name='clientearquivo',
            name='categoria',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='Categoria'),
        ),
        migrations.AddField(
            model_name='clientearquivo',
            name='descricao',
            field=models.TextField(blank=True, null=True, verbose_name='Descrição'),
        ),
        migrations.AddField(
            model_name='clientearquivo',
            name='documento_referencia',
            field=models.CharField(blank=True, max_length=160, null=True, verbose_name='Referência do Documento'),
        ),
        migrations.AddField(
            model_name='clientearquivo',
            name='template',
            field=models.ForeignKey(blank=True, limit_choices_to={'tipo_alvo': 'cliente'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='arquivos_cliente', to='processos.documentotemplate', verbose_name='Template'),
        ),
        migrations.AddField(
            model_name='clientearquivo',
            name='template_nome',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Nome do Template'),
        ),
        migrations.AddField(
            model_name='clientearquivo',
            name='titulo',
            field=models.CharField(blank=True, max_length=220, null=True, verbose_name='Título'),
        ),
        migrations.AddField(
            model_name='clientearquivo',
            name='versao',
            field=models.PositiveIntegerField(default=1, verbose_name='Versão'),
        ),
        migrations.AddConstraint(
            model_name='documentotemplate',
            constraint=models.UniqueConstraint(fields=('tipo_alvo', 'nome'), name='uniq_template_documento_alvo_nome'),
        ),
        migrations.AddConstraint(
            model_name='processoresponsavel',
            constraint=models.UniqueConstraint(fields=('processo', 'usuario'), name='uniq_processo_usuario_responsavel'),
        ),
    ]
