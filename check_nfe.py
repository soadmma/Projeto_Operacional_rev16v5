#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import django

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Importar modelos
from pedidos.models import NotaFiscal, Pedido

def verificar_notas():
    """Verifica as notas fiscais existentes no sistema"""
    print("Verificando notas fiscais no sistema...")
    
    # Buscar todas as notas fiscais
    notas = NotaFiscal.objects.all().order_by('-id')
    
    if not notas.exists():
        print("❌ Nenhuma nota fiscal encontrada no sistema.")
        return
    
    print(f"✅ Total de notas fiscais: {notas.count()}")
    print("\nDetalhes das notas fiscais mais recentes:")
    
    # Mostrar detalhes das 3 notas mais recentes
    for i, nf in enumerate(notas[:3], 1):
        print(f"\nNota fiscal #{i}:")
        print(f"ID: {nf.id}")
        print(f"Chave: {nf.chave_nfe}")
        print(f"Número: {nf.numero_nfe}")
        print(f"Data emissão: {nf.data_emissao}")
        print(f"Valor total: {nf.valor_total}")
        print(f"Emitente: {nf.razao_social_emitente}")
        print(f"CNPJ Emitente: {nf.cnpj_emitente}")
        
        # Mostrar detalhes do pedido associado
        if nf.pedido:
            pedido = nf.pedido
            print(f"Pedido associado: #{pedido.id}")
            print(f"Status do pedido: {pedido.status}")
            print(f"Escola: {pedido.escola.nome if pedido.escola else 'N/A'}")
        else:
            print("Sem pedido associado")
        
        # Mostrar itens da nota fiscal
        itens = nf.itens.all()
        if itens.exists():
            print(f"Total de itens: {itens.count()}")
            for j, item in enumerate(itens[:3], 1):
                print(f"  Item {j}: {item.descricao} ({item.quantidade} {item.unidade}) - R$ {item.valor_total}")
            
            if itens.count() > 3:
                print(f"  ... e mais {itens.count() - 3} itens")
        else:
            print("Nenhum item encontrado nesta nota fiscal")

    # Verificar especificamente a nota fiscal com a chave usada no teste
    chave_teste = "35250320102722000164550000003409721103409721"
    nota_teste = NotaFiscal.objects.filter(chave_nfe=chave_teste).first()
    
    if nota_teste:
        print("\n✅ Nota fiscal de teste encontrada!")
        print(f"ID: {nota_teste.id}")
        print(f"Pedido associado: {nota_teste.pedido_id}")
        print(f"Itens: {nota_teste.itens.count()}")
    else:
        print("\n❌ Nota fiscal de teste NÃO encontrada!")

if __name__ == "__main__":
    verificar_notas() 