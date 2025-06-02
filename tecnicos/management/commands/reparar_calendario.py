from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from tecnicos.models import Tecnico
from ordens.models import OrdemServico


class Command(BaseCommand):
    help = 'Diagnostica e repara problemas no calendário de técnicos'

    def add_arguments(self, parser):
        parser.add_argument('--tecnico_id', type=int, help='ID específico do técnico')
        parser.add_argument('--fix', action='store_true', help='Aplicar as correções sugeridas')
        parser.add_argument('--fix-schema', action='store_true', help='Corrigir problemas de esquema do banco de dados')

    def handle(self, *args, **options):
        tecnico_id = options.get('tecnico_id')
        aplicar_correcoes = options.get('fix', False)
        corrigir_schema = options.get('fix-schema', False)
        
        self.stdout.write(self.style.WARNING(
            'Iniciando diagnóstico do calendário de técnicos...'
            + (f' (Técnico ID: {tecnico_id})' if tecnico_id else '')
        ))
        
        # Verificar problemas de esquema primeiro
        if corrigir_schema:
            self.stdout.write(self.style.WARNING('Verificando problemas de esquema do banco de dados...'))
            try:
                self.corrigir_problemas_schema()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao corrigir esquema: {str(e)}'))
        
        # Obtém técnicos para diagnóstico
        if tecnico_id:
            tecnicos = Tecnico.objects.filter(id=tecnico_id)
            if not tecnicos.exists():
                self.stdout.write(self.style.ERROR(f'Técnico com ID {tecnico_id} não encontrado.'))
                return
        else:
            try:
                tecnicos = Tecnico.objects.filter(ativo=True)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao buscar técnicos ativos: {str(e)}'))
                # Tentar sem o filtro de ativo
                tecnicos = Tecnico.objects.all()
        
        self.stdout.write(f'Analisando {tecnicos.count()} técnico(s)...')
        
        total_problemas = 0
        total_correcoes = 0
        
        # Para cada técnico
        for tecnico in tecnicos:
            self.stdout.write(self.style.NOTICE(f'\nTécnico: {tecnico.nome_completo} (ID: {tecnico.id})'))
            
            # 1. Verificar se possui ordens de serviço
            ordens = OrdemServico.objects.filter(tecnico=tecnico)
            self.stdout.write(f'  Total de ordens: {ordens.count()}')
            
            # 2. Verificar ordens com problemas de data de agendamento
            ordens_sem_agendamento = ordens.filter(data_agendamento__isnull=True, status__in=['aberta', 'em_andamento'])
            if ordens_sem_agendamento.exists():
                total_problemas += ordens_sem_agendamento.count()
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️ {ordens_sem_agendamento.count()} ordens ativas sem data de agendamento'
                ))
                
                if aplicar_correcoes:
                    for ordem in ordens_sem_agendamento:
                        if ordem.data_abertura:
                            ordem.data_agendamento = ordem.data_abertura
                            ordem.save(update_fields=['data_agendamento'])
                            total_correcoes += 1
                            self.stdout.write(self.style.SUCCESS(
                                f'    ✅ Corrigida OS #{ordem.numero}: definida data de agendamento para {ordem.data_agendamento}'
                            ))
                        else:
                            self.stdout.write(self.style.ERROR(
                                f'    ❌ Não foi possível corrigir OS #{ordem.numero}: sem data de abertura'
                            ))
            
            # 3. Verificar ordens com problemas de cliente
            ordens_sem_cliente = ordens.filter(cliente__isnull=True)
            if ordens_sem_cliente.exists():
                total_problemas += ordens_sem_cliente.count()
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️ {ordens_sem_cliente.count()} ordens sem cliente associado'
                ))
                # Não aplicamos correção aqui, pois não temos como determinar o cliente correto
            
            # 4. Verificar localizações do técnico
            if tecnico.latitude is None or tecnico.longitude is None:
                total_problemas += 1
                self.stdout.write(self.style.WARNING(
                    '  ⚠️ Técnico sem coordenadas de localização'
                ))
            
            # 5. Verificar se o técnico tem slugs
            if not tecnico.slug:
                total_problemas += 1
                self.stdout.write(self.style.WARNING('  ⚠️ Técnico sem slug único'))
                
                if aplicar_correcoes:
                    # Usar o método save para gerar o slug
                    tecnico.save()
                    total_correcoes += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'    ✅ Gerado slug para o técnico: {tecnico.slug}'
                    ))
        
        # Resumo final
        self.stdout.write('\n' + self.style.NOTICE('Resumo do diagnóstico:'))
        self.stdout.write(f'Total de técnicos analisados: {tecnicos.count()}')
        self.stdout.write(f'Total de problemas encontrados: {total_problemas}')
        
        if aplicar_correcoes:
            self.stdout.write(f'Total de correções aplicadas: {total_correcoes}')
        else:
            self.stdout.write(self.style.WARNING(
                'Nenhuma correção foi aplicada. Use --fix para aplicar correções.'
            ))
        
        if not corrigir_schema:
            self.stdout.write(self.style.WARNING(
                'Verificação de esquema não foi realizada. Use --fix-schema para corrigir problemas de esquema.'
            ))
    
    def corrigir_problemas_schema(self):
        """Corrige problemas relacionados ao esquema do banco de dados"""
        try:
            with connection.cursor() as cursor:
                # Verificar se a coluna data_criacao existe na tabela tecnicos_tecnico
                cursor.execute("PRAGMA table_info(tecnicos_tecnico)")
                colunas = cursor.fetchall()
                colunas_dict = {col[1]: col for col in colunas}
                
                if 'data_criacao' not in colunas_dict:
                    self.stdout.write(self.style.WARNING('⚠️ Campo data_criacao não encontrado na tabela tecnicos_tecnico'))
                    
                    # Verificar se há alguma view ou consulta usando o campo
                    try:
                        with transaction.atomic():
                            # Solução 1: Adicionar o campo à tabela
                            self.stdout.write(self.style.NOTICE('Adicionando campo data_criacao à tabela tecnicos_tecnico...'))
                            cursor.execute("ALTER TABLE tecnicos_tecnico ADD COLUMN data_criacao timestamp NULL")
                            
                            # Inicializar com a data atual para registros existentes
                            data_atual = timezone.now().isoformat()
                            cursor.execute(f"UPDATE tecnicos_tecnico SET data_criacao = '{data_atual}'")
                            
                            self.stdout.write(self.style.SUCCESS('✅ Campo data_criacao adicionado com sucesso!'))
                    except Exception as e1:
                        self.stdout.write(self.style.ERROR(f'❌ Erro ao adicionar campo: {str(e1)}'))
                        
                        try:
                            # Solução 2: Se não conseguir adicionar o campo, tentar criar uma view
                            self.stdout.write(self.style.NOTICE('Tentando criar uma view para resolver o problema...'))
                            cursor.execute("""
                                CREATE VIEW IF NOT EXISTS vw_tecnicos AS
                                SELECT 
                                    *, 
                                    datetime('now') as data_criacao
                                FROM tecnicos_tecnico
                            """)
                            self.stdout.write(self.style.SUCCESS('✅ View criada com sucesso!'))
                        except Exception as e2:
                            self.stdout.write(self.style.ERROR(f'❌ Erro ao criar view: {str(e2)}'))
                else:
                    self.stdout.write(self.style.SUCCESS('✅ Campo data_criacao já existe na tabela tecnicos_tecnico'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar/corrigir esquema do banco de dados: {str(e)}')) 