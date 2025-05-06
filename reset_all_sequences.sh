#!/bin/bash

# Script para atualizar todas as sequências do PostgreSQL
# Este script atualiza as sequências de IDs para evitar conflitos de chaves duplicadas

# Lista de tabelas a serem atualizadas
TABLES=(
  "auth_user"
  "auth_group"
  "auth_permission"
  "django_content_type"
  "django_admin_log"
  "core_empresa"
  "core_contrato"
  "core_detalhescontrato"
  "produtos_produto"
  "produtos_produtolog"
  "escolas_supervisor"
  "escolas_escola"
  "escolas_escolalog"
  "pedidos_pedido"
  "pedidos_itempedido"
  "pedidos_pedidolog"
  "core_configuracaosistema"
)

echo "Atualizando sequências do PostgreSQL..."

# Atualiza cada sequência
for TABLE in "${TABLES[@]}"; do
  echo "Atualizando sequência para tabela: $TABLE"
  sudo -u postgres psql -d operacional_db -c "SELECT setval(pg_get_serial_sequence('$TABLE', 'id'), COALESCE((SELECT MAX(id) FROM $TABLE), 0) + 1, false);"
done

echo "Todas as sequências foram atualizadas com sucesso!" 