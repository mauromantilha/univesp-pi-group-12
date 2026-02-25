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
