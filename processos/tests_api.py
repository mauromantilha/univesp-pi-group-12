from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario
from processos.models import Cliente, Processo, TipoProcesso


class ProcessosApiPermissoesTest(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='api_admin',
            password='pass',
            papel='administrador',
        )
        self.adv1 = Usuario.objects.create_user(
            username='api_adv_1',
            password='pass',
            papel='advogado',
        )
        self.adv2 = Usuario.objects.create_user(
            username='api_adv_2',
            password='pass',
            papel='advogado',
        )
        self.estagiario_adv1 = Usuario.objects.create_user(
            username='api_estagiario_1',
            password='pass',
            papel='estagiario',
            responsavel_advogado=self.adv1,
        )
        self.estagiario_adv2 = Usuario.objects.create_user(
            username='api_estagiario_2',
            password='pass',
            papel='estagiario',
            responsavel_advogado=self.adv2,
        )
        self.tipo = TipoProcesso.objects.create(nome='Cível API')

        self.cliente_adv1 = Cliente.objects.create(
            nome='Cliente API Adv1',
            tipo='pf',
            responsavel=self.adv1,
        )
        self.cliente_adv2 = Cliente.objects.create(
            nome='Cliente API Adv2',
            tipo='pf',
            responsavel=self.adv2,
        )
        self.cliente_compartilhado = Cliente.objects.create(
            nome='Cliente API Compartilhado',
            tipo='pf',
            responsavel=self.adv2,
        )
        self.processo_adv1 = Processo.objects.create(
            numero='3000000-00.2026.8.26.0001',
            cliente=self.cliente_adv1,
            advogado=self.adv1,
            tipo=self.tipo,
            status='em_andamento',
            objeto='Processo API adv1',
        )
        self.processo_compartilhado = Processo.objects.create(
            numero='3000000-00.2026.8.26.0002',
            cliente=self.cliente_compartilhado,
            advogado=self.adv1,
            tipo=self.tipo,
            status='em_andamento',
            objeto='Processo API compartilhado',
        )

    def test_advogado_lista_clientes_com_escopo_correto(self):
        self.client.force_authenticate(user=self.adv1)
        response = self.client.get(reverse('cliente-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nomes = [item['nome'] for item in response.data['results']]
        self.assertIn('Cliente API Adv1', nomes)
        self.assertIn('Cliente API Compartilhado', nomes)
        self.assertNotIn('Cliente API Adv2', nomes)

    def test_advogado_nao_cria_processo_para_cliente_sem_acesso(self):
        self.client.force_authenticate(user=self.adv1)
        response = self.client.post(
            reverse('processo-list'),
            {
                'numero': '3000000-00.2026.8.26.0010',
                'cliente': self.cliente_adv2.pk,
                'advogado': self.adv1.pk,
                'tipo': self.tipo.pk,
                'vara': None,
                'status': 'em_andamento',
                'objeto': 'Tentativa sem acesso',
                'valor_causa': None,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_advogado_cria_processo_e_sistema_forca_advogado_logado(self):
        self.client.force_authenticate(user=self.adv1)
        response = self.client.post(
            reverse('processo-list'),
            {
                'numero': '3000000-00.2026.8.26.0011',
                'cliente': self.cliente_adv1.pk,
                'advogado': self.adv2.pk,
                'tipo': self.tipo.pk,
                'vara': None,
                'status': 'em_andamento',
                'objeto': 'Criação com advogado forçado',
                'valor_causa': None,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        processo = Processo.objects.get(numero='3000000-00.2026.8.26.0011')
        self.assertEqual(processo.advogado_id, self.adv1.pk)

    def test_advogado_nao_edita_processo_de_outro_advogado(self):
        processo_adv2 = Processo.objects.create(
            numero='3000000-00.2026.8.26.0012',
            cliente=self.cliente_adv2,
            advogado=self.adv2,
            tipo=self.tipo,
            status='em_andamento',
            objeto='Processo de outro advogado',
        )
        self.client.force_authenticate(user=self.adv1)
        response = self.client.patch(
            reverse('processo-detail', args=[processo_adv2.pk]),
            {'objeto': 'Alteração indevida'},
            format='json',
        )
        # queryset do viewset já filtra por advogado, então retorna 404.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edicao_cliente_compartilhado_nao_troca_responsavel_original(self):
        self.client.force_authenticate(user=self.adv1)
        response = self.client.patch(
            reverse('cliente-detail', args=[self.cliente_compartilhado.pk]),
            {'demanda': 'Atualização por advogado do processo'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cliente_compartilhado.refresh_from_db()
        self.assertEqual(self.cliente_compartilhado.responsavel_id, self.adv2.pk)

    def test_inativar_cliente_disponivel_para_advogado(self):
        self.client.force_authenticate(user=self.adv1)
        response = self.client.post(reverse('cliente-inativar', args=[self.cliente_adv1.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cliente_adv1.refresh_from_db()
        self.assertFalse(self.cliente_adv1.ativo)

    def test_alteracao_status_processo_por_acoes_dedicadas(self):
        self.client.force_authenticate(user=self.adv1)

        response_inativar = self.client.post(reverse('processo-inativar', args=[self.processo_adv1.pk]))
        self.assertEqual(response_inativar.status_code, status.HTTP_200_OK)
        self.processo_adv1.refresh_from_db()
        self.assertEqual(self.processo_adv1.status, 'suspenso')

        response_concluir = self.client.post(reverse('processo-concluir', args=[self.processo_adv1.pk]))
        self.assertEqual(response_concluir.status_code, status.HTTP_200_OK)
        self.processo_adv1.refresh_from_db()
        self.assertEqual(self.processo_adv1.status, 'finalizado')

        response_arquivar = self.client.post(reverse('processo-arquivar', args=[self.processo_adv1.pk]))
        self.assertEqual(response_arquivar.status_code, status.HTTP_200_OK)
        self.processo_adv1.refresh_from_db()
        self.assertEqual(self.processo_adv1.status, 'arquivado')

    def test_listagem_processos_com_filtro_cliente_e_status(self):
        self.client.force_authenticate(user=self.adv1)
        self.client.post(reverse('processo-inativar', args=[self.processo_compartilhado.pk]))

        response = self.client.get(
            reverse('processo-list'),
            {'cliente': self.cliente_compartilhado.pk, 'status': 'suspenso'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resultados = response.data['results']
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]['id'], self.processo_compartilhado.pk)

    def test_fluxo_pipeline_qualificacao_conflito_cliente(self):
        self.client.force_authenticate(user=self.adv1)

        response_pipeline = self.client.patch(
            reverse('cliente-pipeline', args=[self.cliente_adv1.pk]),
            {
                'lead_origem': 'Instagram',
                'lead_campanha': 'Campanha Março',
                'lead_etapa': 'qualificacao',
                'lead_responsavel': self.adv1.pk,
            },
            format='json',
        )
        self.assertEqual(response_pipeline.status_code, status.HTTP_200_OK)

        response_qualificacao = self.client.patch(
            reverse('cliente-qualificacao', args=[self.cliente_adv1.pk]),
            {
                'qualificacao_status': 'qualificado',
                'qualificacao_score': 82,
                'formulario_qualificacao': {'urgencia': 'alta', 'orcamento': 'medio'},
            },
            format='json',
        )
        self.assertEqual(response_qualificacao.status_code, status.HTTP_200_OK)

        response_conflito = self.client.patch(
            reverse('cliente-conflito-interesses', args=[self.cliente_adv1.pk]),
            {
                'conflito_interesses_status': 'aprovado',
                'conflito_interesses_observacoes': 'Sem impedimentos.',
            },
            format='json',
        )
        self.assertEqual(response_conflito.status_code, status.HTTP_200_OK)

        self.cliente_adv1.refresh_from_db()
        self.assertEqual(self.cliente_adv1.lead_etapa, 'qualificacao')
        self.assertEqual(self.cliente_adv1.qualificacao_status, 'qualificado')
        self.assertEqual(self.cliente_adv1.qualificacao_score, 82)
        self.assertEqual(self.cliente_adv1.conflito_interesses_status, 'aprovado')

    def test_fluxo_automacao_tarefa_contrato_cliente(self):
        self.client.force_authenticate(user=self.adv1)

        response_automacao = self.client.post(
            reverse('cliente-automacoes', args=[self.cliente_adv1.pk]),
            {
                'canal': 'email',
                'tipo': 'followup',
                'status': 'agendado',
                'mensagem': 'Retornar proposta',
            },
            format='json',
        )
        self.assertEqual(response_automacao.status_code, status.HTTP_201_CREATED)

        response_tarefa = self.client.post(
            reverse('cliente-tarefas', args=[self.cliente_adv1.pk]),
            {
                'titulo': 'Ligar para cliente',
                'descricao': 'Validar documentos',
                'status': 'pendente',
                'prioridade': 'alta',
                'responsavel': self.adv1.pk,
            },
            format='json',
        )
        self.assertEqual(response_tarefa.status_code, status.HTTP_201_CREATED)
        tarefa_id = response_tarefa.data['id']

        response_concluir = self.client.post(
            reverse('cliente-concluir-tarefa', args=[self.cliente_adv1.pk, tarefa_id]),
            {},
            format='json',
        )
        self.assertEqual(response_concluir.status_code, status.HTTP_200_OK)
        self.assertEqual(response_concluir.data['status'], 'concluida')

        response_contrato = self.client.post(
            reverse('cliente-contratos', args=[self.cliente_adv1.pk]),
            {
                'tipo_documento': 'contrato',
                'titulo': 'Contrato de Honorários',
                'assinatura_provedor': 'interno',
            },
            format='json',
        )
        self.assertEqual(response_contrato.status_code, status.HTTP_201_CREATED)
        contrato_id = response_contrato.data['id']

        response_enviar = self.client.post(
            reverse('cliente-enviar-assinatura', args=[self.cliente_adv1.pk, contrato_id]),
            {'assinatura_link': 'https://assinatura.exemplo/abc'},
            format='json',
        )
        self.assertEqual(response_enviar.status_code, status.HTTP_200_OK)
        self.assertEqual(response_enviar.data['status_assinatura'], 'enviado')

        response_assinado = self.client.post(
            reverse('cliente-marcar-assinado', args=[self.cliente_adv1.pk, contrato_id]),
            {},
            format='json',
        )
        self.assertEqual(response_assinado.status_code, status.HTTP_200_OK)
        self.assertEqual(response_assinado.data['status_assinatura'], 'assinado')

    def test_fluxo_processo_workflow_partes_tarefas_prazos_responsaveis(self):
        self.client.force_authenticate(user=self.adv1)

        response_workflow = self.client.patch(
            reverse('processo-workflow', args=[self.processo_adv1.pk]),
            {'tipo_caso': 'consultivo', 'etapa_workflow': 'negociacao'},
            format='json',
        )
        self.assertEqual(response_workflow.status_code, status.HTTP_200_OK)
        self.assertEqual(response_workflow.data['tipo_caso'], 'consultivo')

        response_parte = self.client.post(
            reverse('processo-partes', args=[self.processo_adv1.pk]),
            {'tipo_parte': 'reu', 'nome': 'Empresa Ré Teste', 'documento': '11.111.111/0001-11'},
            format='json',
        )
        self.assertEqual(response_parte.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.admin)
        response_responsavel = self.client.post(
            reverse('processo-responsaveis', args=[self.processo_adv1.pk]),
            {'usuario': self.adv2.pk, 'papel': 'apoio'},
            format='json',
        )
        self.assertIn(response_responsavel.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        self.client.force_authenticate(user=self.adv1)

        response_tarefa = self.client.post(
            reverse('processo-tarefas', args=[self.processo_adv1.pk]),
            {
                'titulo': 'Revisar contrato',
                'descricao': 'Analisar cláusulas críticas',
                'prioridade': 'alta',
                'responsavel': self.adv2.pk,
            },
            format='json',
        )
        self.assertEqual(response_tarefa.status_code, status.HTTP_201_CREATED)
        tarefa_id = response_tarefa.data['id']

        response_prazo = self.client.post(
            reverse('processo-prazos', args=[self.processo_adv1.pk]),
            {
                'titulo': 'Prazo de manifestação',
                'data': '2026-03-10',
                'hora': '14:30:00',
                'descricao': 'Manifestação final',
                'alerta_dias_antes': 2,
                'alerta_horas_antes': 6,
            },
            format='json',
        )
        self.assertEqual(response_prazo.status_code, status.HTTP_201_CREATED)
        prazo_id = response_prazo.data['id']
        self.assertEqual(response_prazo.data['alerta_dias_antes'], 2)
        self.assertEqual(response_prazo.data['alerta_horas_antes'], 6)

        response_concluir_tarefa = self.client.post(
            reverse('processo-concluir-tarefa', args=[self.processo_adv1.pk, tarefa_id]),
            {},
            format='json',
        )
        self.assertEqual(response_concluir_tarefa.status_code, status.HTTP_200_OK)
        self.assertEqual(response_concluir_tarefa.data['status'], 'concluida')

        response_concluir_prazo = self.client.post(
            reverse('processo-concluir-prazo', args=[self.processo_adv1.pk, prazo_id]),
            {},
            format='json',
        )
        self.assertEqual(response_concluir_prazo.status_code, status.HTTP_200_OK)
        self.assertEqual(response_concluir_prazo.data['status'], 'concluido')

        self.client.force_authenticate(user=self.adv2)
        response_lista_processos_adv2 = self.client.get(reverse('processo-list'))
        self.assertEqual(response_lista_processos_adv2.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response_lista_processos_adv2.data['results']]
        self.assertIn(self.processo_adv1.pk, ids)

    def test_apenas_admin_gerencia_time_processo(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            reverse('processo-responsaveis', args=[self.processo_adv1.pk]),
            {'usuario': self.adv2.pk, 'papel': 'apoio'},
            format='json',
        )

        self.client.force_authenticate(user=self.adv2)
        response = self.client.post(
            reverse('processo-responsaveis', args=[self.processo_adv1.pk]),
            {'usuario': self.admin.pk, 'papel': 'apoio'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.adv1)
        response_adv1 = self.client.post(
            reverse('processo-responsaveis', args=[self.processo_adv1.pk]),
            {'usuario': self.adv2.pk, 'papel': 'apoio'},
            format='json',
        )
        self.assertEqual(response_adv1.status_code, status.HTTP_403_FORBIDDEN)

    def test_rbac_equipe_bloqueia_estagiario_de_outro_advogado_em_sigilo(self):
        self.processo_adv1.segredo_justica = True
        self.processo_adv1.save(update_fields=['segredo_justica'])

        self.client.force_authenticate(user=self.admin)
        response_bloqueado = self.client.post(
            reverse('processo-responsaveis', args=[self.processo_adv1.pk]),
            {'usuario': self.estagiario_adv2.pk, 'papel': 'estagiario'},
            format='json',
        )
        self.assertEqual(response_bloqueado.status_code, status.HTTP_400_BAD_REQUEST)

        response_ok = self.client.post(
            reverse('processo-responsaveis', args=[self.processo_adv1.pk]),
            {'usuario': self.estagiario_adv1.pk, 'papel': 'estagiario'},
            format='json',
        )
        self.assertEqual(response_ok.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.estagiario_adv1)
        response_lista = self.client.get(reverse('processo-list'))
        self.assertEqual(response_lista.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response_lista.data['results']]
        self.assertIn(self.processo_adv1.pk, ids)

    def test_upload_documentos_cliente_com_versionamento_e_busca(self):
        self.client.force_authenticate(user=self.admin)
        response_template = self.client.post(
            reverse('cliente-documentos-templates'),
            {
                'nome': 'Procuração PF',
                'descricao': 'Template base de procuração pessoa física',
                'conteudo_base': 'Conteúdo base',
            },
            format='json',
        )
        self.assertEqual(response_template.status_code, status.HTTP_201_CREATED)
        template_id = response_template.data['id']

        self.client.force_authenticate(user=self.adv1)
        url_upload = reverse('cliente-arquivos', args=[self.cliente_adv1.pk])
        arquivo_1 = SimpleUploadedFile('procuracao.pdf', b'PDF-v1', content_type='application/pdf')
        response_upload_1 = self.client.post(
            url_upload,
            {
                'arquivo': arquivo_1,
                'template': template_id,
                'documento_referencia': 'procuracao_cliente',
                'categoria': 'mandato',
            },
            format='multipart',
        )
        self.assertEqual(response_upload_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_upload_1.data[0]['versao'], 1)

        arquivo_2 = SimpleUploadedFile('procuracao.pdf', b'PDF-v2', content_type='application/pdf')
        response_upload_2 = self.client.post(
            url_upload,
            {
                'arquivo': arquivo_2,
                'template': template_id,
                'documento_referencia': 'procuracao_cliente',
                'categoria': 'mandato',
            },
            format='multipart',
        )
        self.assertEqual(response_upload_2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_upload_2.data[0]['versao'], 2)

        response_busca = self.client.get(url_upload, {'q': 'procuracao_cliente'})
        self.assertEqual(response_busca.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_busca.data), 2)
