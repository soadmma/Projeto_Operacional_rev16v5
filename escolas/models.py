from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Supervisor(models.Model):
    nome = models.CharField("Nome do Supervisor", max_length=255)
    email = models.EmailField("E-mail", blank=True, null=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    ativo = models.BooleanField("Ativo", default=True)
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Usuário do Sistema", related_name="supervisor")
    
    class Meta:
        verbose_name = "Supervisor"
        verbose_name_plural = "Supervisores"
        ordering = ["nome"]
    
    def __str__(self):
        return self.nome

class Escola(models.Model):
    nome = models.CharField("Nome da Escola", max_length=255)
    codigo = models.CharField("Código da Escola", max_length=50, blank=True, null=True)
    lote = models.CharField("Lote", max_length=50, blank=True, null=True)
    empresa = models.CharField("Empresa", max_length=100, blank=True, null=True)
    budget = models.DecimalField("Orçamento (R$)", max_digits=10, decimal_places=2, default=0, help_text="Valor máximo permitido por pedido")
    data_validade_budget = models.DateField("Validade do Orçamento", blank=True, null=True, help_text="Data limite para utilização do orçamento")
    endereco = models.TextField("Endereço Completo", blank=True, null=True)
    cep = models.CharField("CEP", max_length=10, blank=True, null=True)
    cidade = models.CharField("Cidade", max_length=100, blank=True, null=True)
    estado = models.CharField("Estado", max_length=2, blank=True, null=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    email = models.EmailField("E-mail", blank=True, null=True)
    supervisor = models.ForeignKey(
        Supervisor, 
        on_delete=models.SET_NULL, 
        verbose_name="Supervisor Responsável", 
        related_name="escolas",
        blank=True, 
        null=True
    )
    data_cadastro = models.DateTimeField("Data de Cadastro", auto_now_add=True)
    ativo = models.BooleanField("Escola Ativa", default=True)
    
    class Meta:
        verbose_name = "Escola"
        verbose_name_plural = "Escolas"
        ordering = ["nome"]
    
    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Verificar se já existe uma instância (edição) ou se é nova
        if self.id:
            # É uma edição, vamos verificar mudanças no budget
            try:
                antiga_escola = Escola.objects.get(id=self.id)
                # Se o budget foi alterado, registrar no histórico
                if antiga_escola.budget != self.budget:
                    user = kwargs.pop('user', None)
                    # Criar registro no histórico de budget
                    HistoricoBudget.objects.create(
                        escola=self,
                        valor_anterior=antiga_escola.budget,
                        valor_novo=self.budget,
                        usuario=user.username if user else 'Sistema'
                    )
            except Escola.DoesNotExist:
                # Escola não existe ainda (pode acontecer em migrações)
                pass
        else:
            # Se o objeto é novo (sem ID) e não tem código definido
            if not self.codigo:
                # Gera um código baseado no total de escolas + 1000
                total_escolas = Escola.objects.count()
                self.codigo = str(total_escolas + 1000)
            
            # Registrar o budget inicial se for maior que zero
            if self.budget > 0:
                user = kwargs.pop('user', None)
                # Precisamos salvar primeiro para ter o ID da escola
                super().save(*args, **kwargs)
                HistoricoBudget.objects.create(
                    escola=self,
                    valor_anterior=0,
                    valor_novo=self.budget,
                    usuario=user.username if user else 'Sistema'
                )
                return  # Já salvou acima, não precisa salvar novamente
                
        super().save(*args, **kwargs)

    @property
    def budget_valido(self):
        """Verifica se o orçamento ainda é válido"""
        if self.data_validade_budget is None:
            return True  # Se não tem data de validade, considera-se válido
        
        return self.data_validade_budget >= timezone.localdate()
    
    @property
    def variacao_budget(self):
        """Retorna a variação percentual do budget atual em relação ao inicial"""
        historico = self.historico_budget.order_by('data_alteracao')
        if not historico.exists():
            return 0
        
        primeiro_budget = historico.first().valor_anterior or 0
        if primeiro_budget == 0:
            # Se o primeiro budget era zero, pegamos o primeiro valor não-zero
            for registro in historico:
                if registro.valor_anterior > 0:
                    primeiro_budget = registro.valor_anterior
                    break
            # Se ainda for zero, usamos o primeiro valor_novo
            if primeiro_budget == 0:
                primeiro_budget = historico.first().valor_novo
                
        # Evitar divisão por zero
        if primeiro_budget == 0:
            return 100 if self.budget > 0 else 0
            
        # Calcular variação em percentual
        return ((self.budget - primeiro_budget) / primeiro_budget) * 100

class EscolaLog(models.Model):
    """Modelo para registrar logs de ações nas escolas/contratos"""
    ACOES_CHOICES = (
        ('INCLUSAO', 'Inclusão'),
        ('EDICAO', 'Edição'),
        ('EXCLUSAO', 'Exclusão'),
        ('IMPORTACAO', 'Importação'),
    )
    
    escola = models.ForeignKey(Escola, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    nome_escola = models.CharField("Nome da Escola/Contrato", max_length=255)
    acao = models.CharField("Ação Realizada", max_length=20, choices=ACOES_CHOICES)
    detalhes = models.TextField("Detalhes", blank=True, null=True)
    usuario = models.CharField("Usuário", max_length=150)
    ip = models.CharField("Endereço IP", max_length=45, blank=True, null=True)
    data_hora = models.DateTimeField("Data e Hora", auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Escola/Contrato"
        verbose_name_plural = "Logs de Escolas/Contratos"
        ordering = ["-data_hora"]
    
    def __str__(self):
        return f"{self.acao} - {self.nome_escola} ({self.data_hora.strftime('%d/%m/%Y %H:%M')})"

class HistoricoBudget(models.Model):
    """Modelo para rastrear alterações no orçamento (budget) das escolas"""
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='historico_budget')
    valor_anterior = models.DecimalField("Valor Anterior (R$)", max_digits=10, decimal_places=2)
    valor_novo = models.DecimalField("Valor Novo (R$)", max_digits=10, decimal_places=2)
    data_alteracao = models.DateTimeField("Data da Alteração", auto_now_add=True)
    usuario = models.CharField("Usuário", max_length=150)
    
    class Meta:
        verbose_name = "Histórico de Orçamento"
        verbose_name_plural = "Históricos de Orçamento"
        ordering = ["-data_alteracao"]
    
    def __str__(self):
        return f"Budget de {self.escola.nome}: R$ {self.valor_anterior} → R$ {self.valor_novo}"
    
    @property
    def variacao_percentual(self):
        """Retorna a variação percentual entre valor_anterior e valor_novo"""
        if self.valor_anterior == 0:
            return 100 if self.valor_novo > 0 else 0
        return ((self.valor_novo - self.valor_anterior) / self.valor_anterior) * 100
