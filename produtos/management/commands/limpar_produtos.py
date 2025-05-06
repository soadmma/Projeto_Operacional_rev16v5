import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from produtos.models import Produto
from django.conf import settings

class Command(BaseCommand):
    help = 'Exclui todos os produtos cadastrados no sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a exclusão sem solicitar confirmação',
        )

    def handle(self, *args, **options):
        total_produtos = Produto.objects.count()
        
        if total_produtos == 0:
            self.stdout.write(self.style.WARNING('Não há produtos cadastrados para excluir.'))
            return
            
        # Solicitar confirmação do usuário
        if not options['force']:
            self.stdout.write(
                self.style.WARNING(f'Atenção! Esta operação excluirá todos os {total_produtos} produtos cadastrados no sistema.')
            )
            confirmacao = input('Deseja continuar? (sim/não): ')
            if confirmacao.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write(self.style.ERROR('Operação cancelada pelo usuário.'))
                return
        
        # Criar diretório de backup se não existir
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Realizar backup dos produtos antes de excluí-los
        self.stdout.write('Realizando backup dos produtos...')
        produtos_data = list(Produto.objects.values())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'produtos_backup_{timestamp}.json')
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(produtos_data, f, ensure_ascii=False, indent=4)
        
        # Excluir todos os produtos
        self.stdout.write('Excluindo produtos...')
        total_excluidos = Produto.objects.all().delete()[0]
        
        # Resetar a sequência de IDs
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval('produtos_produto_id_seq', 1, false);")
        
        self.stdout.write(
            self.style.SUCCESS(f'Operação concluída com sucesso! {total_excluidos} produtos foram excluídos.')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Backup salvo em: {backup_file}')
        ) 