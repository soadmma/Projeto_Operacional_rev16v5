from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from escolas.models import EscolaLog


class Command(BaseCommand):
    help = 'Limpa logs de escolas/contratos mais antigos que 60 dias'

    def handle(self, *args, **options):
        # Calcula a data limite (60 dias atrás)
        data_limite = timezone.now() - timedelta(days=60)
        
        # Conta quantos logs serão excluídos
        logs_antigos = EscolaLog.objects.filter(data_hora__lt=data_limite)
        quantidade = logs_antigos.count()
        
        # Exclui os logs antigos
        logs_antigos.delete()
        
        # Mensagem de resultado
        self.stdout.write(
            self.style.SUCCESS(f'Limpeza concluída! {quantidade} logs de escolas/contratos mais antigos que 60 dias foram removidos.')
        ) 