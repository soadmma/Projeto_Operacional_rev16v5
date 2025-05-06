from django.contrib import admin
from .models import Pedido, ItemPedido, NotaFiscal

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    autocomplete_fields = ['produto']
    fields = ('produto', 'quantidade', 'valor_unitario')
    extra = 1
    min_num = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'escola', 'data_solicitacao', 'status', 'get_valor_total')
    list_filter = ('status', 'escola', 'data_solicitacao')
    search_fields = ('escola__nome', 'observacoes')
    autocomplete_fields = ['escola']
    readonly_fields = ('data_solicitacao',)
    inlines = [ItemPedidoInline]
    
    def get_valor_total(self, obj):
        return f"R$ {obj.valor_total:.2f}"
    get_valor_total.short_description = "Valor Total"

@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = ('numero_nfe', 'pedido', 'chave_nfe', 'data_emissao', 'razao_social_emitente', 'valor_total')
    list_filter = ('data_emissao', 'data_importacao')
    search_fields = ('numero_nfe', 'chave_nfe', 'razao_social_emitente', 'cnpj_emitente')
    readonly_fields = ('data_importacao',)
    autocomplete_fields = ['pedido']
    ordering = ('-data_emissao',)
