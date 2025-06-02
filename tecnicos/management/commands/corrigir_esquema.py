from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Corrige problemas de esquema do banco de dados para o calendário'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando correção de esquema do banco de dados...'))
        
        try:
            self.corrigir_data_criacao()
            self.stdout.write(self.style.SUCCESS('\n✅ Correção de esquema concluída.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro durante a correção do esquema: {str(e)}'))
    
    def corrigir_data_criacao(self):
        """Corrige especificamente o problema com o campo data_criacao"""
        with connection.cursor() as cursor:
            self.stdout.write(self.style.NOTICE('Verificando tabela tecnicos_tecnico...'))
            
            # Verificar se a tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tecnicos_tecnico'")
            if not cursor.fetchone():
                self.stdout.write(self.style.ERROR('❌ Tabela tecnicos_tecnico não encontrada!'))
                return False
            
            # Verificar se a coluna data_criacao existe
            cursor.execute("PRAGMA table_info(tecnicos_tecnico)")
            colunas = cursor.fetchall()
            colunas_dict = {col[1]: col for col in colunas}
            
            self.stdout.write(self.style.NOTICE(f'Colunas encontradas: {", ".join(colunas_dict.keys())}'))
            
            if 'data_criacao' in colunas_dict:
                self.stdout.write(self.style.SUCCESS('✅ Campo data_criacao já existe na tabela.'))
                return True
            
            self.stdout.write(self.style.WARNING('⚠️ Campo data_criacao não encontrado.'))
            
            # Adicionar o campo data_criacao
            self.stdout.write(self.style.NOTICE('Adicionando campo data_criacao à tabela...'))
            
            try:
                cursor.execute("ALTER TABLE tecnicos_tecnico ADD COLUMN data_criacao timestamp NULL")
                
                # Preencher com valores padrão
                data_atual = timezone.now().isoformat()
                cursor.execute(f"UPDATE tecnicos_tecnico SET data_criacao = '{data_atual}'")
                
                self.stdout.write(self.style.SUCCESS('✅ Campo data_criacao adicionado com sucesso!'))
                return True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erro ao adicionar campo: {str(e)}'))
                
                # Solução alternativa - criar uma view
                self.stdout.write(self.style.NOTICE('Tentando solução alternativa: criando uma view...'))
                
                try:
                    cursor.execute("DROP VIEW IF EXISTS vw_tecnicos_com_data_criacao")
                    cursor.execute("""
                        CREATE VIEW vw_tecnicos_com_data_criacao AS
                        SELECT 
                            *, 
                            datetime('now') as data_criacao
                        FROM tecnicos_tecnico
                    """)
                    
                    self.stdout.write(self.style.SUCCESS(
                        '✅ View vw_tecnicos_com_data_criacao criada com sucesso!'
                    ))
                    
                    # Atualizar as consultas que estão procurando por esse campo
                    self.stdout.write(self.style.NOTICE(
                        'Para aplicativos que usam este campo, você deve atualizar suas consultas '
                        'para usar a view vw_tecnicos_com_data_criacao em vez da tabela tecnicos_tecnico.'
                    ))
                    
                    return True
                except Exception as e2:
                    self.stdout.write(self.style.ERROR(f'❌ Erro ao criar view: {str(e2)}'))
                    return False 