#!/usr/bin/env python
"""
Script para migrar dados do SQLite para PostgreSQL
===============================================
Este script:
1. Faz backup dos dados do SQLite
2. Cria as tabelas no PostgreSQL
3. Migra os dados do SQLite para o PostgreSQL
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import subprocess
import time

# Configurações do banco de dados
SQLITE_DB = 'db.sqlite3'
POSTGRES_CONFIG = {
    'dbname': 'operacional_db',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

# Ordem de migração das tabelas para respeitar as dependências
MIGRATION_ORDER = [
    # Tabelas do Django
    'django_content_type',
    'auth_permission',
    'auth_group',
    'auth_user',
    'auth_group_permissions',
    'auth_user_groups',
    'auth_user_user_permissions',
    'django_admin_log',
    'django_session',
    
    # Tabelas do projeto
    'core_empresa',
    'core_contrato',
    'core_detalhescontrato',
    'produtos_produto',
    'escolas_supervisor',
    'escolas_escola',
    'pedidos_pedido',
    'pedidos_itempedido',
    'pedidos_pedidolog',
    'produtos_produtolog',
    'escolas_escolalog',
    'core_configuracaosistema'
]

# Mapeamento de campos booleanos por tabela
BOOLEAN_FIELDS = {
    'produtos_produto': ['ativo'],
    'escolas_supervisor': ['ativo'],
    'core_empresa': ['ativo'],
    'core_contrato': ['ativo'],
    'escolas_escola': ['ativo'],
    'pedidos_pedido': ['aprovado', 'cancelado', 'enviado'],
    'auth_user': ['is_superuser', 'is_staff', 'is_active']
}

def convert_data(data, table_name, columns):
    """Converte os tipos de dados do SQLite para PostgreSQL"""
    converted = []
    
    # Obtém os índices dos campos booleanos
    boolean_indices = []
    if table_name in BOOLEAN_FIELDS:
        boolean_indices = [columns.index(field) for field in BOOLEAN_FIELDS[table_name] if field in columns]
    
    for row in data:
        new_row = list(row)
        
        # Converte campos booleanos
        for idx in boolean_indices:
            new_row[idx] = bool(new_row[idx])
        
        converted.append(tuple(new_row))
    
    return converted

def get_sqlite_tables():
    """Obtém todas as tabelas do banco SQLite"""
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")

    tables = [table[0] for table in cursor.fetchall()]
    conn.close()
    return tables

def get_table_data(table_name):
    """Obtém todos os dados de uma tabela do SQLite"""
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name};")
    columns = [description[0] for description in cursor.description]
    data = cursor.fetchall()
    conn.close()
    return columns, data

def migrate_table(table_name, columns, data):
    """Migra os dados de uma tabela para o PostgreSQL"""
    if not data:
        print(f"✓ Tabela {table_name} está vazia, pulando...")
        return
    
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    
    # Limpa a tabela antes de inserir os dados
    try:
        cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
        conn.commit()
    except Exception as e:
        print(f"✗ Erro ao limpar tabela {table_name}: {e}")
        conn.rollback()
        return
    
    # Converte os dados
    converted_data = convert_data(data, table_name, columns)
    
    # Cria a string de colunas para a query
    columns_str = ', '.join(columns)
    
    # Prepara a query de inserção
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES %s;"
    
    try:
        # Insere os dados
        execute_values(cursor, query, converted_data)
        conn.commit()
        print(f"✓ Tabela {table_name} migrada com sucesso ({len(data)} registros)")
    except Exception as e:
        print(f"✗ Erro ao migrar tabela {table_name}: {e}")
        conn.rollback()
    finally:
        conn.close()

def reset_sequences():
    """Reseta as sequências do PostgreSQL após a migração"""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Obtém todas as sequências
        cursor.execute("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        sequences = cursor.fetchall()
        
        # Atualiza cada sequência
        for seq in sequences:
            seq_name = seq[0]
            table_name = seq_name.replace('_id_seq', '')
            cursor.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1,
                    false
                );
            """)
        
        conn.commit()
        print("\n✓ Sequências atualizadas com sucesso")
    except Exception as e:
        print(f"\n✗ Erro ao atualizar sequências: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    print("Iniciando migração de dados do SQLite para PostgreSQL...")
    
    # Faz backup do SQLite
    print("\nFazendo backup do banco SQLite...")
    subprocess.run(['./backup_sqlite.sh'])
    
    # Aguarda um momento para garantir que o backup foi feito
    time.sleep(2)
    
    # Migra as tabelas na ordem correta
    print(f"\nMigrando tabelas na ordem definida...")
    
    for table in MIGRATION_ORDER:
        print(f"\nMigrando tabela: {table}")
        columns, data = get_table_data(table)
        migrate_table(table, columns, data)
    
    # Atualiza as sequências
    reset_sequences()
    
    print("\nMigração concluída!")

if __name__ == "__main__":
    main() 