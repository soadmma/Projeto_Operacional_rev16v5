# Instruções para Acesso Remoto ao Sistema

Este documento explica como configurar e acessar o sistema remotamente.

## Métodos de Acesso Remoto

Existem três formas de acessar o sistema remotamente:

### 1. Acesso Local (dentro da mesma rede)

Para acessar o sistema de outros dispositivos dentro da mesma rede local:

1. Execute o script `start_server.sh` (Linux/Mac) ou `start_server.bat` (Windows)
2. O servidor estará disponível em: http://192.168.15.69:8000

```bash
# Linux/Mac
./start_server.sh

# Windows (executar o arquivo start_server.bat)
```

### 2. Acesso Remoto via Ngrok (pela Internet)

Para acessar o sistema de qualquer lugar pela internet usando Ngrok:

1. Crie uma conta gratuita em [ngrok.com](https://ngrok.com/)
2. Obtenha seu token de autenticação no painel do Ngrok
3. Edite o arquivo `start_server_ngrok.py` e descomente a linha com `ngrok.set_auth_token`
4. Substitua "SUA_CHAVE_DE_AUTENTICACAO_NGROK" pelo seu token
5. Execute o script:

```bash
# Ative o ambiente virtual primeiro (se necessário)
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Execute o script
python start_server_ngrok.py
```

O script irá mostrar a URL pública que pode ser acessada de qualquer lugar.

### 3. Configuração de VPN (Acesso Permanente)

Para uma solução VPN completa, recomenda-se:

1. Configurar o OpenVPN ou WireGuard no servidor
2. Criar e distribuir arquivos de configuração para os clientes
3. Acessar o sistema usando o IP interno após conectar-se à VPN

## Notas de Segurança

- O acesso via Ngrok é conveniente para testes, mas não é recomendado para produção
- Para ambientes de produção, configure um servidor web adequado (como Nginx ou Apache) com HTTPS
- Sempre use credenciais fortes e considere implementar autenticação de dois fatores
- Desative o modo DEBUG em produção (edite `config/settings.py` e altere `DEBUG = False`)

## Solução de Problemas

- Se o servidor não iniciar, verifique se a porta 8000 está disponível
- Para problemas com Ngrok, consulte a [documentação oficial](https://ngrok.com/docs)
- Para VPN, consulte a documentação específica da solução escolhida 