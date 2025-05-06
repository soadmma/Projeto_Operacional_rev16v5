from django import template
from datetime import datetime

register = template.Library()

@register.filter
def filter_status(queryset, status):
    """Filtra um queryset por status"""
    return [item for item in queryset if item.status == status]

@register.filter
def filter_produto(itens, produto_nome):
    return itens.filter(produto__nome=produto_nome)

@register.filter
def subtract(value, arg):
    """Subtrai o argumento do valor"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def divide(value, arg):
    if arg == 0:
        return 0
    return value / arg

@register.filter
def percentage_difference(value, arg):
    """Calcula a diferença percentual entre dois valores"""
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return 0
        return ((value - arg) / arg) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def dias_ate_primeira_entrega(data_atual, orcamentos):
    """Calcula a diferença em dias entre a data atual e a primeira data de entrega do grupo."""
    if not data_atual or not orcamentos:
        return '--'
    
    datas_entrega = [orc.data_entrega_prevista for orc in orcamentos if orc.data_entrega_prevista]
    if not datas_entrega:
        return '--'
        
    primeira_data = min(datas_entrega)
    if isinstance(data_atual, datetime):
        data_atual = data_atual.date()
    if isinstance(primeira_data, datetime):
        primeira_data = primeira_data.date()
        
    diferenca = (data_atual - primeira_data).days
    if diferenca == 0:
        return 'Mesma data'
    elif diferenca < 0:
        return f'{abs(diferenca)} dias antes'
    else:
        return f'{diferenca} dias depois' 