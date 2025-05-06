from django.db import models
from django.utils import timezone
from escolas.models import Escola
from produtos.models import Produto
from django.db import connection
from decimal import Decimal

class Pedido(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('pedido_enviado', 'Pedido Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    )
    
    escola = models.ForeignKey(
        Escola, 
        on_delete=models.CASCADE, 
        verbose_name="Escola",
        related_name="pedidos"
    )
    fornecedor = models.ForeignKey(
        'produtos.Fornecedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Fornecedor",
        related_name="pedidos"
    )
    data_solicitacao = models.DateTimeField("Data da Solicitação", default=timezone.now)
    data_aprovacao = models.DateTimeField("Data de Aprovação", blank=True, null=True)
    data_envio = models.DateTimeField("Data de Envio", blank=True, null=True)
    data_entrega = models.DateTimeField("Data de Entrega", blank=True, null=True)
    previsao_entrega_fornecedor = models.DateField("Previsão de Entrega (Fornecedor)", blank=True, null=True, help_text="Data prevista de entrega informada pelo fornecedor")
    recebido_por = models.CharField("Recebido por", max_length=100, blank=True, null=True)
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField("Observações", blank=True, null=True)
    justificativa_cancelamento = models.TextField("Justificativa de Cancelamento", blank=True, null=True)
    pedido_recorrente = models.BooleanField("Pedido Recorrente", default=False)
    pedido_original = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Pedido Original",
        related_name="pedidos_recorrentes"
    )
    
    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-data_solicitacao"]
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.escola.nome}"
    
    @property
    def valor_total(self):
        return sum(item.valor_total for item in self.itens.all())
    
    def atualizar_status(self, novo_status, data_entrega_manual=None, recebido_por=None):
        self.status = novo_status
        
        # Atualiza as datas conforme o status
        if novo_status == 'aprovado':
            self.data_aprovacao = timezone.now()
        elif novo_status == 'pedido_enviado':
            self.data_envio = timezone.now()
        elif novo_status == 'entregue':
            # Usar a data fornecida ou a data atual se não fornecida
            self.data_entrega = data_entrega_manual or timezone.now()
            # Armazenar quem recebeu o pedido
            if recebido_por:
                self.recebido_por = recebido_por
            
        self.save()

    def definir_recorrente(self, valor=True):
        """Define se o pedido é recorrente e salva diretamente no banco de dados"""
        # Definir o valor no objeto
        self.pedido_recorrente = bool(valor)
        
        # Se o pedido já tem um ID, atualizar diretamente no banco com SQL
        if self.id:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE pedidos_pedido SET pedido_recorrente=%s WHERE id=%s",
                    [valor, self.id]
                )
            # Verificar se realmente foi atualizado
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pedido_recorrente FROM pedidos_pedido WHERE id=%s",
                    [self.id]
                )
                resultado = cursor.fetchone()
                print(f"DEBUG: Verificação SQL - pedido_recorrente={resultado[0]}")
        # Se não tem ID, apenas salvar normalmente
        else:
            self.save()
        
        return self.pedido_recorrente

    def save(self, *args, **kwargs):
        # Log simples para debugging
        print(f"DEBUG: Salvando pedido ID={self.id if self.id else 'novo'}, pedido_recorrente={self.pedido_recorrente}")
        
        # Chamamos o método save padrão
        super().save(*args, **kwargs)

class ComprovanteEntrega(models.Model):
    """Modelo para armazenar os comprovantes de entrega dos pedidos"""
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        verbose_name="Pedido",
        related_name="comprovantes_entrega"
    )
    arquivo = models.FileField(
        upload_to='comprovantes_entrega/%Y/%m/',
        verbose_name="Arquivo do Comprovante",
        help_text="Anexar comprovante de entrega do pedido (PDF, imagem, etc.)"
    )
    descricao = models.CharField(
        "Descrição", 
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Descrição opcional do comprovante"
    )
    data_upload = models.DateTimeField(
        "Data de Upload", 
        auto_now_add=True
    )
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuário que enviou"
    )

    class Meta:
        verbose_name = "Comprovante de Entrega"
        verbose_name_plural = "Comprovantes de Entrega"
        ordering = ["-data_upload"]
    
    def __str__(self):
        return f"Comprovante #{self.id} - Pedido #{self.pedido.id}"
    
    @property
    def nome_arquivo(self):
        return self.arquivo.name.split('/')[-1]

