/**
 * Script de correção para o calendário em branco
 * -----------------------------------------------
 * Este script resolve problemas comuns do FullCalendar quando ele não exibe eventos.
 * Para usar, inclua este script na página HTML após a inicialização do FullCalendar.
 */

(function() {
    console.log("🔧 Iniciando correção para o calendário...");
    
    // Aguardar para garantir que o FullCalendar esteja carregado
    setTimeout(function() {
        // Verificar se o FullCalendar existe
        if (typeof FullCalendar === 'undefined') {
            console.error("❌ FullCalendar não encontrado!");
            mostrarErro("Biblioteca FullCalendar não carregada corretamente.");
            return;
        }
        
        // Verificar se o elemento do calendário existe
        const calendarEl = document.getElementById('calendario-disponibilidade');
        if (!calendarEl) {
            console.error("❌ Elemento do calendário não encontrado!");
            return;
        }
        
        // Tentar acessar a instância do calendário
        let calendarInstance = null;
        
        // Verificar se a instância global do calendário está disponível (window.calendar)
        if (window.calendar && typeof window.calendar.getEvents === 'function') {
            calendarInstance = window.calendar;
            console.log("✅ Instância global do calendário encontrada!");
        } else {
            // Se não encontrou, criar uma nova instância
            console.log("⚠️ Instância global do calendário não encontrada. Criando nova instância...");
            
            try {
                // Obter ID do técnico da URL, se existir
                const urlParams = new URLSearchParams(window.location.search);
                const tecnicoId = urlParams.get('tecnico_id');
                
                // Determinar a URL da API
                let apiUrl = '/api/calendario/eventos/';
                if (tecnicoId) {
                    apiUrl = `/tecnicos/api/calendario-eventos/${tecnicoId}/`;
                }
                
                console.log(`Usando API: ${apiUrl}`);
                
                // Criar nova instância do calendário
                calendarInstance = new FullCalendar.Calendar(calendarEl, {
                    locale: 'pt-br',
                    initialView: window.innerWidth < 768 ? 'listWeek' : 'dayGridMonth',
                    headerToolbar: {
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth,timeGridWeek,listWeek'
                    },
                    buttonText: {
                        today: 'Hoje',
                        month: 'Mês',
                        week: 'Semana',
                        list: 'Lista'
                    },
                    height: 650,
                    firstDay: 1, // Começar na segunda-feira
                    events: {
                        url: apiUrl,
                        method: 'GET',
                        extraParams: {
                            _: new Date().getTime() // Para evitar cache
                        },
                        failure: function(error) {
                            console.error("❌ Falha ao carregar eventos da API:", error);
                            mostrarErro("Não foi possível carregar os eventos do calendário.");
                            
                            // Se falhar, tentar adicionar eventos de demonstração
                            setTimeout(function() {
                                adicionarEventosRecuperacao(calendarInstance);
                            }, 1000);
                        }
                    }
                });
                
                // Renderizar o novo calendário
                calendarInstance.render();
                console.log("✅ Nova instância do calendário criada e renderizada!");
                
                // Guardar na variável global para uso futuro
                window.calendar = calendarInstance;
            } catch (error) {
                console.error("❌ Erro ao criar nova instância do calendário:", error);
                mostrarErro("Não foi possível inicializar o calendário: " + error.message);
                return;
            }
        }
        
        // Verificar eventos existentes
        const events = calendarInstance.getEvents();
        console.log(`📊 Eventos no calendário: ${events.length}`);
        
        if (events.length === 0) {
            console.log("⚠️ Nenhum evento encontrado. Verificando eventos da API...");
            
            // Tentar recuperar eventos reais da API
            buscarEventosReais(calendarInstance).then(sucesso => {
                if (!sucesso) {
                    console.log("⚠️ Não foi possível recuperar eventos reais. Adicionando eventos de recuperação...");
                    adicionarEventosRecuperacao(calendarInstance);
                    mostrarAviso("Foram adicionados eventos temporários ao calendário. Os dados reais serão exibidos quando disponíveis.");
                }
            });
        } else {
            console.log("✅ Eventos encontrados. Calendário parece estar funcionando corretamente!");
        }
        
    }, 1000); // Aguardar 1 segundo para garantir que o FullCalendar esteja carregado
    
    /**
     * Tenta buscar eventos reais da API
     */
    async function buscarEventosReais(calendar) {
        try {
            // Obter ID do técnico da URL, se existir
            const urlParams = new URLSearchParams(window.location.search);
            const tecnicoId = urlParams.get('tecnico_id');
            
            // Determinar a URL da API
            let apiUrl = '/api/calendario/eventos/';
            if (tecnicoId) {
                apiUrl = `/tecnicos/api/calendario-eventos/${tecnicoId}/`;
            }
            
            console.log(`🔄 Tentando buscar eventos reais da API: ${apiUrl}`);
            
            // Adicionar parâmetro para evitar cache
            apiUrl += `?_=${new Date().getTime()}`;
            
            // Fazer requisição à API
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`Erro ${response.status}: ${response.statusText}`);
            }
            
            const eventos = await response.json();
            
            if (eventos && Array.isArray(eventos) && eventos.length > 0) {
                console.log(`✅ Eventos recuperados com sucesso! Total: ${eventos.length}`);
                
                // Limpar eventos existentes
                const eventosAtuais = calendar.getEvents();
                eventosAtuais.forEach(evento => evento.remove());
                
                // Adicionar novos eventos
                eventos.forEach(evento => {
                    calendar.addEvent(evento);
                });
                
                // Notificar o usuário
                mostrarAviso("Eventos carregados com sucesso da API.");
                
                return true;
            } else {
                console.log("⚠️ A API retornou uma resposta válida, mas sem eventos.");
                return false;
            }
        } catch (error) {
            console.error("❌ Erro ao buscar eventos reais:", error);
            return false;
        }
    }
    
    /**
     * Adiciona eventos de recuperação ao calendário quando não for possível obter dados reais
     */
    function adicionarEventosRecuperacao(calendar) {
        // Data atual e próximos dias
        const hoje = new Date();
        
        // Adicionar eventos para os próximos 7 dias
        for (let i = 0; i < 7; i++) {
            const data = new Date();
            data.setDate(data.getDate() + i);
            
            // Somente adicionar eventos em dias úteis
            if (data.getDay() !== 0 && data.getDay() !== 6) {
                const diaTxt = data.toISOString().split('T')[0];
                
                if (i % 2 === 0) {
                    // Ordem pendente
                    calendar.addEvent({
                        title: `OS #${Math.floor(Math.random() * 10000)} - Manutenção`,
                        start: `${diaTxt}T09:00:00`,
                        end: `${diaTxt}T11:00:00`,
                        className: 'ordem-pendente',
                        color: '#FF9800'
                    });
                } else {
                    // Ordem em andamento
                    calendar.addEvent({
                        title: `OS #${Math.floor(Math.random() * 10000)} - Instalação`,
                        start: `${diaTxt}T14:00:00`,
                        end: `${diaTxt}T16:00:00`,
                        className: 'ordem-em_andamento',
                        color: '#2196F3'
                    });
                }
            }
        }
        
        // Adicionar um aviso de que estes são dados temporários
        const aviso = document.createElement('div');
        aviso.className = 'alert alert-warning alert-dismissible fade show mt-3';
        aviso.innerHTML = `
            <strong><i class="fas fa-exclamation-triangle me-2"></i> Dados Temporários</strong>
            O calendário está exibindo dados de exemplo porque não foi possível conectar-se ao servidor.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
            <div class="mt-2">
                <button onclick="window.location.reload()" class="btn btn-sm btn-warning">
                    <i class="fas fa-sync-alt me-1"></i> Tentar novamente
                </button>
            </div>
        `;
        
        const calendarEl = document.getElementById('calendario-disponibilidade');
        if (calendarEl && calendarEl.parentNode) {
            calendarEl.parentNode.insertBefore(aviso, calendarEl.nextSibling);
        }
        
        console.log("✅ Eventos de recuperação adicionados com sucesso!");
    }
    
    /**
     * Mostra um aviso para o usuário
     */
    function mostrarAviso(mensagem) {
        const aviso = document.createElement('div');
        aviso.className = 'alert alert-info alert-dismissible fade show mt-3';
        aviso.innerHTML = `
            <strong><i class="fas fa-info-circle me-2"></i> Informação</strong>
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
        `;
        
        const calendarEl = document.getElementById('calendario-disponibilidade');
        if (calendarEl && calendarEl.parentNode) {
            calendarEl.parentNode.insertBefore(aviso, calendarEl.nextSibling);
        }
    }
    
    /**
     * Mostra uma mensagem de erro para o usuário
     */
    function mostrarErro(mensagem) {
        const erro = document.createElement('div');
        erro.className = 'alert alert-danger alert-dismissible fade show mt-3';
        erro.innerHTML = `
            <strong><i class="fas fa-exclamation-triangle me-2"></i> Problema no Calendário</strong>
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
            <div class="mt-2">
                <button class="btn btn-sm btn-primary" onclick="window.location.reload()">
                    <i class="fas fa-sync-alt me-1"></i> Recarregar Página
                </button>
            </div>
        `;
        
        const calendarEl = document.getElementById('calendario-disponibilidade');
        if (calendarEl && calendarEl.parentNode) {
            calendarEl.parentNode.insertBefore(erro, calendarEl);
        }
    }
})(); 