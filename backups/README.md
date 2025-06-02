# Backup e Restauração do Banco de Dados

Este diretório contém backups do banco de dados PostgreSQL do CyberOS.

## Instruções de Backup

Para criar um novo backup do banco de dados, execute:

```bash
./scripts/backup_db.sh
```

Este comando criará um arquivo SQL com todos os dados do banco, nomeado com data e hora (por exemplo, `backup_cyberos_db_20250430_104413.sql`).

## Instruções de Restauração

Para restaurar um backup em um novo servidor ou na mesma máquina:

1. Certifique-se de que o PostgreSQL está instalado e em execução
2. Execute o script de restauração, fornecendo o caminho para o arquivo de backup:

```bash
./scripts/restore_db.sh ./backups/nome_do_arquivo_de_backup.sql
```

Por exemplo:
```bash
./scripts/restore_db.sh ./backups/backup_cyberos_db_20250430_104413.sql
```

## Configuração Manual

Se preferir fazer o processo manualmente:

### Backup Manual

```bash
PGPASSWORD=postgres pg_dump -h localhost -U postgres -d cyberos_db -f backup_manual.sql
```

### Restauração Manual

1. Crie o banco de dados (se ainda não existir):
```bash
PGPASSWORD=postgres createdb -h localhost -U postgres cyberos_db
```

2. Restaure o backup:
```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d cyberos_db -f arquivo_de_backup.sql
```

### Configuração no settings.py

Certifique-se de que o arquivo `settings.py` esteja configurado corretamente:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cyberos_db',
        'USER': 'postgres',  # Ajuste conforme necessário
        'PASSWORD': 'postgres',  # Ajuste conforme necessário
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
``` 