class NotaFiscal(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        verbose_name="Pedido",
        related_name="notas_fiscais"
    )
    chave_nfe = models.CharField("Chave da NFe", max_length=44, unique=True)
    numero_nfe = models.CharField("Número da NFe", max_length=20)
    data_emissao = models.DateTimeField("Data de Emissão")
    data_importacao = models.DateTimeField("Data de Importação", auto_now_add=True)
    valor_total = models.DecimalField("Valor Total", max_digits=12, decimal_places=2)
    razao_social_emitente = models.CharField("Razão Social do Emitente", max_length=255)
    cnpj_emitente = models.CharField("CNPJ do Emitente", max_length=14)
    xml_completo = models.TextField("XML Completo", blank=True, null=True)
    # Campos adicionais
    natureza_operacao = models.CharField("Natureza da Operação", max_length=100, blank=True, null=True)
    serie = models.CharField("Série", max_length=10, blank=True, null=True)
    tipo_documento = models.CharField("Tipo de Documento", max_length=20, blank=True, null=True)
    data_saida = models.DateTimeField("Data de Saída/Entrega", blank=True, null=True)
    destinatario_nome = models.CharField("Nome do Destinatário", max_length=255, blank=True, null=True)
    destinatario_cnpj = models.CharField("CNPJ do Destinatário", max_length=14, blank=True, null=True)
    valor_produtos = models.DecimalField("Valor dos Produtos", max_digits=12, decimal_places=2, default=0)
    valor_frete = models.DecimalField("Valor do Frete", max_digits=12, decimal_places=2, default=0)
    valor_seguro = models.DecimalField("Valor do Seguro", max_digits=12, decimal_places=2, default=0)
    valor_desconto = models.DecimalField("Valor do Desconto", max_digits=12, decimal_places=2, default=0)
    valor_outras_despesas = models.DecimalField("Outras Despesas", max_digits=12, decimal_places=2, default=0)
    valor_impostos = models.DecimalField("Valor dos Impostos", max_digits=12, decimal_places=2, default=0)
    informacoes_complementares = models.TextField("Informações Complementares", blank=True, null=True)
    
    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ["-data_emissao"]
    
    def __str__(self):
        return f"NFe {self.numero_nfe} - Pedido #{self.pedido.id}"

class ItemNotaFiscal(models.Model):
    nota_fiscal = models.ForeignKey(
        NotaFiscal,
        on_delete=models.CASCADE,
        verbose_name="Nota Fiscal",
        related_name="itens"
    )
    numero_item = models.PositiveIntegerField("Número do Item")
    codigo_produto = models.CharField("Código do Produto", max_length=60)
    descricao = models.CharField("Descrição", max_length=255)
    ncm = models.CharField("NCM", max_length=8, blank=True, null=True)
    cfop = models.CharField("CFOP", max_length=4, blank=True, null=True)
    unidade = models.CharField("Unidade", max_length=6)
    quantidade = models.DecimalField("Quantidade", max_digits=12, decimal_places=4)
    valor_unitario = models.DecimalField("Valor Unitário", max_digits=12, decimal_places=4)
    valor_total = models.DecimalField("Valor Total", max_digits=12, decimal_places=2)
    valor_desconto = models.DecimalField("Valor Desconto", max_digits=12, decimal_places=2, default=0)
    num_pedido = models.CharField("Número do Pedido no Item", max_length=60, blank=True, null=True)
    # Campos para impostos
    icms = models.DecimalField("Alíquota ICMS (%)", max_digits=8, decimal_places=2, blank=True, null=True)
    ipi = models.DecimalField("Alíquota IPI (%)", max_digits=8, decimal_places=2, blank=True, null=True)
    
    class Meta:
        verbose_name = "Item da Nota Fiscal"
        verbose_name_plural = "Itens da Nota Fiscal"
        ordering = ["numero_item"]
    
    def __str__(self):
        return f"Item {self.numero_item} - {self.descricao}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE, 
        verbose_name="Pedido",
        related_name="itens"
    )
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.PROTECT, 
        verbose_name="Produto"
    )
    quantidade = models.PositiveIntegerField("Quantidade")
    valor_unitario = models.DecimalField("Valor Unitário (R$)", max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
        unique_together = ['pedido', 'produto']
    
    def __str__(self):
        return f"{self.quantidade} x {self.produto.nome}"
    
    @property
    def valor_total(self):
        return self.quantidade * self.valor_unitario
    
    def save(self, *args, **kwargs):
        # Atualiza o valor unitário baseado no valor atual do produto
        if not self.valor_unitario:
            self.valor_unitario = self.produto.valor_unitario
        super().save(*args, **kwargs)

class PedidoLog(models.Model):
    """Modelo para registrar o histórico de operações em pedidos"""
    ACAO_CHOICES = (
        ('criacao', 'Criação'),
        ('alteracao_status', 'Alteração de Status'),
        ('edicao', 'Edição de Dados'),
        ('exclusao', 'Exclusão'),
    )
    
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        verbose_name="Pedido",
        related_name="logs"
    )
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuário"
    )
    data_hora = models.DateTimeField("Data/Hora", auto_now_add=True)
    acao = models.CharField("Ação", max_length=20, choices=ACAO_CHOICES)
    status_anterior = models.CharField("Status Anterior", max_length=20, blank=True, null=True)
    status_novo = models.CharField("Novo Status", max_length=20, blank=True, null=True)
    descricao = models.TextField("Descrição", blank=True, null=True)
    
    class Meta:
        verbose_name = "Log de Pedido"
        verbose_name_plural = "Logs de Pedidos"
        ordering = ["-data_hora"]
    
    def __str__(self):
        return f"Log #{self.id} - Pedido #{self.pedido.id}"
