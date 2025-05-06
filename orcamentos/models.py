from django.db import models
from django.contrib.auth.models import User
from produtos.models import Produto, Fornecedor
from django.utils import timezone

class Orcamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('avista', 'À Vista'),
        ('30dias', '30 Dias'),
        ('60dias', '60 Dias'),
        ('90dias', '90 Dias'),
        ('parcelado', 'Parcelado'),
        ('outros', 'Outros'),
    ]
    
    nome = models.CharField('Nome do Orçamento', max_length=200)
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pendente')
    justificativa = models.TextField('Justificativa', blank=True, null=True)
    melhor_orcamento = models.BooleanField('Melhor Orçamento', default=False)
    data_aprovacao = models.DateTimeField('Data de Aprovação', blank=True, null=True)
    usuario_aprovador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orcamentos_aprovados')
    fornecedor_vencedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True, related_name='orcamentos_vencedores')
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='avista', blank=True, null=True)
    data_entrega_prevista = models.DateField('Data Prevista de Entrega', blank=True, null=True)

    def __str__(self):
        return f"Orçamento #{self.id} - {self.nome}"

    @property
    def total(self):
        return sum(item.total for item in self.itens.all())

class ItemOrcamento(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True, blank=True)
    quantidade = models.PositiveIntegerField('Quantidade')
    valor_unitario = models.DecimalField('Valor Unitário', max_digits=10, decimal_places=2)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.DecimalField('Total', max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.quantidade * self.valor_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produto} - {self.quantidade} x {self.valor_unitario} (Orçamento {self.orcamento.id})"

class JustificativaAprovacao(models.Model):
    orcamento = models.OneToOneField('Orcamento', on_delete=models.CASCADE, related_name='justificativa_aprovacao')
    texto = models.TextField(verbose_name='Justificativa')
    data_criacao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Justificativa de Aprovação'
        verbose_name_plural = 'Justificativas de Aprovação'

    def __str__(self):
        return f'Justificativa para Orçamento #{self.orcamento.id}'
