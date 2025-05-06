#!/bin/bash

# Verifica se o PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL não está instalado. Instalando..."
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
fi

# Inicia o serviço do PostgreSQL
sudo service postgresql start

# Cria o banco de dados e o usuário
sudo -u postgres psql -c "CREATE DATABASE operacional_db;"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"

# Ativa o ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "env" ]; then
    source env/bin/activate
fi\

# Instala as dependências
pip install -r requirements.txt

# Faz as migrações
python manage.py makemigrations
python manage.py migrate

echo "Banco de dados PostgreSQL configurado com sucesso!"
echo "Você pode acessar o banco de dados com:"
echo "Host: localhost"
echo "Porta: 5432"
echo "Banco: operacional_db"
echo "Usuário: postgres"
echo "Senha: postgres" 