from django.urls import reverse
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
