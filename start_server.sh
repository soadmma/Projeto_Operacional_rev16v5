#!/bin/bash

# Ativa o ambiente virtual (se necessário)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "env" ]; then
    source .venv/bin/activate
fi

# Inicia o servidor em 0.0.0.0:8000 para aceitar conexões de qualquer endereço IP
echo "Iniciando servidor em 0.0.0.0:8000"
echo "Este servidor estará disponível na rede local em: http://192.168.15.69:8000"
python3 manage.py runserver 0.0.0.0:8000 