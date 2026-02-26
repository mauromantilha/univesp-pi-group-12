from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from financeiro.models import Lancamento


class Command(BaseCommand):
    help = 'Marca como atrasados os lançamentos pendentes com vencimento inferior à data atual.'

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        atualizados = Lancamento.objects.filter(
            Q(status='pendente'),
            Q(data_vencimento__lt=hoje),
        ).update(status='atrasado')

        self.stdout.write(
            self.style.SUCCESS(f'Lançamentos atualizados para atrasado: {atualizados}')
        )
