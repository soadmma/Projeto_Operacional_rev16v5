#!/usr/bin/env python
"""
Script para restaurar permissões do superusuário
=============================================================
Este script restaura todas as permissões para o usuário administrador,
garantindo que ele tenha acesso total ao sistema.

Executar com: python restaurar_admin.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

# Função principal
def restaurar_admin():
    try:
        # Encontrar o primeiro superusuário (geralmente chamado admin)
        admin = User.objects.filter(is_superuser=True).first()
        
        if not admin:
            print("⚠️ ERRO: Nenhum superusuário encontrado no sistema.")
            return
        
        print(f"\n=== Restaurando permissões para o superusuário: {admin.username} ===")
        
        # Garantir que todas as flags estão ativas
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        
        # Atualizar o usuário
        admin.save()
        
        # Conceder todas as permissões para o usuário admin
        todas_permissoes = Permission.objects.all()
        admin.user_permissions.clear()  # Limpar permissões existentes
        
        # Adicionar todas as permissões
        for permissao in todas_permissoes:
            admin.user_permissions.add(permissao)
        
        # Salvar novamente
        admin.save()
        
        print(f"✅ Permissões restauradas com sucesso para {admin.username}!")
        print(f"   • Total de permissões concedidas: {admin.user_permissions.count()}")
        print(f"   • Status de superusuário: {'SIM' if admin.is_superuser else 'NÃO'}")
        print(f"   • Status de staff: {'SIM' if admin.is_staff else 'NÃO'}")
        print(f"   • Status ativo: {'SIM' if admin.is_active else 'NÃO'}")
        
        print("\n🔍 Verificando middleware de controle de acesso...")
        from django.conf import settings
        if 'core.middleware.PerfilAcessoMiddleware' in settings.MIDDLEWARE:
            print("ℹ️ O middleware de controle de acesso está ativo.")
            print("   Isto NÃO deve afetar o superusuário, pois ele está explicitamente excluído.")
            print("   Verifique a linha em core/middleware.py que contém 'and not request.user.is_superuser'")
            
    except Exception as e:
        print(f"⚠️ ERRO ao restaurar permissões: {str(e)}")

# Executar o script
if __name__ == "__main__":
    restaurar_admin()
    
    print("\n=== INSTRUÇÕES ADICIONAIS ===")
    print("""
Se ainda houver problemas após executar este script:

1. Verifique se o middleware está funcionando corretamente
   Na classe PerfilAcessoMiddleware, certifique-se de que a condição:
   'if request.user.groups.filter(name='Gerente Operacional').exists() and not request.user.is_superuser:'
   contenha 'and not request.user.is_superuser' para excluir o superusuário das restrições.

2. Se precisar criar um novo superusuário:
   python manage.py createsuperuser

3. Para verificar se o middleware está configurado corretamente:
   python manage.py shell
   >>> from django.conf import settings
   >>> 'core.middleware.PerfilAcessoMiddleware' in settings.MIDDLEWARE
""") 