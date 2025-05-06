#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import os
from requests.cookies import cookiejar_from_dict

# Configuração do teste
SERVER_URL = "http://localhost:8000"
LOGIN_URL = f"{SERVER_URL}/usuarios/login/"
UPLOAD_URL = f"{SERVER_URL}/pedidos/processar-xml-nfe-massa/"
USERNAME = "mauricio"  # Usuário com permissão
PASSWORD = "senha123"  # Senha do usuário

# Caminho para o arquivo XML
XML_FILE_PATH = "teste_pedint_10.xml"

# Função para fazer login e obter a sessão autenticada
def login():
    # Criar uma sessão para manter os cookies
    session = requests.Session()
    
    # Primeiro acesso para obter o token CSRF
    print("Obtendo token CSRF...")
    response = session.get(LOGIN_URL)
    
    # Extrair o token CSRF do HTML (técnica simples)
    csrf_token = None
    for line in response.text.split('\n'):
        if 'csrfmiddlewaretoken' in line:
            # Extração básica do valor do token
            parts = line.split('value="')
            if len(parts) > 1:
                csrf_token = parts[1].split('"')[0]
                break
    
    if not csrf_token:
        print("❌ Não foi possível obter o token CSRF")
        return None
    
    print(f"✅ Token CSRF obtido: {csrf_token[:10]}...")
    
    # Fazer login com as credenciais
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_token,
    }
    
    print(f"Fazendo login com o usuário: {USERNAME}...")
    response = session.post(
        LOGIN_URL, 
        data=login_data,
        headers={'Referer': LOGIN_URL}
    )
    
    # Verificar se o login foi bem-sucedido
    if response.url != LOGIN_URL:  # Redirecionou para outra página (login bem-sucedido)
        print(f"✅ Login realizado com sucesso! Redirecionado para: {response.url}")
        return session
    else:
        print("❌ Falha no login. Verifique as credenciais.")
        return None

# Função para fazer upload do XML
def upload_xml(session):
    if not os.path.exists(XML_FILE_PATH):
        print(f"❌ Arquivo XML não encontrado: {XML_FILE_PATH}")
        return False
    
    # Obter token CSRF da página de upload antes de enviar o arquivo
    print("Obtendo token CSRF da página alvo...")
    response = session.get(UPLOAD_URL.replace("processar-xml-nfe-massa", "importar-xml-nfe-massa"))
    
    # Extrair o token CSRF do HTML
    csrf_token = None
    for line in response.text.split('\n'):
        if 'csrfmiddlewaretoken' in line:
            parts = line.split('value="')
            if len(parts) > 1:
                csrf_token = parts[1].split('"')[0]
                break
    
    if not csrf_token:
        print("❌ Não foi possível obter o token CSRF da página alvo")
        return False
    
    print(f"✅ Token CSRF alvo obtido: {csrf_token[:10]}...")
    
    # Preparar os dados para upload
    with open(XML_FILE_PATH, 'rb') as f:
        files = {'xml_files': (os.path.basename(XML_FILE_PATH), f, 'text/xml')}
        data = {
            'atualizar_previsao_entrega': '1',
            'csrfmiddlewaretoken': csrf_token
        }
        
        print(f"Enviando XML para {UPLOAD_URL}...")
        response = session.post(
            UPLOAD_URL, 
            files=files, 
            data=data,
            headers={
                'Referer': response.url,
                'X-CSRFToken': csrf_token
            }
        )
        
        # Verificar resposta
        print(f"Status Code: {response.status_code}")
        print(f"URL de resposta: {response.url}")
        
        if response.status_code == 200 or response.status_code == 302:
            print("✅ Upload realizado!")
            # Se redirecionou para a mesma página, pode ter sido processado com sucesso
            if "processar-xml-nfe-massa" in response.url or "importar-xml-nfe-massa" in response.url:
                print("✅ Processo concluído com sucesso!")
                return True
            else:
                print("⚠️ Redirecionado para outra página. Verifique se o upload foi bem-sucedido.")
                return True
        else:
            print(f"❌ Erro no upload: {response.status_code}")
            # Tentar imprimir parte da resposta para debug
            print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
            return False

# Função principal
def main():
    print("🔄 Iniciando teste de upload autenticado de XML...")
    
    # Fazer login
    session = login()
    if not session:
        print("❌ Abortando teste devido a falha no login")
        return
    
    # Fazer upload do XML
    success = upload_xml(session)
    
    if success:
        print("✅ Teste concluído com sucesso!")
    else:
        print("❌ Teste falhou!")

# Executar o teste
if __name__ == "__main__":
    main() 