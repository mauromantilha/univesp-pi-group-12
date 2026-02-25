from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, UsuarioAtividadeLog
from processos.models import Cliente, Comarca, Vara, TipoProcesso, Processo
from agenda.models import Compromisso
from jurisprudencia.models import Documento


class UsuarioModelTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_test', password='pass', papel='administrador',
            first_name='Admin', last_name='Test',
        )
        self.advogado = Usuario.objects.create_user(
            username='adv_test', password='pass', papel='advogado', oab='SP99999',
        )

    def test_papel_display(self):
        self.assertEqual(self.admin.get_papel_display(), 'Administrador')
        self.assertEqual(self.advogado.get_papel_display(), 'Advogado')

    def test_is_administrador(self):
        self.assertTrue(self.admin.is_administrador())
        self.assertFalse(self.advogado.is_administrador())

    def test_is_advogado(self):
        self.assertTrue(self.advogado.is_advogado())
        self.assertFalse(self.admin.is_advogado())


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(username='u1', password='pass123', papel='advogado')

    def test_login_page_accessible(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_valid(self):
        response = self.client.post(reverse('login'), {'username': 'u1', 'password': 'pass123'})
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid(self):
        response = self.client.post(reverse('login'), {'username': 'u1', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')


class DashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(username='adv1', password='pass', papel='advogado')
        self.client.login(username='adv1', password='pass')

    def test_dashboard_accessible(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)


class GestaoUsuariosViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(username='adm_gestao', password='pass', papel='administrador')
        self.advogado = Usuario.objects.create_user(username='adv_gestao', password='pass', papel='advogado')

    def test_admin_acessa_gestao_usuarios(self):
        self.client.login(username='adm_gestao', password='pass')
        response = self.client.get(reverse('gestao_usuarios'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestão Usuários')

    def test_advogado_nao_acessa_gestao_usuarios(self):
        self.client.login(username='adv_gestao', password='pass')
        response = self.client.get(reverse('gestao_usuarios'))
        self.assertRedirects(response, reverse('dashboard'))


class UsuarioAtividadeLogTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(username='adm_log', password='pass', papel='administrador')
        self.user = Usuario.objects.create_user(username='user_log', password='pass123', papel='advogado')

    def test_login_web_gera_log(self):
        self.client.post(reverse('login'), {'username': 'user_log', 'password': 'pass123'})
        self.assertTrue(
            UsuarioAtividadeLog.objects.filter(usuario=self.user, autor=self.user, acao='login_web').exists()
        )

    def test_acesso_gestao_usuarios_gera_log(self):
        self.client.login(username='adm_log', password='pass')
        self.client.get(reverse('gestao_usuarios'))
        self.assertTrue(
            UsuarioAtividadeLog.objects.filter(autor=self.admin, acao='gestao_usuarios').exists()
        )


class PortalUsuarioTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(username='admin_portal', password='pass', papel='administrador')
        self.adv1 = Usuario.objects.create_user(username='adv_portal_1', password='pass', papel='advogado')
        self.adv2 = Usuario.objects.create_user(username='adv_portal_2', password='pass', papel='advogado')

    def test_advogado_acessa_proprio_portal(self):
        self.client.login(username='adv_portal_1', password='pass')
        response = self.client.get(reverse('meu_portal'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Portal de')

    def test_advogado_nao_acessa_portal_de_outro(self):
        self.client.login(username='adv_portal_1', password='pass')
        response = self.client.get(reverse('portal_usuario', args=[self.adv2.pk]))
        self.assertRedirects(response, reverse('meu_portal'))

    def test_admin_acessa_portal_de_qualquer_advogado(self):
        self.client.login(username='admin_portal', password='pass')
        response = self.client.get(reverse('portal_usuario', args=[self.adv1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Portal de')


class ProcessoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(username='adm', password='pass', papel='administrador')
        self.advogado = Usuario.objects.create_user(username='adv', password='pass', papel='advogado')
        self.comarca = Comarca.objects.create(nome='São Paulo', estado='SP')
        self.vara = Vara.objects.create(nome='1ª Vara Cível', comarca=self.comarca)
        self.tipo = TipoProcesso.objects.create(nome='Civil')
        self.cliente = Cliente.objects.create(nome='Cliente Teste', tipo='pf')
        self.processo = Processo.objects.create(
            numero='9999999-99.2024.8.26.0100',
            cliente=self.cliente,
            advogado=self.advogado,
            tipo=self.tipo,
            vara=self.vara,
            status='em_andamento',
            objeto='Teste',
        )
        self.client.login(username='adv', password='pass')

    def test_lista_processos(self):
        response = self.client.get(reverse('lista_processos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '9999999-99.2024.8.26.0100')

    def test_detalhe_processo(self):
        response = self.client.get(reverse('detalhe_processo', args=[self.processo.pk]))
        self.assertEqual(response.status_code, 200)

    def test_lista_clientes(self):
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Teste')

    def test_novo_processo_form(self):
        response = self.client.get(reverse('novo_processo'))
        self.assertEqual(response.status_code, 200)

    def test_carga_trabalho(self):
        response = self.client.get(reverse('carga_trabalho'))
        self.assertEqual(response.status_code, 200)


class AgendaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(username='adv2', password='pass', papel='advogado')
        from django.utils import timezone
        self.compromisso = Compromisso.objects.create(
            titulo='Audiência Teste',
            tipo='audiencia',
            data=timezone.now().date(),
            advogado=self.user,
            status='pendente',
        )
        self.client.login(username='adv2', password='pass')

    def test_calendario_accessible(self):
        response = self.client.get(reverse('calendario'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Audiência Teste')

    def test_alertas_accessible(self):
        response = self.client.get(reverse('alertas'))
        self.assertEqual(response.status_code, 200)


class JurisprudenciaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(username='adv3', password='pass', papel='advogado')
        self.doc = Documento.objects.create(
            titulo='Decisão Trabalhista',
            categoria='acordao',
            conteudo='Reconhecimento de vínculo empregatício.',
            adicionado_por=self.user,
        )
        self.client.login(username='adv3', password='pass')

    def test_lista_documentos(self):
        response = self.client.get(reverse('lista_documentos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Decisão Trabalhista')

    def test_detalhe_documento(self):
        response = self.client.get(reverse('detalhe_documento', args=[self.doc.pk]))
        self.assertEqual(response.status_code, 200)

    def test_busca_documentos(self):
        response = self.client.get(reverse('lista_documentos') + '?q=trabalhista')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Decisão Trabalhista')


class IAPreditivaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.advogado = Usuario.objects.create_user(username='adv4', password='pass', papel='advogado')
        self.comarca = Comarca.objects.create(nome='Campinas', estado='SP')
        self.vara = Vara.objects.create(nome='1ª Vara', comarca=self.comarca)
        self.tipo = TipoProcesso.objects.create(nome='Previdenciário')
        self.cliente = Cliente.objects.create(nome='Cliente IA', tipo='pf')
        self.processo = Processo.objects.create(
            numero='0000001-01.2024.8.26.0100',
            cliente=self.cliente,
            advogado=self.advogado,
            tipo=self.tipo,
            vara=self.vara,
            status='em_andamento',
            objeto='Análise IA',
        )
        self.client.login(username='adv4', password='pass')

    def test_analise_risco(self):
        response = self.client.get(reverse('analise_risco', args=[self.processo.pk]))
        self.assertEqual(response.status_code, 200)

    def test_sugestoes_jurisprudencia(self):
        response = self.client.get(reverse('sugestoes_jurisprudencia') + '?q=previdenciário')
        self.assertEqual(response.status_code, 200)
