import os
import django
import sys
from datetime import datetime

# Configuração inicial do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cyberOS.settings")
django.setup()

# Importação das bibliotecas necessárias
from django.db import connection

def limpar_migracoes_duplicadas():
    """
    Remove as entradas duplicadas da migração 0004.
    """
    with connection.cursor() as cursor:
        print("Limpando migrações duplicadas...")
        
        # Encontrar as migrações 0004 duplicadas
        cursor.execute("SELECT id FROM django_migrations WHERE app = 'tecnicos' AND name = '0004_remove_tecnico_data_cadastro_and_more' ORDER BY id")
        registros = cursor.fetchall()
        
        if len(registros) <= 1:
            print("Não há duplicatas para limpar.")
            return
        
        # Remover todas as entradas exceto a primeira
        primeiro_id = registros[0][0]
        print(f"Mantendo a migração com ID {primeiro_id} e removendo {len(registros)-1} duplicatas.")
        
        # Excluir as duplicatas
        for registro in registros[1:]:
            cursor.execute(f"DELETE FROM django_migrations WHERE id = {registro[0]}")
            print(f"Excluído registro com ID {registro[0]}")
        
        print("Limpeza concluída.")

def registrar_nova_migracao():
    """
    Exclui a migração 0004_remove e adiciona a nova migração 0004_tecnico_data_campos.
    """
    with connection.cursor() as cursor:
        # Remover qualquer migração 0004_remove
        cursor.execute("DELETE FROM django_migrations WHERE app = 'tecnicos' AND name = '0004_remove_tecnico_data_cadastro_and_more'")
        rows_deleted = cursor.rowcount
        print(f"Removidas {rows_deleted} migração(ões) 0004_remove_tecnico_data_cadastro_and_more")
        
        # Verificar se a nova migração já existe
        cursor.execute("SELECT id FROM django_migrations WHERE app = 'tecnicos' AND name = '0004_tecnico_data_campos'")
        if cursor.fetchone():
            print("Migração 0004_tecnico_data_campos já existe no banco de dados.")
            return
        
        # Inserir a nova migração
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = f"INSERT INTO django_migrations (app, name, applied) VALUES ('tecnicos', '0004_tecnico_data_campos', '{now}')"
        cursor.execute(sql)
        print(f"Nova migração 0004_tecnico_data_campos adicionada com data {now}")

def listar_migracoes_tecnicos():
    """
    Lista as migrações registradas do app tecnicos.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, app, name, applied FROM django_migrations WHERE app = 'tecnicos' ORDER BY id")
        print("\nMigrações do app tecnicos:")
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, App: {row[1]}, Nome: {row[2]}, Aplicada em: {row[3]}")

if __name__ == "__main__":
    print("Iniciando correção automática das migrações...")
    listar_migracoes_tecnicos()
    
    # Executar ambas as funções automaticamente
    limpar_migracoes_duplicadas()
    registrar_nova_migracao()
    
    print("\nMigrações após correções:")
    listar_migracoes_tecnicos()
    print("Processo concluído.") 