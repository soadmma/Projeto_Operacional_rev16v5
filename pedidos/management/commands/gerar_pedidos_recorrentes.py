from django.core.management.base import BaseCommand
from django.utils import timezone
from pedidos.models import Pedido, ItemPedido
from produtos.models import Fornecedor
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Gera pedidos recorrentes para fornecedores configurados com dia de recorrência'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a geração de pedidos mesmo se não for o dia configurado',
        )
        parser.add_argument(
            '--fornecedor-id',
            type=int,
            help='ID do fornecedor para gerar pedidos recorrentes específicos',
        )
        parser.add_argument(
            '--ignore-date',
            action='store_true',
            help='Ignora a verificação de data e processa todos os fornecedores configurados',
        )

    def handle(self, *args, **options):
        force = options['force']
        fornecedor_id = options['fornecedor_id']
        ignore_date = options['ignore_date']
        
        # Obtém o dia atual
        hoje = timezone.now()
        dia_atual = hoje.day
        
        self.stdout.write(f"Iniciando geração de pedidos recorrentes - Data atual: {hoje.strftime('%d/%m/%Y')}")
        
        # Busca fornecedores com pedidos recorrentes configurados
        query = Fornecedor.objects.filter(ativo=True).exclude(dia_pedido_recorrente__isnull=True)
        if fornecedor_id:
            query = query.filter(id=fornecedor_id)
        
        fornecedores = query.all()
        
        if not fornecedores:
            self.stdout.write(self.style.WARNING("Nenhum fornecedor com recorrência configurada encontrado."))
            return
        
        # Contador de pedidos gerados
        total_gerados = 0
        
        for fornecedor in fornecedores:
            if not (force or ignore_date) and fornecedor.dia_pedido_recorrente != dia_atual:
                self.stdout.write(f"Pulando fornecedor {fornecedor.razao_social} - Dia configurado: {fornecedor.dia_pedido_recorrente}, Dia atual: {dia_atual}")
                continue
                
            self.stdout.write(f"Processando fornecedor: {fornecedor.razao_social}")
            
            # Busca pedidos recorrentes deste fornecedor que ainda não foram replicados este mês
            pedidos_base = Pedido.objects.filter(
                fornecedor=fornecedor,
                pedido_recorrente=True,
                status='aprovado'
            )
            
            if not pedidos_base:
                self.stdout.write(self.style.WARNING(f"Nenhum pedido recorrente base encontrado para {fornecedor.razao_social}"))
                continue
            
            # Para cada pedido recorrente, verifica se já foi gerado este mês
            for pedido_base in pedidos_base:
                # Verifica se já existe um pedido recorrente gerado no mês atual
                primeiro_dia_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                ultimo_dia_mes = primeiro_dia_mes.replace(
                    month=primeiro_dia_mes.month + 1 if primeiro_dia_mes.month < 12 else 1,
                    year=primeiro_dia_mes.year if primeiro_dia_mes.month < 12 else primeiro_dia_mes.year + 1
                ) - timezone.timedelta(days=1)
                
                ja_gerado = Pedido.objects.filter(
                    pedido_original=pedido_base,
                    data_solicitacao__gte=primeiro_dia_mes,
                    data_solicitacao__lte=ultimo_dia_mes
                ).exists()
                
                if ja_gerado and not force:
                    self.stdout.write(f"Pedido #{pedido_base.id} já possui um pedido recorrente gerado neste mês.")
                    continue
                
                # Verificar se o pedido ainda está marcado como recorrente
                if not pedido_base.pedido_recorrente:
                    self.stdout.write(f"Pedido #{pedido_base.id} não está mais marcado como recorrente. Ignorando.")
                    continue
                
                # Criar uma cópia do pedido base com nova data
                try:
                    with transaction.atomic():
                        # Cria o novo pedido
                        novo_pedido = Pedido(
                            escola=pedido_base.escola,
                            fornecedor=fornecedor,
                            data_solicitacao=hoje,
                            data_aprovacao=hoje,  # Já aprova o pedido
                            observacoes=f"Pedido recorrente gerado automaticamente. Pedido original: #{pedido_base.id}",
                            status='aprovado',
                            pedido_recorrente=False,  # Não é mais recorrente, é uma instância
                            pedido_original=pedido_base
                        )
                        novo_pedido.save()
                        
                        # Copia os itens do pedido original
                        for item_original in pedido_base.itens.all():
                            ItemPedido.objects.create(
                                pedido=novo_pedido,
                                produto=item_original.produto,
                                quantidade=item_original.quantidade,
                                valor_unitario=item_original.produto.valor_unitario  # Usa o valor atual do produto
                            )
                        
                        total_gerados += 1
                        self.stdout.write(self.style.SUCCESS(f"Pedido recorrente #{novo_pedido.id} gerado com sucesso baseado no pedido #{pedido_base.id}"))
                        
                except Exception as e:
                    logger.error(f"Erro ao gerar pedido recorrente para o pedido #{pedido_base.id}: {str(e)}")
                    self.stdout.write(self.style.ERROR(f"Erro ao gerar pedido recorrente: {str(e)}"))
        
        # Mensagem final
        if total_gerados > 0:
            self.stdout.write(self.style.SUCCESS(f"Geração concluída. {total_gerados} pedidos recorrentes gerados com sucesso."))
        else:
            self.stdout.write(self.style.WARNING("Nenhum pedido recorrente foi gerado.")) 