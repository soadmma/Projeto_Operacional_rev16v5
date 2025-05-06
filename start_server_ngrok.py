#!/usr/bin/env python
"""
Script para iniciar o servidor Django com Ngrok para acesso remoto
===============================
Este script inicia o servidor Django em 0.0.0.0:8000 e cria um túnel Ngrok
para permitir acesso ao sistema de qualquer lugar via internet.

Nota: É necessário cadastrar-se em https://ngrok.com/ e obter um token
de autenticação gratuito para usar este script sem restrições.
"""

import os
import sys
import subprocess
import time
import threading
from pyngrok import ngrok, conf

# Define a porta do servidor Django
PORT = 8000

def start_django_server():
    """Inicia o servidor Django em segundo plano"""
    print("Iniciando servidor Django na porta", PORT)
    # Usando subprocess.Popen para não bloquear o fluxo principal
    return subprocess.Popen([
        sys.executable, "manage.py", "runserver", f"0.0.0.0:{PORT}"
    ])

def setup_ngrok():
    """Configura e inicia o túnel Ngrok"""
    # Descomente e substitua pela sua chave de autenticação Ngrok se tiver uma
    # ngrok.set_auth_token("SUA_CHAVE_DE_AUTENTICACAO_NGROK")
    
    # Inicia o túnel Ngrok apontando para o servidor Django
    public_url = ngrok.connect(PORT).public_url
    print(f"\n{'='*80}")
    print(f"🌐 Servidor acessível publicamente em: {public_url}")
    print(f"🌐 Servidor acessível na rede local em: http://192.168.15.69:{PORT}")
    print(f"{'='*80}\n")
    return public_url

def main():
    # Configura ambiente Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    try:
        # Inicia o servidor Django
        django_process = start_django_server()
        
        # Aguarda alguns segundos para o servidor iniciar
        time.sleep(2)
        
        # Configura e inicia o túnel Ngrok
        public_url = setup_ngrok()
        
        print("Servidor iniciado com sucesso!")
        print("Pressione Ctrl+C para encerrar o servidor.")
        
        # Mantém o script em execução até Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nEncerrando servidor...")
            django_process.terminate()
            ngrok.kill()
            print("Servidor encerrado.")
    
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 