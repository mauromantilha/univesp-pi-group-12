from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario
from agenda.models import Compromisso
from financeiro.models import Lancamento
from processos.models import Cliente, Processo, TipoProcesso, Movimentacao


class IAPreditivaApiTest(APITestCase):
    def setUp(self):
        self.adv = Usuario.objects.create_user(username='ia_adv', password='pass', papel='advogado')
        self.adv2 = Usuario.objects.create_user(username='ia_adv2', password='pass', papel='advogado')
        self.tipo = TipoProcesso.objects.create(nome='Cível IA')

        self.cliente = Cliente.objects.create(nome='Cliente IA', tipo='pf', responsavel=self.adv, demanda='Cobrança indevida bancária')
        self.processo = Processo.objects.create(
            numero='9000000-00.2026.8.26.0001',
            cliente=self.cliente,
            advogado=self.adv,
            tipo=self.tipo,
            status='em_andamento',
            objeto='Ação de repetição de indébito por cobrança indevida',
        )

        cliente2 = Cliente.objects.create(nome='Cliente Similar', tipo='pf', responsavel=self.adv, demanda='Cobrança indevida')
        self.processo_similar = Processo.objects.create(
            numero='9000000-00.2026.8.26.0002',
            cliente=cliente2,
            advogado=self.adv,
            tipo=self.tipo,
            status='finalizado',
            objeto='Ação de cobrança indevida em contrato bancário',
        )
        Movimentacao.objects.create(
            processo=self.processo_similar,
            autor=self.adv,
            data=timezone.localdate(),
            titulo='Sentença',
            descricao='Pedido julgado procedente com provimento integral.',
        )

        Compromisso.objects.create(
            titulo='Prazo recursal',
            tipo='prazo',
            data=timezone.localdate() + timedelta(days=2),
            advogado=self.adv,
            processo=self.processo,
            status='pendente',
            alerta_dias_antes=1,
            alerta_horas_antes=0,
        )

        Lancamento.objects.create(
            cliente=self.cliente,
            processo=self.processo,
            tipo='pagar',
            descricao='Custas iniciais',
            valor=500,
            data_vencimento=timezone.localdate() + timedelta(days=1),
            status='pendente',
            criado_por=self.adv,
        )

        self.client.force_authenticate(self.adv)

    def test_analisar_processo_retorna_previsao(self):
        response = self.client.post('/api/v1/ia/analises/analisar/', {'processo_id': self.processo.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('probabilidade_sucesso', response.data)
        self.assertIn('nivel_risco', response.data)
        self.assertIn('similares_internos', response.data)
        self.assertTrue(isinstance(response.data.get('probabilidade_sucesso'), float))

    def test_fluxo_peca_revisao_e_monitoramento(self):
        redigir = self.client.post(
            '/api/v1/ia/analises/redigir-peca/',
            {
                'processo_id': self.processo.id,
                'tipo_peca': 'defesa',
                'objetivo': 'Impugnar pedido inicial',
                'tese_principal': 'Inexistência de débito',
                'pedidos': ['Improcedência total'],
            },
            format='json',
        )
        self.assertEqual(redigir.status_code, status.HTTP_200_OK)
        self.assertIn('texto', redigir.data)

        revisar = self.client.post(
            '/api/v1/ia/analises/revisar-peca/',
            {'tipo_peca': 'defesa', 'texto': redigir.data['texto']},
            format='json',
        )
        self.assertEqual(revisar.status_code, status.HTTP_200_OK)
        self.assertIn('score_qualidade', revisar.data)

        monitor = self.client.get('/api/v1/ia/analises/monitoramento/')
        self.assertEqual(monitor.status_code, status.HTTP_200_OK)
        self.assertIn('prazos', monitor.data)
        self.assertIn('financeiro', monitor.data)
        self.assertIn('sistema', monitor.data)
