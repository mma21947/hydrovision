// Função para obter o cookie por nome
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // O cookie tem o nome que estamos procurando?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Função para configurar cabeçalhos CSRF para solicitações AJAX
function setupCSRF() {
    const csrftoken = getCookie('csrftoken');
    
    // Se não tiver o token CSRF, tentar obter do elemento meta
    if (!csrftoken) {
        const tokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (tokenElement) {
            // Salvar como cookie para uso futuro
            document.cookie = `csrftoken=${tokenElement.value};path=/`;
        }
    }
    
    // Configurar todos os formulários para incluir o token CSRF
    document.querySelectorAll('form').forEach(form => {
        if (!form.querySelector('input[name="csrfmiddlewaretoken"]')) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'csrfmiddlewaretoken';
            input.value = csrftoken || getCookie('csrftoken');
            form.prepend(input);
        }
    });
    
    // Configurar AJAX para incluir o token CSRF no cabeçalho
    document.addEventListener('DOMContentLoaded', function() {
        // Para jQuery (se estiver usando)
        if (typeof $ !== 'undefined') {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken || getCookie('csrftoken'));
                    }
                }
            });
        }
        
        // Para fetch API
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (options.method && !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(options.method)) {
                if (!options.headers) {
                    options.headers = {};
                }
                
                // Se já for um objeto Headers, criar um novo com o mesmo conteúdo
                if (options.headers instanceof Headers) {
                    const originalHeaders = options.headers;
                    options.headers = new Headers(originalHeaders);
                    options.headers.append('X-CSRFToken', csrftoken || getCookie('csrftoken'));
                } else {
                    options.headers['X-CSRFToken'] = csrftoken || getCookie('csrftoken');
                }
            }
            return originalFetch(url, options);
        };
    });
}

// Chamar configuração quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', setupCSRF); 