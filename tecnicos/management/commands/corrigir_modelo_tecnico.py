from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

class Command(BaseCommand):
    help = 'Corrige o modelo Tecnico adicionando os campos data_criacao e data_atualizacao diretamente no banco de dados'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando correção do modelo Tecnico...'))
        
        with transaction.atomic():
            # Verificar se os campos já existem
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(tecnicos_tecnico)")
            colunas = [coluna[1] for coluna in cursor.fetchall()]
            
            self.stdout.write(f"Colunas existentes: {', '.join(colunas)}")
            
            # Lista de SQL para executar
            sql_commands = []
            
            # Verificar se precisa adicionar os campos (permitindo NULL)
            if 'data_criacao' not in colunas:
                self.stdout.write(self.style.WARNING('Adicionando campo data_criacao...'))
                sql_commands.append(
                    "ALTER TABLE tecnicos_tecnico ADD COLUMN data_criacao datetime NULL;"
                )
            
            if 'data_atualizacao' not in colunas:
                self.stdout.write(self.style.WARNING('Adicionando campo data_atualizacao...'))
                sql_commands.append(
                    "ALTER TABLE tecnicos_tecnico ADD COLUMN data_atualizacao datetime NULL;"
                )
            
            # Verificar se precisa remover campos antigos
            if 'data_cadastro' in colunas:
                self.stdout.write(self.style.WARNING('Removendo campo data_cadastro...'))
                sql_commands.append(
                    "ALTER TABLE tecnicos_tecnico DROP COLUMN data_cadastro;"
                )
            
            if 'ultima_atualizacao' in colunas:
                self.stdout.write(self.style.WARNING('Removendo campo ultima_atualizacao...'))
                sql_commands.append(
                    "ALTER TABLE tecnicos_tecnico DROP COLUMN ultima_atualizacao;"
                )
            
            # Executar os comandos SQL
            for sql in sql_commands:
                try:
                    cursor.execute(sql)
                    self.stdout.write(self.style.SUCCESS(f'Executado com sucesso: {sql}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao executar {sql}: {str(e)}'))
            
            # Recarregar colunas após alterações
            cursor.execute("PRAGMA table_info(tecnicos_tecnico)")
            colunas_atuais = [coluna[1] for coluna in cursor.fetchall()]
            
            # Atualizar os campos com a data atual para registros existentes
            if 'data_criacao' in colunas_atuais:
                self.stdout.write(self.style.WARNING('Atualizando campo data_criacao para todos os registros...'))
                now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cursor.execute(f"UPDATE tecnicos_tecnico SET data_criacao = '{now}' WHERE data_criacao IS NULL")
                    self.stdout.write(self.style.SUCCESS('Campo data_criacao atualizado.'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao atualizar data_criacao: {str(e)}'))
            
            if 'data_atualizacao' in colunas_atuais:
                self.stdout.write(self.style.WARNING('Atualizando campo data_atualizacao para todos os registros...'))
                now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cursor.execute(f"UPDATE tecnicos_tecnico SET data_atualizacao = '{now}' WHERE data_atualizacao IS NULL")
                    self.stdout.write(self.style.SUCCESS('Campo data_atualizacao atualizado.'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao atualizar data_atualizacao: {str(e)}'))
            
            # Mostrar as colunas atuais
            cursor.execute("PRAGMA table_info(tecnicos_tecnico)")
            colunas_atuais = cursor.fetchall()
            self.stdout.write(self.style.SUCCESS('\nColunas atuais da tabela tecnicos_tecnico:'))
            for coluna in colunas_atuais:
                self.stdout.write(f"  {coluna[1]} ({coluna[2]})")
                
        # Marcar a migração 0004 como aplicada manualmente no registro de migrações
        self.stdout.write(self.style.WARNING('\nAtualizando o registro de migrações...'))
        try:
            with connection.cursor() as cursor:
                now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    f"INSERT INTO django_migrations (app, name, applied) VALUES ('tecnicos', '0004_remove_tecnico_data_cadastro_and_more', '{now}')"
                )
            self.stdout.write(self.style.SUCCESS('Migração 0004_remove_tecnico_data_cadastro_and_more marcada como aplicada.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao marcar a migração como aplicada: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('Correção do modelo Tecnico concluída com sucesso!')) 