import os
import django

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def reset_auth_user_sequence():
    """Reseta a sequência da tabela auth_user"""
    with connection.cursor() as cursor:
        try:
            # Primeiro, vamos verificar o maior ID existente
            cursor.execute("SELECT MAX(id) FROM auth_user")
            max_id = cursor.fetchone()[0]
            
            if max_id is None:
                max_id = 0
            
            print(f"Maior ID encontrado na tabela auth_user: {max_id}")
            
            # Agora vamos resetar a sequência
            cursor.execute(f"""
                SELECT setval('auth_user_id_seq', {max_id}, true);
            """)
            
            # Verificar se a sequência foi atualizada
            cursor.execute("SELECT last_value FROM auth_user_id_seq")
            new_value = cursor.fetchone()[0]
            
            print(f"Sequência auth_user_id_seq atualizada para: {new_value}")
            print("✓ Sequência atualizada com sucesso!")
            
        except Exception as e:
            print(f"✗ Erro ao atualizar sequência: {e}")

if __name__ == "__main__":
    print("Iniciando atualização da sequência auth_user_id_seq...")
    reset_auth_user_sequence()
    print("Concluído!") 