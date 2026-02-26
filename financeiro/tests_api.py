from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario
from processos.models import Cliente, Processo, TipoProcesso
from financeiro.models import Lancamento, ApontamentoTempo


class FinanceiroCobrancaApiTest(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(username='fin_admin', password='pass', papel='administrador')
        self.adv = Usuario.objects.create_user(username='fin_adv', password='pass', papel='advogado')
        self.tipo = TipoProcesso.objects.create(nome='Cível Financeiro')
        self.cliente = Cliente.objects.create(nome='Cliente Financeiro', tipo='pf', responsavel=self.adv)
        self.processo = Processo.objects.create(
            numero='9000000-00.2026.8.26.0001',
            cliente=self.cliente,
            advogado=self.adv,
            tipo=self.tipo,
            status='em_andamento',
            objeto='Processo financeiro teste',
        )

    def test_fluxo_time_tracking_regra_fatura_recebimento_online(self):
        self.client.force_authenticate(user=self.adv)

        response_regra = self.client.post(
            reverse('regra-cobranca-list'),
            {
                'cliente': self.cliente.pk,
                'processo': self.processo.pk,
                'titulo': 'Regra por Hora',
                'tipo_cobranca': 'hora',
                'valor_hora': '300.00',
            },
            format='json',
        )
        self.assertEqual(response_regra.status_code, status.HTTP_201_CREATED)
        regra_id = response_regra.data['id']

        response_ap = self.client.post(
            reverse('apontamento-tempo-list'),
            {
                'cliente': self.cliente.pk,
                'processo': self.processo.pk,
                'regra_cobranca': regra_id,
                'descricao': 'Elaboração de petição',
                'data': timezone.now().date().isoformat(),
                'minutos': 120,
            },
            format='json',
        )
        self.assertEqual(response_ap.status_code, status.HTTP_201_CREATED)

        response_despesa = self.client.post(
            reverse('lancamento-list'),
            {
                'cliente': self.cliente.pk,
                'processo': self.processo.pk,
                'tipo': 'pagar',
                'descricao': 'Custas processuais',
                'valor': '150.00',
                'data_vencimento': timezone.now().date().isoformat(),
                'data_pagamento': timezone.now().date().isoformat(),
                'status': 'pago',
                'reembolsavel_cliente': True,
            },
            format='json',
        )
        self.assertEqual(response_despesa.status_code, status.HTTP_201_CREATED)
        despesa_id = response_despesa.data['id']

        response_fatura = self.client.post(
            reverse('fatura-gerar'),
            {
                'cliente': self.cliente.pk,
                'processo': self.processo.pk,
                'regra_cobranca': regra_id,
                'periodo_inicio': timezone.now().date().replace(day=1).isoformat(),
                'periodo_fim': timezone.now().date().isoformat(),
                'data_vencimento': (timezone.now().date() + timedelta(days=5)).isoformat(),
                'incluir_despesas_reembolsaveis': True,
            },
            format='json',
        )
        self.assertEqual(response_fatura.status_code, status.HTTP_201_CREATED)
        self.assertGreater(float(response_fatura.data['total']), 0)
        fatura_id = response_fatura.data['id']

        response_enviar = self.client.post(reverse('fatura-enviar', args=[fatura_id]), {}, format='json')
        self.assertEqual(response_enviar.status_code, status.HTTP_200_OK)
        lancamento_receber_id = response_enviar.data['lancamento_receber_id']
        self.assertIsNotNone(lancamento_receber_id)

        response_link = self.client.post(
            reverse('fatura-gerar-link', args=[fatura_id]),
            {'gateway': 'manual'},
            format='json',
        )
        self.assertEqual(response_link.status_code, status.HTTP_200_OK)
        self.assertTrue(response_link.data.get('online_url'))

        response_pago = self.client.post(reverse('fatura-marcar-paga', args=[fatura_id]), {}, format='json')
        self.assertEqual(response_pago.status_code, status.HTTP_200_OK)
        self.assertEqual(response_pago.data['status'], 'paga')

        lancamento_receber = Lancamento.objects.get(pk=lancamento_receber_id)
        self.assertEqual(lancamento_receber.status, 'pago')

        apontamento = ApontamentoTempo.objects.get(pk=response_ap.data['id'])
        self.assertIsNotNone(apontamento.faturado_em)

        despesa = Lancamento.objects.get(pk=despesa_id)
        self.assertIsNotNone(despesa.faturado_em)
