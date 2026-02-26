from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario
from processos.models import Cliente, Processo, TipoProcesso

from .models import Documento


class DocumentoApiIsolamentoTest(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='jur_admin',
            password='pass',
            papel='administrador',
        )
        self.adv1 = Usuario.objects.create_user(
            username='jur_adv_1',
            password='pass',
            papel='advogado',
        )
        self.adv2 = Usuario.objects.create_user(
            username='jur_adv_2',
            password='pass',
            papel='advogado',
        )
        tipo = TipoProcesso.objects.create(nome='Cível Jurisprudência')
        cliente_1 = Cliente.objects.create(nome='Cliente Jur 1', tipo='pf', responsavel=self.adv1)
        cliente_2 = Cliente.objects.create(nome='Cliente Jur 2', tipo='pf', responsavel=self.adv2)
        self.processo_1 = Processo.objects.create(
            numero='6000000-00.2026.8.26.0001',
            cliente=cliente_1,
            advogado=self.adv1,
            tipo=tipo,
            status='em_andamento',
            objeto='Processo jur 1',
        )
        self.processo_2 = Processo.objects.create(
            numero='6000000-00.2026.8.26.0002',
            cliente=cliente_2,
            advogado=self.adv2,
            tipo=tipo,
            status='em_andamento',
            objeto='Processo jur 2',
        )
        self.doc_adv1 = Documento.objects.create(
            titulo='Doc Adv 1',
            categoria='tese',
            conteudo='Conteúdo advogado 1',
            processo_referencia=self.processo_1,
            adicionado_por=self.adv1,
        )
        self.doc_adv2 = Documento.objects.create(
            titulo='Doc Adv 2',
            categoria='tese',
            conteudo='Conteúdo advogado 2',
            processo_referencia=self.processo_2,
            adicionado_por=self.adv2,
        )
        self.doc_sem_processo_adv2 = Documento.objects.create(
            titulo='Doc Sem Processo Adv 2',
            categoria='jurisprudencia',
            conteudo='Conteúdo sem processo advogado 2',
            adicionado_por=self.adv2,
        )

    def test_advogado_ve_apenas_seus_documentos_ou_de_processos_visiveis(self):
        self.client.force_authenticate(user=self.adv1)
        response = self.client.get(reverse('documento-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titulos = [item['titulo'] for item in response.data['results']]
        self.assertIn(self.doc_adv1.titulo, titulos)
        self.assertNotIn(self.doc_adv2.titulo, titulos)
        self.assertNotIn(self.doc_sem_processo_adv2.titulo, titulos)

    def test_admin_ve_todos_documentos(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('documento-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titulos = [item['titulo'] for item in response.data['results']]
        self.assertIn(self.doc_adv1.titulo, titulos)
        self.assertIn(self.doc_adv2.titulo, titulos)
        self.assertIn(self.doc_sem_processo_adv2.titulo, titulos)
