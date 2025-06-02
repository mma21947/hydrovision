from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages

def custom_logout_view(request):
    """
    View personalizada para logout sem dependências da view padrão do Django.
    Agora redireciona para /sair/ para garantir uso da rota correta.
    """
    # Se for uma requisição GET, redirecionar para /sair/
    if request.method == 'GET':
        return redirect('sair')
        
    # Realizar logout
    logout(request)
    
    # Adicionar mensagem de confirmação
    messages.success(request, 'Você foi desconectado com sucesso.')
    
    # Renderizar página de logout diretamente
    return render(request, 'logout.html')

def sair_view(request):
    """
    View específica para a rota /sair/
    Funciona exatamente como a view de logout
    """
    # Realizar logout
    logout(request)
    
    # Adicionar mensagem de confirmação
    messages.success(request, 'Você foi desconectado com sucesso.')
    
    # Renderizar página de logout diretamente
    return render(request, 'logout.html') 