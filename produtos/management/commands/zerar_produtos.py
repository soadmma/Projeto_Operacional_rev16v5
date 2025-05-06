from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os
import datetime
import shutil
from produtos.models import Produto, ProdutoLog
import logging

class Command(BaseCommand):
    help = 'Zera todos os produtos no sistema e reinicia a contagem a partir do número 1'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a exclusão de todos os produtos',
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
                self.style.WARNING('ATENÇÃO: Esta operação excluirá TODOS os produtos do sistema!\n'
                                  'Para confirmar, execute o comando com a flag --confirmar')
            )
            return
        
        # Cria um backup do banco de dados antes de prosseguir
        self._fazer_backup_banco()
        
        try:
            # Verifica se existem pedidos no sistema que podem ter referências a produtos
            try:
                from pedidos.models import ItemPedido
                pedidos_existentes = ItemPedido.objects.count() > 0
                if pedidos_existentes:
                    self.stdout.write(
                        self.style.WARNING('AVISO: Existem pedidos no sistema que podem estar referenciando produtos.\n'
                                         'Recomendamos executar o comando "zerar_pedidos" antes de zerar os produtos.')
                    )
                    if not self._confirmar_continuar():
                        return
            except:
                self.stdout.write(
                    self.style.WARNING('Não foi possível verificar a existência de pedidos. Continuando...')
                )
            
            # Conta o número de produtos e logs que serão excluídos
            num_produtos = Produto.objects.count()
            
            # Obtém o nome dos produtos antes da exclusão para os logs
            produtos_nomes = list(Produto.objects.values_list('nome', flat=True))
            
            # Registra o log de exclusão para cada produto antes de excluir
            for produto in Produto.objects.all():
                try:
                    ProdutoLog.objects.create(
                        produto=None,
                        nome_produto=produto.nome,
                        acao='EXCLUSAO',
                        detalhes=f"Produto excluído durante processo de limpeza total. Valor: R$ {produto.valor_unitario}, Código: {produto.codigo or '-'}",
                        usuario='Sistema',
                        ip='127.0.0.1'
                    )
                except:
                    pass
            
            # Exclui todos os produtos
            Produto.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Excluídos {num_produtos} produtos.'))
            
            # Reseta a sequência de IDs para começar do 1 novamente
            with connection.cursor() as cursor:
                if 'sqlite' in connection.vendor:
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name='produtos_produto';")
                    self.stdout.write(self.style.SUCCESS('Sequência de IDs dos produtos resetada para SQLite.'))
                elif 'postgresql' in connection.vendor:
                    cursor.execute("ALTER SEQUENCE produtos_produto_id_seq RESTART WITH 1;")
                    self.stdout.write(self.style.SUCCESS('Sequência de IDs dos produtos resetada para PostgreSQL.'))
                elif 'mysql' in connection.vendor:
                    cursor.execute("ALTER TABLE produtos_produto AUTO_INCREMENT = 1;")
                    self.stdout.write(self.style.SUCCESS('Sequência de IDs dos produtos resetada para MySQL.'))
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Banco de dados {connection.vendor} não suportado para reset de sequência. '
                                         f'A sequência pode não ter sido resetada corretamente.')
                    )
            
            # Registra o log da operação
            logger.info(f'Todos os produtos foram zerados. {num_produtos} produtos foram excluídos.')
            self.stdout.write(self.style.SUCCESS(f'Operação concluída com sucesso! O sistema agora começará a contar os produtos a partir do número 1.'))
            self.stdout.write(self.style.SUCCESS(f'Produtos excluídos: {", ".join(produtos_nomes[:20])}{" e outros..." if len(produtos_nomes) > 20 else ""}'))
            
        except Exception as e:
            logger.error(f'Erro ao zerar produtos: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Erro ao zerar produtos: {str(e)}\n'
                               f'O backup do banco de dados foi criado em: {settings.BASE_DIR}')
            )
    
    def _fazer_backup_banco(self):
        """Cria um backup do banco de dados antes de zerar os produtos"""
        db_name = settings.DATABASES['default']['NAME']
        
        if os.path.exists(db_name):
            # Cria o nome do arquivo de backup com data/hora
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{db_name}_backup_produtos_{timestamp}"
            
            # Copia o arquivo do banco para o backup
            shutil.copy2(db_name, backup_file)
            
            self.stdout.write(self.style.SUCCESS(f'Backup do banco de dados criado: {backup_file}'))
            return backup_file
        
        return None
        
    def _confirmar_continuar(self):
        """Solicita confirmação adicional para continuar com a operação"""
        self.stdout.write("Deseja continuar mesmo assim? (s/n): ", ending='')
        resposta = input().lower()
        return resposta in ('s', 'sim', 'y', 'yes') 