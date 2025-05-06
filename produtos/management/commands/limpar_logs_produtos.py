from django.core.management.base import BaseCommand
from produtos.models import ProdutoLog
from django.utils import timezone
from datetime import timedelta
import logging

class Command(BaseCommand):
    help = 'Limpa logs de produtos com mais de 3 meses de idade'

    def handle(self, *args, **options):
        # Configura logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
        )
        logger = logging.getLogger(__name__)
        
        # Calcula a data de corte (3 meses atrás)
        data_corte = timezone.now() - timedelta(days=90)
        
        # Busca e conta os logs antigos
        logs_antigos = ProdutoLog.objects.filter(data_hora__lt=data_corte)
        count_logs = logs_antigos.count()
        
        if count_logs > 0:
            # Exclui os logs
            logs_antigos.delete()
            msg = f'Limpeza concluída: {count_logs} logs de produtos com mais de 3 meses foram excluídos.'
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        else:
            msg = 'Nenhum log de produto com mais de 3 meses encontrado para exclusão.'
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg)) 