#!/bin/bash

# Verificar se foi fornecido um arquivo de backup
if [ $# -ne 1 ]; then
  echo "Uso: $0 caminho_para_arquivo_de_backup.sql"
  echo "Exemplo: $0 ./backups/backup_cyberos_db_20250430_104413.sql"
  exit 1
fi

BACKUP_FILE=$1

# Verificar se o arquivo existe
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Arquivo de backup não encontrado: $BACKUP_FILE"
  exit 1
fi

# Configurações do banco de dados
DB_NAME="cyberos_db"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"

# Confirmar restauração
echo "ATENÇÃO: Este processo irá substituir TODOS os dados no banco de dados '$DB_NAME'."
echo "O backup que será restaurado é: $BACKUP_FILE"
read -p "Deseja continuar? (s/n): " CONFIRM

if [ "$CONFIRM" != "s" ]; then
  echo "Operação cancelada pelo usuário."
  exit 0
fi

# Verificar se o banco de dados existe, senão criar
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME
if [ $? -ne 0 ]; then
  echo "Criando banco de dados $DB_NAME..."
  PGPASSWORD=$DB_PASSWORD createdb -h $DB_HOST -U $DB_USER $DB_NAME
  if [ $? -ne 0 ]; then
    echo "Erro ao criar o banco de dados. Verifique as credenciais e tente novamente."
    exit 1
  fi
else
  # Se o banco de dados existe, limpar todas as tabelas
  echo "Limpando banco de dados existente..."
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"
fi

# Restaurar o backup
echo "Iniciando restauração do banco de dados a partir de $BACKUP_FILE..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f "$BACKUP_FILE"

# Verificar se a restauração foi bem-sucedida
if [ $? -eq 0 ]; then
  echo "Restauração concluída com sucesso!"
else
  echo "Erro ao restaurar o backup. Verifique o arquivo de backup e tente novamente."
  exit 1
fi

echo "Banco de dados '$DB_NAME' restaurado com sucesso a partir de $BACKUP_FILE." 