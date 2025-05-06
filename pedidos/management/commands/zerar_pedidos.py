from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os
import datetime
import shutil
from pedidos.models import Pedido, ItemPedido
import logging

class Command(BaseCommand):
    help = 'Zera todos os pedidos no sistema e reinicia a contagem a partir do número 1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a exclusão de todos os pedidos',
        )

    def handle(self, *args, **options):
        # Configura logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
        )
        logger = logging.getLogger(__name__)
        
        # Verifica se o usuário confirmou a operação
        if not options['confirmar']:
            self.stdout.write(
                self.style.WARNING('ATENÇÃO: Esta operação excluirá TODOS os pedidos do sistema!\n'
                                  'Para confirmar, execute o comando com a flag --confirmar')
            )
            return
        
        # Cria um backup do banco de dados antes de prosseguir
        self._fazer_backup_banco()
        
        try:
            # Conta o número de pedidos que serão excluídos
            num_pedidos = Pedido.objects.count()
            num_itens = ItemPedido.objects.count()
            
            # Exclui todos os itens de pedidos primeiro (para evitar problemas de integridade referencial)
            ItemPedido.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Excluídos {num_itens} itens de pedidos.'))
            
            # Exclui todos os pedidos
            Pedido.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Excluídos {num_pedidos} pedidos.'))
            
            # Reseta a sequência de IDs para começar do 1 novamente
            with connection.cursor() as cursor:
                if 'sqlite' in connection.vendor:
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name='pedidos_pedido';")
                    self.stdout.write(self.style.SUCCESS('Sequência de IDs dos pedidos resetada para SQLite.'))
                elif 'postgresql' in connection.vendor:
                    cursor.execute("ALTER SEQUENCE pedidos_pedido_id_seq RESTART WITH 1;")
                    self.stdout.write(self.style.SUCCESS('Sequência de IDs dos pedidos resetada para PostgreSQL.'))
                elif 'mysql' in connection.vendor:
                    cursor.execute("ALTER TABLE pedidos_pedido AUTO_INCREMENT = 1;")
                    self.stdout.write(self.style.SUCCESS('Sequência de IDs dos pedidos resetada para MySQL.'))
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Banco de dados {connection.vendor} não suportado para reset de sequência. '
                                         f'A sequência pode não ter sido resetada corretamente.')
                    )
            
            # Registra o log da operação
            logger.info(f'Todos os pedidos foram zerados. {num_pedidos} pedidos e {num_itens} itens de pedidos foram excluídos.')
            self.stdout.write(self.style.SUCCESS(f'Operação concluída com sucesso! O sistema agora começará a contar os pedidos a partir do número 1.'))
            
        except Exception as e:
            logger.error(f'Erro ao zerar pedidos: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Erro ao zerar pedidos: {str(e)}\n'
                               f'O backup do banco de dados foi criado em: {settings.BASE_DIR}')
            )
    
    def _fazer_backup_banco(self):
        """Cria um backup do banco de dados antes de zerar os pedidos"""
        db_name = settings.DATABASES['default']['NAME']
        
        if os.path.exists(db_name):
            # Cria o nome do arquivo de backup com data/hora
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{db_name}_backup_{timestamp}"
            
            # Copia o arquivo do banco para o backup
            shutil.copy2(db_name, backup_file)
            
            self.stdout.write(self.style.SUCCESS(f'Backup do banco de dados criado: {backup_file}'))
            return backup_file
        
        return None 