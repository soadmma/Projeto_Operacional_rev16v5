from django.db import models

# Create your models here.

class Fornecedor(models.Model):
    TIPO_CHOICES = (
        ('FIXO', 'Fixo'),
        ('ESPORADICO', 'Esporádico'),
    )
    nome = models.CharField("Nome Fantasia", max_length=100)
    razao_social = models.CharField("Razão Social", max_length=200, null=True, blank=True)
    cnpj = models.CharField("CNPJ/CPF", max_length=18, unique=True)
    inscricao_estadual = models.CharField("Inscrição Estadual", max_length=20, blank=True, null=True)
    endereco = models.TextField("Endereço Completo")
    cep = models.CharField("CEP", max_length=9, blank=True, null=True)
    cidade = models.CharField("Cidade", max_length=100, null=True, blank=True)
    estado = models.CharField("Estado", max_length=2, null=True, blank=True)
    telefone = models.CharField("Telefone Principal", max_length=15)
    telefone_secundario = models.CharField("Telefone Secundário", max_length=15, blank=True, null=True)
    email = models.EmailField("E-mail Principal")
    email_secundario = models.EmailField("E-mail Secundário", blank=True, null=True)
    website = models.URLField("Website", blank=True, null=True)
    pessoa_contato = models.CharField("Pessoa de Contato", max_length=100, blank=True, null=True)
    cargo_contato = models.CharField("Cargo do Contato", max_length=100, blank=True, null=True)
    descricao = models.TextField("Descrição do Fornecedor", blank=True, null=True)
    dia_pedido_recorrente = models.PositiveSmallIntegerField("Dia do Pedido Recorrente", blank=True, null=True, help_text="Dia do mês para gerar pedidos recorrentes (1-31)")
    tipo_fornecedor = models.CharField("Tipo do Fornecedor", max_length=10, choices=TIPO_CHOICES, default='FIXO')
    ativo = models.BooleanField("Ativo", default=True)
    data_cadastro = models.DateTimeField("Data de Cadastro", auto_now_add=True)
    data_atualizacao = models.DateTimeField("Data de Atualização", auto_now=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome']

class Produto(models.Model):
    nome = models.CharField("Nome do Produto", max_length=255)
    descricao = models.TextField("Descrição", blank=True, null=True)
    valor_unitario = models.DecimalField("Valor Unitário (R$)", max_digits=10, decimal_places=2)
    unidade_medida = models.CharField("Unidade de Medida", max_length=50, default="Unidade")
    codigo = models.CharField("Código do Produto", max_length=50, blank=True, null=True)
    data_cadastro = models.DateTimeField("Data de Cadastro", auto_now_add=True)
    ativo = models.BooleanField("Produto Ativo", default=True)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["nome"]
    
    def __str__(self):
        return f"{self.nome} - R$ {self.valor_unitario}"


class ProdutoLog(models.Model):
    ACAO_CHOICES = (
        ('INCLUSAO', 'Inclusão'),
        ('EDICAO', 'Edição'),
        ('EXCLUSAO', 'Exclusão'),
        ('IMPORTACAO', 'Importação'),
    )
    
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produto")
    nome_produto = models.CharField("Nome do Produto", max_length=255)
    acao = models.CharField("Ação", max_length=20, choices=ACAO_CHOICES)
    detalhes = models.TextField("Detalhes", blank=True, null=True)
    usuario = models.CharField("Usuário", max_length=255)
    data_hora = models.DateTimeField("Data/Hora", auto_now_add=True)
    ip = models.CharField("Endereço IP", max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = "Log de Produto"
        verbose_name_plural = "Logs de Produtos"
        ordering = ["-data_hora"]
    
    def __str__(self):
        return f"{self.acao} - {self.nome_produto} por {self.usuario} em {self.data_hora}"
    
    @classmethod
    def limpar_logs_antigos(cls, meses=3):
        """
        Remove logs mais antigos que o número de meses especificado.
        
        Args:
            meses (int): Número de meses para manter os logs. Padrão: 3
        
        Returns:
            int: Número de logs removidos
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Calcula a data de corte
        data_corte = timezone.now() - timedelta(days=meses * 30)
        
        # Encontra e exclui logs antigos
        logs_antigos = cls.objects.filter(data_hora__lt=data_corte)
        count = logs_antigos.count()
        logs_antigos.delete()
        
        return count
