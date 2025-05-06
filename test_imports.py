#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script para testar a importação correta dos modelos
import os
import sys
import django

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Agora tenta importar os modelos
try:
    from pedidos.models import Pedido, NotaFiscal, ItemNotaFiscal
    print("✅ Importação bem-sucedida!")
    print(f"Pedido: {Pedido}")
    print(f"NotaFiscal: {NotaFiscal}")
    print(f"ItemNotaFiscal: {ItemNotaFiscal}")
except ImportError as e:
    print(f"❌ Erro na importação: {e}") 