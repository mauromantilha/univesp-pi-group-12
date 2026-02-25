from django.core.management.base import BaseCommand
from consulta_tribunais.models import Tribunal


class Command(BaseCommand):
    help = 'Popula banco com tribunais disponíveis para consulta'
    
    def handle(self, *args, **options):
        # TRT 2ª Região (São Paulo)
        trt2, created = Tribunal.objects.update_or_create(
            sigla='TRT2',
            defaults={
                'nome': 'Tribunal Regional do Trabalho da 2ª Região',
                'tipo': 'trabalho',
                'regiao': 'São Paulo',
                'api_endpoint': 'https://api-publica.datajud.cnj.jus.br/api_publica_trt2/_search',
                'api_key': 'cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==',
                'ativo': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ {trt2.sigla} criado'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ {trt2.sigla} atualizado'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Tribunais configurados com sucesso!'))
        self.stdout.write(f'\nTotal de tribunais ativos: {Tribunal.objects.filter(ativo=True).count()}')
