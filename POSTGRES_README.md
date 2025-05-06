# Configuração do PostgreSQL

Este projeto agora utiliza PostgreSQL como banco de dados principal. Este documento fornece informações sobre como gerenciar o banco de dados PostgreSQL.

## Configuração Atual

- **Banco de dados**: `operacional_db`
- **Usuário**: `postgres`
- **Senha**: `postgres`
- **Host**: `localhost`
- **Porta**: `5432`

## Scripts Disponíveis

### 1. Configuração do PostgreSQL

O script `setup_postgres.sh` configura o PostgreSQL e cria o banco de dados:

```bash
sudo ./setup_postgres.sh
```

### 2. Backup do SQLite

O script `backup_sqlite.sh` cria um backup do banco de dados SQLite:

```bash
./backup_sqlite.sh
```

### 3. Migração de SQLite para PostgreSQL

O script `migrate_to_postgres.py` migra os dados do SQLite para o PostgreSQL:

```bash
source venv/bin/activate
python migrate_to_postgres.py
```

### 4. Resetar Sequências de IDs

O script `reset_all_sequences.sh` atualiza todas as sequências de IDs para evitar conflitos:

```bash
sudo ./reset_all_sequences.sh
```

## Comandos Úteis do PostgreSQL

### Conectar ao banco de dados
```bash
sudo -u postgres psql -d operacional_db
```

### Listar tabelas
```bash
\dt 
```

### Backup do banco de dados
```bash
pg_dump -U postgres -d operacional_db > backup.sql
```

### Restaurar banco de dados
```bash
psql -U postgres -d operacional_db < backup.sql
```

## Solução de Problemas

### Erro de chave duplicada

Se você encontrar erros de chave duplicada ao criar novos registros, execute o script de reset de sequências:

```bash
sudo ./reset_all_sequences.sh
```

### Serviço PostgreSQL não está rodando

Para iniciar o serviço PostgreSQL:

```bash
sudo service postgresql start
```

### Verificar status do PostgreSQL

```bash
sudo service postgresql status
``` 