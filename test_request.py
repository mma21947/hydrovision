import requests
import json

def test_equipamentos_cliente_url(cliente_id, base_url="http://localhost:8000", username="admin", password="admin"):
    """
    Testa a URL dos equipamentos do cliente usando uma requisição HTTP real, com autenticação.
    """
    # Criar uma sessão para manter os cookies
    session = requests.Session()
    
    # Primeiro vamos acessar a página de login para obter o token CSRF
    login_url = f"{base_url}/admin/login/"
    
    print(f"Obtendo token CSRF de: {login_url}")
    login_page = session.get(login_url)
    
    # Extrair o token CSRF (pode variar dependendo de como o Django está configurado)
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']
        print(f"Token CSRF obtido: {csrf_token}")
    else:
        print("CSRF token não encontrado nos cookies.")
        # Tentar extrair do corpo da página como fallback
        import re
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
        if match:
            csrf_token = match.group(1)
            print(f"Token CSRF extraído do HTML: {csrf_token}")
        else:
            print("CSRF token não encontrado. Tentando login sem token...")
            csrf_token = None
    
    # Fazer login
    login_data = {
        'username': username,
        'password': password,
    }
    
    if csrf_token:
        login_data['csrfmiddlewaretoken'] = csrf_token
        headers = {'Referer': login_url, 'X-CSRFToken': csrf_token}
    else:
        headers = {'Referer': login_url}
    
    print(f"Tentando login como: {username}")
    login_response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
    
    if login_response.status_code == 200 and "authentication failed" in login_response.text.lower():
        print("Falha na autenticação. Verifique o usuário e senha.")
        return None
    
    print(f"Login concluído com status: {login_response.status_code}")
    
    # Agora vamos acessar a URL dos equipamentos do cliente
    url = f"{base_url}/equipamentos/cliente/{cliente_id}/"
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    
    print(f"Fazendo requisição para: {url}")
    
    try:
        response = session.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print("Resposta JSON:")
                print(json.dumps(json_data, indent=2, ensure_ascii=False))
                return json_data
            except json.JSONDecodeError:
                print("Não foi possível decodificar a resposta como JSON.")
                print(f"Conteúdo: {response.text[:500]}...")
        else:
            print(f"Resposta com erro {response.status_code}:")
            print(response.text[:500])
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a requisição: {str(e)}")
        
    return None

if __name__ == "__main__":
    import sys
    cliente_id = sys.argv[1] if len(sys.argv) > 1 else 2
    test_equipamentos_cliente_url(cliente_id) 