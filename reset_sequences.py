#!/usr/bin/env python
"""
Script para resetar as sequências do PostgreSQL
==============================================
Este script atualiza todas as sequências do PostgreSQL para o maior ID existente em cada tabela,
evitando erros de chave duplicada ao inserir novos registros.
"""

import psycopg2

# Configurações do banco de dados
POSTGRES_CONFIG = {
    'dbname': 'operacional_db',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

def reset_sequences():
    """Reseta as sequências do PostgreSQL após a migração"""
    print("Tentando conectar ao banco de dados...")
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        # Obtém todas as sequências
        cursor.execute("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        sequences = cursor.fetchall()
        
        print(f"Encontradas {len(sequences)} sequências para atualizar")
        
        # Atualiza cada sequência
        for seq in sequences:
            seq_name = seq[0]
            table_name = seq_name.replace('_id_seq', '')
            
            # Para algumas tabelas, precisamos ajustar o nome da tabela
            if table_name.startswith('django_'):
                table_name = table_name  # Mantém o nome da tabela django
            
            try:
                cursor.execute(f"""
                    SELECT setval(
                        '{seq_name}',
                        COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1,
                        false
                    );
                """)
                print(f"✓ Sequência {seq_name} atualizada com sucesso")
            except Exception as e:
                print(f"✗ Erro ao atualizar sequência {seq_name}: {e}")
        
        conn.commit()
        print("\n✓ Todas as sequências foram atualizadas com sucesso")
    except Exception as e:
        print(f"\n✗ Erro ao conectar ao banco de dados: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Iniciando atualização das sequências do PostgreSQL...")
    reset_sequences()
    print("Concluído!") 