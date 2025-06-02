// Script de emergência para consertar o calendário em branco
(function() {
    console.log('🔧 Script de emergência para o calendário (v2 - com interações)');
    
    // Executar após o carregamento completo da página
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(inicializarCalendario, 500);
    });
    
    // Se a página já estiver carregada, executar imediatamente
    if (document.readyState === 'complete') {
        setTimeout(inicializarCalendario, 500);
    }
    
    function inicializarCalendario() {
        try {
            // Verificar se o elemento do calendário existe
            const calendario = document.getElementById('calendario-disponibilidade');
            if (!calendario) {
                console.error('❌ Elemento do calendário não encontrado!');
                return;
            }
            
            // Verificar se o FullCalendar foi carregado
            if (typeof FullCalendar === 'undefined') {
                console.error('❌ Biblioteca FullCalendar não carregada!');
                adicionarScriptsFullCalendar();
                return;
            }
            
            // Ocultar o loader se existir
            const loader = document.getElementById('calendario-loader');
            if (loader) {
                loader.style.display = 'none';
            }
            
            console.log('✅ Iniciando calendário de emergência...');
            
            // Criar eventos de exemplo
            const hoje = new Date();
            const eventos = [];
            
            // Adicionar eventos para os próximos 7 dias
            for (let i = 0; i < 7; i++) {
                const data = new Date();
                data.setDate(data.getDate() + i);
                const dataFormatada = data.toISOString().split('T')[0];
                
                // Adicionar apenas nos dias úteis (1-5 = seg-sex)
                if (data.getDay() >= 1 && data.getDay() <= 5) {
                    if (i % 2 === 0) {
                        eventos.push({
                            id: `os-${1000 + i}`,
                            title: `OS #${Math.floor(1000 + Math.random() * 9000)} - Manutenção`,
                            start: `${dataFormatada}T09:00:00`,
                            end: `${dataFormatada}T11:00:00`,
                            className: 'ordem-pendente',
                            color: '#FF9800',
                            extendedProps: {
                                tipo: 'manutenção',
                                status: 'pendente'
                            }
                        });
                    } else {
                        eventos.push({
                            id: `os-${2000 + i}`,
                            title: `OS #${Math.floor(1000 + Math.random() * 9000)} - Instalação`,
                            start: `${dataFormatada}T14:00:00`,
                            end: `${dataFormatada}T16:00:00`,
                            className: 'ordem-em_andamento',
                            color: '#2196F3',
                            extendedProps: {
                                tipo: 'instalação',
                                status: 'em_andamento'
                            }
                        });
                    }
                }
            }
            
            // Adicionar evento de férias
            const proximoMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 1);
            eventos.push({
                id: 'ferias-1',
                title: 'Férias Programadas',
                start: proximoMes.toISOString().split('T')[0],
                end: new Date(proximoMes.getFullYear(), proximoMes.getMonth(), 15).toISOString().split('T')[0],
                className: 'ferias',
                color: '#FFCA28',
                allDay: true,
                extendedProps: {
                    tipo: 'férias',
                    status: 'aprovado'
                }
            });
            
            // Criar o calendário
            const calendar = new FullCalendar.Calendar(calendario, {
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
                events: eventos,
                
                // Adicionar opções de interação
                selectable: true,
                selectMirror: true,
                unselectAuto: true,
                
                // Adicionar tooltips para eventos
                eventDidMount: function(info) {
                    // Adicionar tooltip usando Bootstrap se disponível
                    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                        new bootstrap.Tooltip(info.el, {
                            title: info.event.title,
                            placement: 'top',
                            container: 'body'
                        });
                    }
                },
                
                // Manipular clique em datas (seleção)
                select: function(info) {
                    const dataFormatada = new Date(info.start).toLocaleDateString('pt-BR', {
                        weekday: 'long',
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric'
                    });
                    
                    // Verificar se o Sweet Alert está disponível
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            title: 'Adicionar Atividade',
                            html: `
                                <p>Data selecionada: <strong>${dataFormatada}</strong></p>
                                <div class="mt-4">
                                    <a href="#" onclick="adicionarNovaOrdem('${info.startStr}')" class="btn btn-primary">
                                        <i class="fas fa-clipboard-list me-2"></i> Nova Ordem de Serviço
                                    </a>
                                </div>
                            `,
                            icon: 'info',
                            showCancelButton: true,
                            cancelButtonText: 'Cancelar',
                            showConfirmButton: false
                        });
                    } else {
                        // Usar prompt nativo se o SweetAlert não estiver disponível
                        if (confirm(`Deseja adicionar uma atividade para o dia ${dataFormatada}?`)) {
                            alert('Esta é uma versão de demonstração. Em um ambiente real, você seria redirecionado para a página de criação de ordens de serviço.');
                        }
                    }
                    
                    calendar.unselect();
                },
                
                // Manipular clique em eventos
                eventClick: function(info) {
                    // Extrair dados do evento
                    const evento = info.event;
                    const titulo = evento.title;
                    const inicio = evento.start ? new Date(evento.start).toLocaleString('pt-BR') : 'Não definido';
                    const fim = evento.end ? new Date(evento.end).toLocaleString('pt-BR') : 'Não definido';
                    const tipo = evento.extendedProps?.tipo || 'Não especificado';
                    const status = evento.extendedProps?.status || 'Não especificado';
                    
                    // Mostrar detalhes do evento
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            title: titulo,
                            html: `
                                <div class="text-start">
                                    <p><strong>Início:</strong> ${inicio}</p>
                                    <p><strong>Fim:</strong> ${fim}</p>
                                    <p><strong>Tipo:</strong> ${tipo}</p>
                                    <p><strong>Status:</strong> <span class="status-badge status-${status}">${status}</span></p>
                                </div>
                            `,
                            icon: 'info',
                            showCancelButton: true,
                            confirmButtonText: 'Ver Detalhes',
                            cancelButtonText: 'Fechar'
                        }).then((result) => {
                            if (result.isConfirmed) {
                                alert('Esta é uma versão de demonstração. Em um ambiente real, você seria redirecionado para a página de detalhes da ordem de serviço.');
                            }
                        });
                    } else {
                        // Usar alert nativo se o SweetAlert não estiver disponível
                        alert(`Detalhes do Evento:\nTítulo: ${titulo}\nInício: ${inicio}\nFim: ${fim}\nTipo: ${tipo}\nStatus: ${status}`);
                    }
                }
            });
            
            // Renderizar o calendário
            calendar.render();
            console.log('✅ Calendário de emergência renderizado com sucesso!');
            
            // Salvar o calendário na variável global
            window.calendar = calendar;
            
            // Função global para adicionar nova ordem
            window.adicionarNovaOrdem = function(dataStr) {
                alert(`Esta é uma versão de demonstração. Em um ambiente real, você seria redirecionado para a página de criação de ordens de serviço para a data ${dataStr}.`);
            };
            
            // Mostrar mensagem de calendário em modo demo
            const mensagem = document.createElement('div');
            mensagem.className = 'alert alert-info alert-dismissible fade show mt-3';
            mensagem.innerHTML = `
                <strong><i class="fas fa-info-circle me-2"></i> Modo de Compatibilidade</strong>
                O calendário está exibindo eventos de demonstração com interação habilitada.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
            `;
            
            calendario.parentNode.insertBefore(mensagem, calendario.nextSibling);
            
        } catch (erro) {
            console.error('❌ Erro ao inicializar o calendário:', erro);
            mostrarErro('Ocorreu um erro ao inicializar o calendário: ' + erro.message);
        }
    }
    
    function mostrarErro(mensagem) {
        const calendario = document.getElementById('calendario-disponibilidade');
        if (!calendario) return;
        
        const erro = document.createElement('div');
        erro.className = 'alert alert-danger mt-3';
        erro.innerHTML = `
            <h4 class="alert-heading"><i class="fas fa-exclamation-triangle me-2"></i> Erro no calendário</h4>
            <p>${mensagem}</p>
            <hr>
            <button onclick="window.location.reload()" class="btn btn-sm btn-danger">
                <i class="fas fa-sync-alt me-1"></i> Recarregar página
            </button>
        `;
        
        calendario.parentNode.insertBefore(erro, calendario);
    }
    
    function adicionarScriptsFullCalendar() {
        // Adicionar a biblioteca FullCalendar se não estiver presente
        const scripts = [
            'https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.js',
            'https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/locales-all.min.js'
        ];
        
        const links = [
            'https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.css'
        ];
        
        // Adicionar CSS
        links.forEach(url => {
            if (!document.querySelector(`link[href="${url}"]`)) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = url;
                document.head.appendChild(link);
            }
        });
        
        // Adicionar scripts
        let contador = 0;
        scripts.forEach(url => {
            if (!document.querySelector(`script[src="${url}"]`)) {
                const script = document.createElement('script');
                script.src = url;
                script.onload = function() {
                    contador++;
                    if (contador === scripts.length) {
                        console.log('✅ Bibliotecas FullCalendar carregadas com sucesso!');
                        setTimeout(inicializarCalendario, 500);
                    }
                };
                document.body.appendChild(script);
            }
        });
        
        // Mostrar mensagem de carregamento
        const calendario = document.getElementById('calendario-disponibilidade');
        if (calendario) {
            calendario.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <h5>Carregando bibliotecas necessárias...</h5>
                    <p class="text-muted">Por favor, aguarde um momento.</p>
                </div>
            `;
        }
    }
})(); 