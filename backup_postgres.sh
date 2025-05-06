#!/bin/bash

# Cria um diretório para os backups se não existir
mkdir -p backups/postgres

# Gera um nome de arquivo com timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backups/postgres/db_backup_${TIMESTAMP}.sql"

# Faz backup do banco de dados PostgreSQL
echo "Fazendo backup do banco de dados PostgreSQL..."
sudo -u postgres pg_dump operacional_db > "$BACKUP_FILE"

# Compacta o arquivo para economizar espaço
gzip "$BACKUP_FILE"

echo "Backup do banco de dados PostgreSQL criado em: ${BACKUP_FILE}.gz"
echo "Você pode restaurar este backup usando:"
echo "gunzip ${BACKUP_FILE}.gz"
echo "sudo -u postgres psql -d operacional_db < $BACKUP_FILE" 