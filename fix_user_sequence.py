import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_pedidos.settings')
django.setup()

from django.db import connection

def fix_user_sequence():
    with connection.cursor() as cursor:
        # Obter o maior ID atual
        cursor.execute("SELECT MAX(id) FROM auth_user;")
        max_id = cursor.fetchone()[0] or 0
        
        # Resetar a sequência para o próximo valor após o maior ID
        cursor.execute(f"ALTER SEQUENCE auth_user_id_seq RESTART WITH {max_id + 1};")
        print(f"Sequência resetada para {max_id + 1}")

if __name__ == '__main__':
    fix_user_sequence() 