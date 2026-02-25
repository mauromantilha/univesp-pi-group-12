from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import Usuario
from .models import Cliente, Processo, TipoProcesso


class ClienteSegurancaUploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.adv1 = Usuario.objects.create_user(username='adv_cli_1', password='pass', papel='advogado')
        self.adv2 = Usuario.objects.create_user(username='adv_cli_2', password='pass', papel='advogado')
        self.tipo_civel = TipoProcesso.objects.create(nome='Cível')

        self.cliente_adv1 = Cliente.objects.create(nome='Cliente Adv1', tipo='pf', responsavel=self.adv1)
        self.cliente_adv2 = Cliente.objects.create(nome='Cliente Adv2', tipo='pf', responsavel=self.adv2)
        self.cliente_compartilhado = Cliente.objects.create(
            nome='Cliente Compartilhado',
            tipo='pf',
            responsavel=self.adv2,
        )
        Processo.objects.create(
            numero='1000000-00.2026.8.26.0001',
            cliente=self.cliente_compartilhado,
            advogado=self.adv1,
            tipo=self.tipo_civel,
            status='em_andamento',
            objeto='Processo que garante acesso do adv1',
        )

    def test_lista_clientes_isolada_por_advogado(self):
        self.client.login(username='adv_cli_1', password='pass')
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Adv1')
        self.assertContains(response, 'Cliente Compartilhado')
        self.assertNotContains(response, 'Cliente Adv2')

    def test_detalhe_cliente_negado_quando_sem_relacao(self):
        self.client.login(username='adv_cli_1', password='pass')
        response = self.client.get(reverse('detalhe_cliente', args=[self.cliente_adv2.pk]))
        self.assertRedirects(response, reverse('lista_clientes'))

    def test_editar_cliente_nao_toma_responsavel_de_outro_advogado(self):
        self.client.login(username='adv_cli_1', password='pass')
        response = self.client.post(
            reverse('editar_cliente', args=[self.cliente_compartilhado.pk]),
            {
                'tipo': 'pf',
                'nome': 'Cliente Compartilhado Atualizado',
                'cpf_cnpj': '',
                'email': '',
                'telefone': '',
                'endereco': '',
                'demanda': 'Nova demanda',
                'processos_possiveis': [str(self.tipo_civel.pk)],
                'observacoes': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.cliente_compartilhado.refresh_from_db()
        self.assertEqual(self.cliente_compartilhado.responsavel_id, self.adv2.pk)

    def test_novo_cliente_com_upload_multiplo_documentos(self):
        self.client.login(username='adv_cli_1', password='pass')

        arquivo_1 = SimpleUploadedFile('doc1.txt', b'documento 1', content_type='text/plain')
        arquivo_2 = SimpleUploadedFile('doc2.txt', b'documento 2', content_type='text/plain')

        response = self.client.post(
            reverse('novo_cliente'),
            {
                'tipo': 'pf',
                'nome': 'Cliente Upload',
                'cpf_cnpj': '123',
                'email': 'upload@example.com',
                'telefone': '11999999999',
                'endereco': 'Rua 1',
                'demanda': 'Demanda de teste',
                'processos_possiveis': [str(self.tipo_civel.pk)],
                'observacoes': 'Obs',
                'documentos': [arquivo_1, arquivo_2],
            },
        )
        self.assertEqual(response.status_code, 302)

        cliente = Cliente.objects.get(nome='Cliente Upload')
        self.assertEqual(cliente.responsavel_id, self.adv1.pk)
        self.assertEqual(cliente.processos_possiveis.count(), 1)
        self.assertEqual(cliente.arquivos.count(), 2)
