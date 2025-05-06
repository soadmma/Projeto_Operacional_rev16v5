#!/bin/bash

# Cria um diretório para os backups se não existir
mkdir -p backups

# Gera um nome de arquivo com timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backups/db_backup_${TIMESTAMP}.sqlite3"

# Faz uma cópia do banco de dados SQLite
cp db.sqlite3 "$BACKUP_FILE"

echo "Backup do banco de dados SQLite criado em: $BACKUP_FILE"
echo "Você pode restaurar este backup se necessário usando:"
echo "cp $BACKUP_FILE db.sqlite3" 