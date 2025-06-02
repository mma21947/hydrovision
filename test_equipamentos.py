import os
import sys
import django

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyberOS.settings')
django.setup()

# Importar após configurar o ambiente
from equipamentos.models import Equipamento
from clientes.models import Cliente
from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from equipamentos.views import equipamentos_cliente

# Criamos uma classe para simular uma requisição HTTP com um usuário autenticado
class AuthenticatedHttpRequest(HttpRequest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = User.objects.first()  # Pega o primeiro usuário do sistema
        self.headers = {'X-Requested-With': 'XMLHttpRequest'}

def test_equipamentos_cliente(cliente_id):
    # Verificar se o cliente existe
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        print(f"Cliente encontrado: {cliente.nome} (ID: {cliente.id})")
        
        # Verificar quantos equipamentos o cliente tem
        equipamentos = Equipamento.objects.filter(cliente=cliente)
        print(f"Total de equipamentos do cliente: {equipamentos.count()}")
        
        for eq in equipamentos:
            print(f"- {eq.codigo} - {eq.nome} - {eq.status}")
        
        # Criar uma requisição simulada
        request = AuthenticatedHttpRequest()
        
        # Se não houver usuário cadastrado, vai falhar
        if not request.user:
            print("ERRO: Não há usuários cadastrados no sistema!")
            return
        
        print(f"\nTestando a view equipamentos_cliente com cliente_id={cliente_id}...")
        
        # Chamar a view
        try:
            response = equipamentos_cliente(request, cliente_id)
            print(f"Status code: {response.status_code}")
            
            if hasattr(response, 'content'):
                try:
                    # Tentar interpretar como JSON primeiro
                    import json
                    json_content = json.loads(response.content)
                    print("Resposta JSON completa:")
                    import pprint
                    pprint.pprint(json_content)
                except json.JSONDecodeError:
                    # Se não for JSON, mostrar como texto
                    print(f"Conteúdo da resposta: {response.content[:500]}...")
            else:
                print("Resposta não tem conteúdo direto.")
                
            return response
        except Exception as e:
            print(f"ERRO ao executar a view: {str(e)}")
            import traceback
            traceback.print_exc()
    
    except Cliente.DoesNotExist:
        print(f"Cliente com ID {cliente_id} não existe.")
    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Pega o id do cliente da linha de comando ou usa o default 2
    cliente_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    test_equipamentos_cliente(cliente_id) 