from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import Perfil
from tecnicos.models import Tecnico
import datetime

class Command(BaseCommand):
    help = 'Sincroniza usuários com perfil de técnico com a tabela de Tecnico'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando sincronização de técnicos...'))
        
        # Buscar todos os perfis do tipo 'tecnico'
        perfis_tecnicos = Perfil.objects.filter(tipo='tecnico')
        self.stdout.write(f'Encontrados {perfis_tecnicos.count()} usuários com perfil de técnico')
        
        # Contador para estatísticas
        criados = 0
        ja_existentes = 0
        erros = 0
        
        # Processar cada perfil
        for perfil in perfis_tecnicos:
            usuario = perfil.user
            self.stdout.write(f'Processando usuário: {usuario.username}')
            
            # Verificar se já existe um técnico para este usuário
            try:
                Tecnico.objects.get(usuario=usuario)
                self.stdout.write(self.style.WARNING(f'Técnico já existe para o usuário {usuario.username}'))
                ja_existentes += 1
                continue
            except Tecnico.DoesNotExist:
                # Não existe, vamos criar um técnico básico
                try:
                    # Gerar um código para o técnico (TEC + ID do usuário)
                    codigo = f"TEC{usuario.id:04d}"
                    
                    # Obter dados básicos do usuário
                    nome_completo = f"{usuario.first_name} {usuario.last_name}".strip()
                    if not nome_completo:
                        nome_completo = usuario.username
                        
                    # Criar técnico com dados básicos
                    tecnico = Tecnico(
                        usuario=usuario,
                        codigo=codigo,
                        nome_completo=nome_completo,
                        cpf="000.000.000-00",  # CPF temporário
                        data_nascimento=datetime.date.today(),  # Data temporária
                        celular="(00) 00000-0000",  # Celular temporário
                        email=usuario.email,
                        endereco="Endereço não informado",
                        numero="S/N",
                        bairro="Bairro não informado",
                        cidade="Cidade não informada",
                        estado="SP",
                        cep="00000-000",
                        data_admissao=datetime.date.today(),
                        nivel="junior"
                    )
                    tecnico.save()
                    self.stdout.write(self.style.SUCCESS(f'Técnico criado com sucesso para o usuário {usuario.username}'))
                    criados += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao criar técnico para o usuário {usuario.username}: {str(e)}'))
                    erros += 1
        
        # Apresentar estatísticas
        self.stdout.write(self.style.SUCCESS(f'Sincronização concluída.'))
        self.stdout.write(f'  - Técnicos já existentes: {ja_existentes}')
        self.stdout.write(f'  - Técnicos criados: {criados}')
        self.stdout.write(f'  - Erros: {erros}') 