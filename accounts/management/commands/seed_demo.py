"""
Management command to seed the database with initial demo data.
Usage: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Usuario
from processos.models import Cliente, Comarca, Vara, TipoProcesso, Processo
from agenda.models import Compromisso
from jurisprudencia.models import Documento


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de demonstração'

    def handle(self, *args, **options):
        self.stdout.write('Criando dados de demonstração...')

        # Admin
        admin, _ = Usuario.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'email': 'admin@escritorio.com',
                'papel': 'administrador',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin.set_password('admin123')
        admin.save()

        # Advogados
        advogados_data = [
            ('adv1', 'Ana', 'Silva', 'SP12345'),
            ('adv2', 'Carlos', 'Oliveira', 'SP67890'),
            ('adv3', 'Mariana', 'Santos', 'RJ11111'),
            ('adv4', 'Pedro', 'Lima', 'MG22222'),
            ('adv5', 'Juliana', 'Costa', 'SP33333'),
        ]
        advogados = []
        for username, first, last, oab in advogados_data:
            u, _ = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@escritorio.com',
                    'papel': 'advogado',
                    'oab': oab,
                }
            )
            u.set_password('senha123')
            u.save()
            advogados.append(u)

        # Tipos de processo
        tipos_nomes = ['Civil', 'Trabalhista', 'Tributário', 'Criminal', 'Previdenciário']
        tipos = []
        for nome in tipos_nomes:
            t, _ = TipoProcesso.objects.get_or_create(nome=nome)
            tipos.append(t)

        # Comarcas e varas
        comarca_sp, _ = Comarca.objects.get_or_create(nome='São Paulo', estado='SP')
        comarca_rj, _ = Comarca.objects.get_or_create(nome='Rio de Janeiro', estado='RJ')
        vara1, _ = Vara.objects.get_or_create(nome='1ª Vara Cível', comarca=comarca_sp)
        vara2, _ = Vara.objects.get_or_create(nome='2ª Vara do Trabalho', comarca=comarca_sp)
        vara3, _ = Vara.objects.get_or_create(nome='1ª Vara Federal', comarca=comarca_rj)

        # Clientes
        clientes_data = [
            ('João Ferreira', 'pf', '123.456.789-00'),
            ('Maria Rodrigues', 'pf', '987.654.321-00'),
            ('Empresa ABC Ltda', 'pj', '12.345.678/0001-90'),
            ('Construtora XYZ S/A', 'pj', '98.765.432/0001-10'),
            ('Roberto Almeida', 'pf', '111.222.333-44'),
        ]
        clientes = []
        for nome, tipo, cpf_cnpj in clientes_data:
            c, _ = Cliente.objects.get_or_create(
                nome=nome,
                defaults={'tipo': tipo, 'cpf_cnpj': cpf_cnpj, 'telefone': '(11) 99999-0000'}
            )
            clientes.append(c)

        # Processos
        processos_data = [
            ('0001234-12.2024.8.26.0100', clientes[0], advogados[0], tipos[0], vara1, 'em_andamento'),
            ('0002345-23.2024.8.26.0100', clientes[1], advogados[1], tipos[1], vara2, 'em_andamento'),
            ('0003456-34.2023.8.26.0100', clientes[2], advogados[2], tipos[2], vara1, 'suspenso'),
            ('0004567-45.2023.8.26.0100', clientes[3], advogados[3], tipos[0], vara3, 'finalizado'),
            ('0005678-56.2024.8.26.0100', clientes[4], advogados[4], tipos[4], vara2, 'em_andamento'),
            ('0006789-67.2022.8.26.0100', clientes[0], advogados[0], tipos[0], vara1, 'finalizado'),
        ]
        processos = []
        for numero, cliente, adv, tipo, vara, status in processos_data:
            p, _ = Processo.objects.get_or_create(
                numero=numero,
                defaults={
                    'cliente': cliente,
                    'advogado': adv,
                    'tipo': tipo,
                    'vara': vara,
                    'status': status,
                    'objeto': f'Ação {tipo.nome} – {cliente.nome}',
                    'valor_causa': 50000.00,
                }
            )
            processos.append(p)

        # Compromissos
        hoje = timezone.now().date()
        from datetime import timedelta
        Compromisso.objects.get_or_create(
            titulo='Audiência de Instrução',
            defaults={
                'tipo': 'audiencia',
                'data': hoje + timedelta(days=3),
                'advogado': advogados[0],
                'processo': processos[0],
                'status': 'pendente',
            }
        )
        Compromisso.objects.get_or_create(
            titulo='Prazo para Recurso',
            defaults={
                'tipo': 'prazo',
                'data': hoje + timedelta(days=2),
                'advogado': advogados[1],
                'processo': processos[1],
                'status': 'pendente',
            }
        )
        Compromisso.objects.get_or_create(
            titulo='Reunião com Cliente',
            defaults={
                'tipo': 'reuniao',
                'data': hoje,
                'advogado': advogados[0],
                'status': 'pendente',
            }
        )

        # Jurisprudência
        Documento.objects.get_or_create(
            titulo='Súmula 331 TST – Terceirização',
            defaults={
                'categoria': 'jurisprudencia',
                'tribunal': 'TST',
                'conteudo': 'Contrato de prestação de serviços. Legalidade. A contratação de trabalhadores por empresa interposta é ilegal, formando-se o vínculo diretamente com o tomador dos serviços, salvo no caso de trabalho temporário.',
                'tags': 'trabalhista, terceirização, vínculo empregatício',
                'adicionado_por': admin,
            }
        )
        Documento.objects.get_or_create(
            titulo='Prescrição Intercorrente – Enunciado 390 TST',
            defaults={
                'categoria': 'tese',
                'tribunal': 'TST',
                'conteudo': 'Aplica-se a prescrição intercorrente ao processo do trabalho em consonância com súmula do TST.',
                'tags': 'trabalhista, prescrição',
                'adicionado_por': admin,
            }
        )

        self.stdout.write(self.style.SUCCESS('Dados de demonstração criados com sucesso!'))
        self.stdout.write(self.style.SUCCESS('Login admin: admin / admin123'))
        self.stdout.write(self.style.SUCCESS('Login advogado: adv1 / senha123'))
