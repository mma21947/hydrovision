/**
 * Calendário para a página de detalhes do técnico
 * -----------------------------------------------
 * Este script implementa um calendário completo usando FullCalendar
 * para substituir a visualização simplificada na página de detalhes do técnico.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos na página de detalhes do técnico
    const calendarioSimplificado = document.getElementById('calendario-alternativo');
    if (!calendarioSimplificado) return;
    
    console.log('🔄 Inicializando calendário completo para técnico...');
    
    // Obter ID do técnico da URL ou dos dados da página
    const urlAtual = window.location.pathname;
    let idTecnico = '';
    
    // Tentar obter da variável global (se definida no template)
    if (typeof tecnicoData !== 'undefined' && tecnicoData.id) {
        idTecnico = tecnicoData.id;
        console.log(`✅ ID do técnico obtido de tecnicoData: ${idTecnico}`);
    } else if (document.getElementById('tecnico-id')) {
        idTecnico = document.getElementById('tecnico-id').value;
        console.log(`✅ ID do técnico obtido de elemento HTML: ${idTecnico}`);
    } else {
        // Tentar extrair da URL
        const match = urlAtual.match(/\/detalhe\/([^\/]+)/);
        if (match && match[1]) {
            idTecnico = 'slug:' + match[1];
            console.log(`✅ ID do técnico obtido da URL: ${idTecnico}`);
        }
    }
    
    if (!idTecnico) {
        console.error('❌ Não foi possível determinar o ID do técnico');
        mostrarAlerta('danger', 
            `<strong><i class="fas fa-exclamation-triangle me-2"></i> Erro</strong> ` +
            `Não foi possível determinar o ID do técnico. Verifique seu login e permissões.`
        );
        return;
    }
    
    // Verificar dependências
    if (typeof FullCalendar === 'undefined') {
        console.error('❌ Biblioteca FullCalendar não encontrada!');
        return;
    }
    
    // Criar container para o calendário completo
    const containerCalendario = document.createElement('div');
    containerCalendario.id = 'calendario';
    
    // Inserir antes da tabela
    const tabelaContainer = calendarioSimplificado.querySelector('.table-responsive');
    if (tabelaContainer) {
        calendarioSimplificado.insertBefore(containerCalendario, tabelaContainer);
    } else {
        calendarioSimplificado.appendChild(containerCalendario);
    }
    
    // Definir a URL da API com base no ID do técnico
    let apiUrl = '';
    const apiUrlsAlternativas = [];
    
    if (idTecnico.startsWith('slug:')) {
        // Usar endpoint de slug
        const slug = idTecnico.replace('slug:', '');
        apiUrl = `/tecnicos/api/calendario-eventos/slug/${slug}/`;
        
        // APIs alternativas caso a principal não funcione
        apiUrlsAlternativas.push(
            `/api/tecnicos/calendario-eventos/slug/${slug}/`,
            `/api/calendario/eventos/slug/${slug}/`,
            `/tecnicos/calendario/eventos/slug/${slug}/`
        );
    } else {
        // Usar endpoint de ID
        apiUrl = `/tecnicos/calendario/eventos/${idTecnico}/`;
        
        // URLs alternativas com diferentes formatos
        apiUrlsAlternativas.push(
            `/tecnicos/api/calendario-eventos/${idTecnico}/`,
            `/api/calendario-eventos/${idTecnico}/`,
            `/api/tecnicos/calendario-eventos/${idTecnico}/`,
            `/tecnicos/ordens/${idTecnico}/`,
            `/api/ordens/tecnico/${idTecnico}/`,
            `/ordens/api/tecnico/${idTecnico}/`,
            `/ordens/api/agendamentos/tecnico/${idTecnico}/`,
            `/api/ordens/agendadas/tecnico/${idTecnico}/`
        );
    }
    
    console.log(`🔄 URL da API: ${apiUrl}`);
    console.log(`🔄 URLs alternativas: ${apiUrlsAlternativas.length} opções configuradas`);
    
    // Inicializar o calendário com opções avançadas de tratamento de falhas
    const opcoesCalendario = {
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },
        initialView: 'dayGridMonth',
        height: 550,
        nowIndicator: true,
        navLinks: true,
        editable: false,
        dayMaxEvents: false,
        locale: 'pt-br',
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5], // Segunda a sexta
            startTime: '08:00',
            endTime: '18:00',
        },
        timeZone: 'local',
        slotMinTime: '07:00:00',
        slotMaxTime: '22:00:00',
        slotDuration: '00:30:00',
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        },
        buttonText: {
            today: 'Hoje',
            month: 'Mês',
            week: 'Semana',
            day: 'Dia',
            list: 'Lista'
        },
        allDayText: 'Dia todo',
        noEventsText: 'Nenhum evento para exibir',
        
        events: {
            url: apiUrl,
            method: 'GET',
            withCredentials: true, // Enviar cookies com a requisição
            extraParams: {
                _: new Date().getTime() // Sempre usar timestamp atual para evitar cache
            },
            success: function(eventos) {
                console.log(`✅ ${eventos.length} eventos recebidos da API (${apiUrl})`);
                
                // Remover a mensagem de carregamento
                const alertasCarregamento = document.querySelectorAll('.alerta-calendario');
                alertasCarregamento.forEach(alerta => alerta.remove());
                
                // Mostrar número de eventos carregados
                if (eventos.length > 0) {
                    mostrarAlerta('success', 
                        `<strong><i class="fas fa-calendar-check me-2"></i> Dados carregados</strong> ` +
                        `${eventos.length} compromisso(s) encontrado(s) para este técnico.`
                    );
                } else {
                    mostrarAlerta('info', 
                        `<strong><i class="fas fa-calendar me-2"></i> Calendário vazio</strong> ` +
                        `Não há compromissos agendados para este técnico.`
                    );
                }
            },
            failure: function(error) {
                console.error('❌ Falha ao carregar eventos do calendário da API principal:', error);
                
                // Tentar APIs alternativas
                carregarEventosReais(0);
            }
        },
        
        // Configurações de interação
        eventDidMount: function(info) {
            // Adicionar tooltip usando Bootstrap
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                new bootstrap.Tooltip(info.el, {
                    title: info.event.title,
                    placement: 'top',
                    container: 'body'
                });
            }
        },
        
        // Estilização de eventos
        eventClassNames: function(arg) {
            return ['rounded', 'border-0', 'py-1', 'px-2'];
        },
        
        // Responsivo
        windowResize: function(view) {
            if (window.innerWidth < 768) {
                calendar.changeView('listWeek');
            } else {
                calendar.changeView('dayGridMonth');
            }
            // Forçar atualização do tamanho do calendário após o redimensionamento
            setTimeout(function() {
                calendar.updateSize();
            }, 200);
        },
        
        // Adicionar manipuladores para cliques na visualização do calendário
        viewDidMount: function(viewInfo) {
            // Verificar o estado do rendering do calendário quando a visualização é montada
            setTimeout(verificarRenderingCalendario, 100);
        },
        
        // Adicionar listener para cliques no calendário
        dateClick: function(info) {
            // Verificar se o calendário está visível quando o usuário clica
            verificarVisibilidadeCalendario();
        }
    };
    
    // Mostrar mensagem de carregamento
    mostrarAlerta('info', 
        '<strong><i class="fas fa-sync-alt me-2 fa-spin"></i> Carregando</strong> ' +
        'Buscando eventos do calendário. Por favor, aguarde...'
    );
    
    // Criar instância do calendário
    const calendar = new FullCalendar.Calendar(containerCalendario, opcoesCalendario);
    
    // Renderizar o calendário
    calendar.render();
    console.log('✅ Calendário inicializado com sucesso!');
    
    // Executar verificações iniciais para garantir que o calendário seja exibido corretamente
    setTimeout(() => {
        console.log('🔄 Executando verificações iniciais do calendário...');
        
        // Verificar se o calendário está visível e tem dimensões apropriadas
        const calendarEl = document.querySelector('.fc');
        if (calendarEl) {
            const rect = calendarEl.getBoundingClientRect();
            if (rect.width < 50 || rect.height < 50) {
                console.log('⚠️ ALERTA: Detectado calendário com dimensões muito pequenas!');
                console.log(`Dimensões atuais: ${rect.width}x${rect.height}px`);
                
                // Aplicar correção imediata sem mostrar alerta
                const containerCalendario = document.getElementById('calendario');
                if (containerCalendario) {
                    // Definir um estilo explícito para forçar dimensões
                    containerCalendario.style.cssText = 'min-height: 500px; width: 100%; display: block;';
                    
                    // Forçar um redesenho
                    setTimeout(() => {
                        calendar.updateSize();
                        console.log('🔄 Dimensões do contêiner forçadas e tamanho do calendário atualizado');
                    }, 100);
                }
            }
        }
        
        // Verificar se a API foi carregada corretamente
        carregarEventosReais(0); // Iniciar do começo especificamente
        
        // Verificar eventos após um tempo e tentar resolver problemas automaticamente
        setTimeout(() => {
            const eventos = calendar.getEvents();
            console.log(`📊 Total de eventos encontrados: ${eventos.length}`);
            
            // Se o calendário estiver vazio após o carregamento, verificar se está visível
            if (eventos.length === 0) {
                const calendarWrapper = document.querySelector('.fc-view-harness');
                if (calendarWrapper && (calendarWrapper.offsetHeight < 100 || calendarWrapper.offsetWidth < 100)) {
                    console.log('⚠️ Detectado problema crítico: calendário com dimensões insuficientes');
                    
                    // Aplicar correção automática para o calendário vazio
                    corrigirCalendarioVazio();
                } else {
                    // Se o calendário tem dimensões ok mas não tem eventos, tentar novamente
                    carregarEventosReais(0);
                }
            } else {
                // Se tem eventos, verificar se estão sendo exibidos corretamente
                verificarVisualizacaoCalendario();
            }
        }, 2000);
    }, 500);
    
    // Função para verificar se há eventos após o carregamento
    function verificarEventos() {
        const eventos = calendar.getEvents();
        if (eventos.length === 0) {
            console.log('⚠️ Nenhum evento encontrado. Tentando buscar novamente...');
            
            // Tentar forçar um recarregamento dos eventos reais uma única vez
            // sem oferecer dados de demonstração como fallback
            carregarEventosReais();
        }
    }
    
    // Função para carregar eventos reais do servidor
    function carregarEventosReais(urlIndex = 0) {
        // Se não recebemos índice, reiniciar do começo
        if (urlIndex === undefined || urlIndex === null) {
            urlIndex = 0;
        }
        
        // Se chegamos ao fim das URLs alternativas
        if (urlIndex >= apiUrlsAlternativas.length) {
            console.error('❌ Todas as URLs alternativas falharam. Tentando busca direta das ordens.');
            buscarOrdensTecnico();
            return;
        }
        
        // Obter a URL atual para tentar
        const urlAtual = urlIndex === 0 ? apiUrl : apiUrlsAlternativas[urlIndex - 1];
        console.log(`🔄 Tentativa ${urlIndex + 1}/${apiUrlsAlternativas.length + 1}: ${urlAtual}`);
        
        // Remover eventos existentes
        calendar.getEvents().forEach(event => event.remove());
        
        // Mostrar mensagem de carregamento
        mostrarAlerta('info', 
            `<strong><i class="fas fa-sync-alt me-2 fa-spin"></i> Carregando</strong> ` +
            `Tentativa ${urlIndex + 1}: buscando eventos em ${urlAtual}...`
        );
        
        // Mostrar carregando na tabela também
        mostrarCarregandoNaTabela();
        
        // Adicionar timestamp para evitar cache
        const timestamp = new Date().getTime();
        const urlComTimestamp = `${urlAtual}?_=${timestamp}&nocache=true`;
        
        // Configurar cabeçalhos para a requisição
        const headers = new Headers();
        headers.append('Accept', 'application/json');
        
        // Obter token CSRF se disponível
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            headers.append('X-CSRFToken', csrfToken.content);
        }
        
        // Obter token JWT se disponível
        const jwtToken = localStorage.getItem('jwt_token');
        if (jwtToken) {
            headers.append('Authorization', `Bearer ${jwtToken}`);
        }
        
        // Fazer a requisição
        fetch(urlComTimestamp, {
            method: 'GET',
            headers: headers,
            credentials: 'same-origin' // Enviar cookies
        })
        .then(response => {
            console.log(`Status da resposta (${urlAtual}):`, response.status);
            
            // Verificar o status da resposta
            if (response.status === 404) {
                // URL não encontrada, tentar próxima
                console.log(`⚠️ URL ${urlAtual} não encontrada (404). Tentando próxima URL...`);
                carregarEventosReais(urlIndex + 1);
                return null;
            }
            else if (response.status === 403 || response.status === 401) {
                // Erro de autenticação/autorização
                console.error(`❌ Erro de permissão (${response.status}) ao acessar ${urlAtual}`);
                mostrarAlerta('danger', 
                    `<strong><i class="fas fa-lock me-2"></i> Erro de permissão</strong> ` +
                    `Você não tem permissão para acessar os dados do calendário.`
                );
                return null;
            }
            else if (!response.ok) {
                // Outro erro
                console.error(`❌ Erro HTTP ${response.status} ao acessar ${urlAtual}`);
                carregarEventosReais(urlIndex + 1);
                return null;
            }
            
            // Tentar processar a resposta como JSON
            return response.json().catch(error => {
                console.error('❌ Erro ao processar JSON:', error);
                return null;
            });
        })
        .then(dados => {
            // Verificar se os dados são válidos
            if (!dados) {
                console.log('⚠️ Resposta vazia ou inválida. Tentando próxima URL...');
                carregarEventosReais(urlIndex + 1);
                return;
            }
            
            console.log(`✅ Dados recebidos de ${urlAtual}:`, dados);
            
            // Processar diferentes formatos de resposta
            let eventos = [];
            
            if (Array.isArray(dados)) {
                // Formato 1: Array direto de eventos
                eventos = dados;
            } 
            else if (dados.eventos && Array.isArray(dados.eventos)) {
                // Formato 2: { eventos: [...] }
                eventos = dados.eventos;
            }
            else if (dados.status === 'sucesso' && dados.eventos && Array.isArray(dados.eventos)) {
                // Formato 3: { status: 'sucesso', eventos: [...] }
                eventos = dados.eventos;
            }
            else if (dados.data && Array.isArray(dados.data)) {
                // Formato 4: { data: [...] }
                eventos = dados.data;
            }
            else if (dados.results && Array.isArray(dados.results)) {
                // Formato 5: { results: [...] }
                eventos = dados.results;
            }
            else {
                // Tentar converter outro formato (último recurso)
                eventos = converterOrdensParaEventos(dados);
            }
            
            // Verificar se temos eventos
            if (eventos.length === 0) {
                console.log('⚠️ Nenhum evento encontrado na resposta. Tentando próxima URL...');
                carregarEventosReais(urlIndex + 1);
                return;
            }
            
            // Adicionar eventos ao calendário
            eventos.forEach(evento => {
                console.log('Adicionando evento ao calendário:', evento);
                calendar.addEvent(evento);
            });
            
            // Atualizar a tabela com os mesmos eventos
            atualizarTabelaEventos(eventos);
            
            // Mostrar mensagem de sucesso
            mostrarAlerta('success', 
                `<strong><i class="fas fa-calendar-check me-2"></i> Dados carregados</strong> ` +
                `${eventos.length} evento(s) carregado(s) com sucesso.`
            );
            
            // Verificar se o calendário está mostrando corretamente
            setTimeout(() => {
                verificarVisualizacaoCalendario();
            }, 500);
            
            // Limpar mensagem de carregamento
            limparCarregamentoTabela();
        })
        .catch(error => {
            // Erro durante o fetch
            console.error(`❌ Erro ao buscar dados de ${urlAtual}:`, error);
            
            // Se não for a última URL, tentar a próxima
            if (urlIndex < apiUrlsAlternativas.length) {
                console.log(`⚠️ Tentando próxima URL alternativa (${urlIndex + 1}/${apiUrlsAlternativas.length})...`);
                carregarEventosReais(urlIndex + 1);
            } else {
                console.error('❌ Todas as URLs falharam. Tentando buscar ordens diretamente...');
                buscarOrdensTecnico();
            }
        });
    }
    
    // Função para converter diferentes formatos de dados em eventos de calendário
    function converterOrdensParaEventos(dados) {
        console.log('🔄 Tentando converter dados para formato de eventos:', dados);
        let eventos = [];
        
        // Verificar se estamos lidando com um objeto ou array
        if (!dados) {
            return [];
        }
        
        // Se for um array, verificar se cada item tem dados que podem ser convertidos
        if (Array.isArray(dados)) {
            console.log('📋 Processando array de dados...');
            dados.forEach((item, index) => {
                let evento = criarEventoDeItem(item, index);
                if (evento) {
                    eventos.push(evento);
                }
            });
        } 
        // Se for um objeto, verificar se tem uma lista de ordens
        else if (typeof dados === 'object') {
            console.log('📋 Processando objeto de dados...');
            
            // Opção 1: Procurar por propriedades comuns que podem conter ordens
            const possiveisPropriedades = ['ordens', 'os', 'orders', 'servicoOrdens', 'serviceOrders', 'atendimentos'];
            
            for (const prop of possiveisPropriedades) {
                if (dados[prop] && Array.isArray(dados[prop])) {
                    console.log(`📋 Encontrada lista em dados.${prop}`);
                    dados[prop].forEach((item, index) => {
                        let evento = criarEventoDeItem(item, index);
                        if (evento) {
                            eventos.push(evento);
                        }
                    });
                    break; // Encontramos uma lista válida, não precisa procurar mais
                }
            }
            
            // Opção 2: Se o próprio objeto parece uma ordem
            if (eventos.length === 0 && (dados.id || dados.numero || dados.ordem_id)) {
                let evento = criarEventoDeItem(dados, 0);
                if (evento) {
                    eventos.push(evento);
                }
            }
            
            // Opção 3: Se tem listas em algum lugar mais profundo
            if (eventos.length === 0) {
                for (const key in dados) {
                    if (typeof dados[key] === 'object' && dados[key] !== null) {
                        // Recursivamente tentar encontrar listas de eventos
                        const eventosEncontrados = converterOrdensParaEventos(dados[key]);
                        if (eventosEncontrados.length > 0) {
                            console.log(`📋 Encontrados ${eventosEncontrados.length} eventos em dados.${key}`);
                            eventos = eventos.concat(eventosEncontrados);
                        }
                    }
                }
            }
        }
        
        console.log(`✅ Convertidos ${eventos.length} eventos de dados personalizados`);
        return eventos;
    }
    
    // Função auxiliar para criar um evento a partir de um item
    function criarEventoDeItem(item, index) {
        if (!item || typeof item !== 'object') {
            return null;
        }
        
        console.log(`📦 Processando item ${index}:`, item);
        
        // Campos possíveis para data
        const camposData = ['data_agendamento', 'data', 'data_inicio', 'start', 'startDate', 'dataHora', 
                             'data_hora', 'data_atendimento', 'agendamento', 'scheduled_date'];
        
        // Campos possíveis para título/descrição
        const camposTitulo = ['titulo', 'title', 'descricao', 'description', 'nome', 'name', 'servico', 'service'];
        
        // Campos possíveis para ID
        const camposId = ['id', 'ordem_id', 'os_id', 'numero', 'number', 'codigo', 'code'];
        
        // Encontrar data
        let dataEvento = null;
        for (const campo of camposData) {
            if (item[campo]) {
                dataEvento = item[campo];
                console.log(`📅 Data encontrada em ${campo}:`, dataEvento);
                break;
            }
        }
        
        // Se não encontrou data, verificar campos aninhados
        if (!dataEvento && item.ordem && typeof item.ordem === 'object') {
            for (const campo of camposData) {
                if (item.ordem[campo]) {
                    dataEvento = item.ordem[campo];
                    console.log(`📅 Data encontrada em ordem.${campo}:`, dataEvento);
                    break;
                }
            }
        }
        
        // Verificar se a data está em formato válido
        if (dataEvento) {
            // Se for string, tentar converter para data ISO
            if (typeof dataEvento === 'string') {
                // Formatar data se não estiver em formato ISO
                if (!dataEvento.includes('T') && dataEvento.includes('/')) {
                    // Formato DD/MM/YYYY ou MM/DD/YYYY
                    const partes = dataEvento.split('/');
                    if (partes.length === 3) {
                        // Assumir DD/MM/YYYY e converter para YYYY-MM-DD
                        dataEvento = `${partes[2]}-${partes[1].padStart(2, '0')}-${partes[0].padStart(2, '0')}`;
                        console.log('🔄 Data convertida de DD/MM/YYYY para:', dataEvento);
                    }
                }
            }
        } else {
            console.log('⚠️ Não foi possível encontrar uma data válida para o evento');
            return null;
        }
        
        // Encontrar título
        let tituloEvento = null;
        for (const campo of camposTitulo) {
            if (item[campo]) {
                tituloEvento = item[campo];
                console.log(`📝 Título encontrado em ${campo}:`, tituloEvento);
                break;
            }
        }
        
        // Se não encontrou título, verificar campos aninhados
        if (!tituloEvento && item.ordem && typeof item.ordem === 'object') {
            for (const campo of camposTitulo) {
                if (item.ordem[campo]) {
                    tituloEvento = item.ordem[campo];
                    console.log(`📝 Título encontrado em ordem.${campo}:`, tituloEvento);
                    break;
                }
            }
        }
        
        // Encontrar ID
        let idEvento = null;
        for (const campo of camposId) {
            if (item[campo]) {
                idEvento = item[campo];
                console.log(`🔑 ID encontrado em ${campo}:`, idEvento);
                break;
            }
        }
        
        // Se não encontrou ID, verificar campos aninhados
        if (!idEvento && item.ordem && typeof item.ordem === 'object') {
            for (const campo of camposId) {
                if (item.ordem[campo]) {
                    idEvento = item.ordem[campo];
                    console.log(`🔑 ID encontrado em ordem.${campo}:`, idEvento);
                    break;
                }
            }
        }
        
        // Se não tiver título mas tiver ID, criar um título padrão
        if (!tituloEvento && idEvento) {
            tituloEvento = `OS #${idEvento}`;
        }
        
        // Se mesmo assim não tiver título, usar um genérico
        if (!tituloEvento) {
            tituloEvento = `Atendimento ${index + 1}`;
        }
        
        // Determinar cor com base em algum status ou tipo
        let corEvento = '#3498db'; // Azul padrão
        
        if (item.status) {
            if (item.status.toLowerCase().includes('conclu') || item.status === 'done') {
                corEvento = '#28a745'; // Verde
            } else if (item.status.toLowerCase().includes('andamento') || item.status === 'in_progress') {
                corEvento = '#17a2b8'; // Azul esverdeado
            } else if (item.status.toLowerCase().includes('cancel') || item.status === 'cancelled') {
                corEvento = '#dc3545'; // Vermelho
            } else if (item.status.toLowerCase().includes('aberta') || item.status === 'open') {
                corEvento = '#fd7e14'; // Laranja
            }
        }
        
        // Criar evento com os dados extraídos
        return {
            id: idEvento || `custom-event-${index}`,
            title: tituloEvento,
            start: dataEvento,
            color: corEvento,
            extendedProps: {
                customData: item // Preservar dados originais
            }
        };
    }
    
    // Função para buscar ordens do técnico diretamente
    function buscarOrdensTecnico() {
        console.log("🔍 Tentando extrair ordens do técnico da página...");
        mostrarAlerta('info', '<i class="fas fa-search me-2"></i> <strong>Buscando ordens</strong> na página...');
        mostrarCarregandoNaTabela();
        
        const ordens = extrairOrdensDaPagina();
        console.log(`📋 Extraídas ${ordens.length} ordens da página`);
        
        if (ordens.length > 0) {
            const eventos = converterOrdensParaEventos(ordens);
            adicionarEventosAoCalendario(eventos);
            
            // Limpar mensagem de carregamento
            limparCarregamentoTabela();
            
            mostrarAlerta('success', `<i class="fas fa-clipboard-list me-2"></i> <strong>${ordens.length} ordens</strong> encontradas e adicionadas ao calendário!`);
            return true;
        } else {
            // Se não conseguiu extrair da página, mostrar erro e oferecer demonstração
            mostrarErroAPI('Não foi possível buscar as ordens do técnico. Deseja visualizar dados de demonstração para testar o calendário?', true);
        }
    }
    
    // Função para extrair ordens da própria página
    function extrairOrdensDaPagina() {
        console.log('🔎 Tentando extrair ordens diretamente da página...');
        
        // Tentar encontrar tabelas de ordens em diferentes seletores comuns
        const possiveisSeletores = [
            'table.ordens-servico', 
            'table.ordens',
            'table.orders',
            '#lista-ordens',
            '#ordens-tecnico',
            '.ordem-item',
            '.lista-os'
        ];
        
        let ordens = [];
        
        // Verificar cada possível seletor
        for (const seletor of possiveisSeletores) {
            const elementos = document.querySelectorAll(seletor);
            
            if (elementos && elementos.length > 0) {
                console.log(`✅ Encontrados ${elementos.length} elementos com o seletor "${seletor}"`);
                
                // Processar tabelas
                if (seletor.startsWith('table')) {
                    elementos.forEach(tabela => {
                        const linhas = tabela.querySelectorAll('tbody tr');
                        console.log(`📋 Processando ${linhas.length} linhas da tabela`);
                        
                        linhas.forEach((linha, idx) => {
                            // Obter células
                            const celulas = linha.querySelectorAll('td');
                            if (celulas.length >= 3) {
                                const ordem = {
                                    id: celulas[0].textContent.trim(),
                                    titulo: celulas[1].textContent.trim(),
                                    data_agendamento: null
                                };
                                
                                // Tentar encontrar uma data em alguma célula
                                celulas.forEach(celula => {
                                    const texto = celula.textContent.trim();
                                    if (texto.match(/\d{2}\/\d{2}\/\d{4}/) || texto.match(/\d{4}-\d{2}-\d{2}/)) {
                                        ordem.data_agendamento = texto;
                                    }
                                });
                                
                                // Se encontrou uma data válida, adicionar às ordens
                                if (ordem.data_agendamento) {
                                    ordens.push(ordem);
                                }
                            }
                        });
                    });
                }
                // Processar itens individuais
                else {
                    elementos.forEach((elemento, idx) => {
                        const numeroElement = elemento.querySelector('.numero, .id, .codigo');
                        const descricaoElement = elemento.querySelector('.descricao, .titulo, .servico');
                        const dataElement = elemento.querySelector('.data, .agendamento, .data-hora');
                        
                        if (dataElement) {
                            const ordem = {
                                id: numeroElement ? numeroElement.textContent.trim() : `ordem-${idx}`,
                                titulo: descricaoElement ? descricaoElement.textContent.trim() : `Ordem ${idx + 1}`,
                                data_agendamento: dataElement.textContent.trim()
                            };
                            
                            ordens.push(ordem);
                        }
                    });
                }
                
                // Se encontrou ordens, interromper a busca
                if (ordens.length > 0) {
                    break;
                }
            }
        }
        
        console.log(`✅ Total de ${ordens.length} ordens extraídas da página`);
        return ordens;
    }
    
    // Função para verificar se o calendário está exibindo corretamente
    function verificarVisualizacaoCalendario() {
        console.log('🔍 Verificando visualização do calendário...');
        
        const events = calendar.getEvents();
        console.log(`📊 Total de eventos no calendário: ${events.length}`);
        
        if (events.length === 0) {
            console.log('⚠️ Calendário vazio após carregamento de dados!');
            mostrarAlerta('warning', 
                `<strong><i class="fas fa-exclamation-triangle me-2"></i> Atenção</strong> ` +
                `O calendário parece estar vazio. ` +
                `<button class="btn btn-sm btn-primary mx-1" onclick="carregarEventosReais(0); return false;">Carregar Compromissos</button> ` +
                `<button class="btn btn-sm btn-warning mx-1" onclick="corrigirCalendarioVazio(); return false;">Diagnosticar Problemas</button> ` +
                `<button class="btn btn-sm btn-info mx-1" onclick="carregarEventosDemonstracao(); return false;">Ver Demonstração</button>`
            );
        } else {
            // Verificar se os eventos estão visíveis na visualização atual
            const visibleEvents = events.filter(event => {
                const start = event.start;
                if (!start) return false;
                
                const view = calendar.view;
                const viewStart = view.activeStart;
                const viewEnd = view.activeEnd;
                
                return start >= viewStart && start <= viewEnd;
            });
            
            console.log(`📊 Eventos visíveis no período atual: ${visibleEvents.length}`);
            
            if (visibleEvents.length === 0 && events.length > 0) {
                console.log('⚠️ Há eventos carregados mas nenhum está visível na visualização atual!');
                
                // Pegar a data do primeiro evento
                const firstEventDate = events[0].start;
                if (firstEventDate) {
                    console.log(`📅 Navegando para o primeiro evento: ${firstEventDate}`);
                    calendar.gotoDate(firstEventDate);
                    
                    mostrarAlerta('info', 
                        `<strong><i class="fas fa-calendar-day me-2"></i> Navegação automática</strong> ` +
                        `Navegando para a data do primeiro evento: ${firstEventDate.toLocaleDateString()}.`
                    );
                }
            }
        }
    }
    
    // Função para corrigir o calendário quando estiver vazio
    function corrigirCalendarioVazio() {
        console.log('🔧 Tentando corrigir o calendário vazio...');
        mostrarAlerta('info', '<i class="fas fa-wrench me-2"></i> <strong>Diagnóstico</strong> em andamento...');
        
        // 1. Verificar se o contêiner tem altura
        const calendarContainer = document.getElementById('calendario');
        const calendarHeight = calendarContainer ? calendarContainer.offsetHeight : 0;
        
        if (calendarHeight < 100) {
            console.log('⚠️ Container do calendário sem altura adequada.');
            calendarContainer.style.height = '500px';
        }
        
        // 2. Forçar redesenho do calendário
        setTimeout(function() {
            // Verificar se o FullCalendar foi inicializado
            if (typeof calendar === 'undefined' || !calendar) {
                console.error('❌ Objeto calendar não encontrado!');
                mostrarAlerta('danger', 
                    '<strong><i class="fas fa-exclamation-triangle me-2"></i> Erro</strong> ' +
                    'O calendário não foi inicializado corretamente. Tente recarregar a página.'
                );
                return;
            }
            
            try {
                // Remover todos os eventos existentes
                calendar.getEvents().forEach(event => event.remove());
                
                // Forçar redesenho
                calendar.render();
                calendar.updateSize();
                
                // Esperar o redesenho e verificar dimensões
                setTimeout(function() {
                    const fcViewHarness = document.querySelector('.fc-view-harness');
                    if (fcViewHarness && fcViewHarness.offsetHeight < 100) {
                        console.log('⚠️ Calendário com altura insuficiente após redesenho.');
                        
                        // Tentar injetar um estilo para forçar altura
                        const styleElement = document.createElement('style');
                        styleElement.textContent = `
                            .fc-view-harness {
                                min-height: 500px !important;
                                height: 500px !important;
                            }
                            .fc-scroller {
                                height: auto !important;
                                overflow: visible !important;
                            }
                        `;
                        document.head.appendChild(styleElement);
                        
                        // Novo redesenho
                        setTimeout(function() {
                            calendar.render();
                            calendar.updateSize();
                            
                            // Tentar carregar eventos
                            carregarEventosReais(0);
                        }, 200);
                    } else {
                        // Tudo parece ok, tentar carregar eventos
                        console.log('✅ Calendário redesenhado com sucesso!');
                        carregarEventosReais(0);
                    }
                }, 200);
                
                mostrarAlerta('success', 
                    '<strong><i class="fas fa-check me-2"></i> Correção aplicada</strong> ' +
                    'Calendário redesenhado e eventos recarregados.'
                );
            } catch (error) {
                console.error('❌ Erro ao redesenhar calendário:', error);
                mostrarAlerta('danger', 
                    `<strong><i class="fas fa-exclamation-triangle me-2"></i> Erro</strong> ` +
                    `Falha ao redesenhar o calendário: ${error.message}`
                );
            }
        }, 300);
    }
    
    function mostrarErroAPI(mensagemErro, oferecer_demo) {
        let mensagem = '<strong><i class="fas fa-exclamation-triangle me-2"></i> Atenção</strong> ' +
            'A API de calendário não está disponível ou o endpoint não foi encontrado.';
            
        if (mensagemErro) {
            mensagem += `<br><small class="text-danger">Erro: ${mensagemErro}</small>`;
        }
        
        mensagem += '<br><small>Carregando dados de demonstração automaticamente...</small>';
        
        mostrarAlerta('warning', mensagem);
        
        // Carregar demonstração automaticamente após um curto período
        if (oferecer_demo) {
            setTimeout(() => {
                console.log('🔄 Carregando demonstração automaticamente após erro da API');
                carregarEventosDemonstracao();
                
                // Atualizar a mensagem após carregar os dados
                setTimeout(() => {
                    mostrarAlerta('info', 
                        '<strong><i class="fas fa-info-circle me-2"></i> Dados de Demonstração</strong> ' +
                        'Exibindo eventos de exemplo devido à indisponibilidade temporária dos dados reais.'
                    );
                }, 1500);
            }, 2000);
        }
    }
    
    // Função para mostrar diálogo de confirmação com Bootstrap
    function mostrarDialogoConfirmacao(titulo, mensagem, callbackSim) {
        // Verificar se já existe um diálogo
        let dialogo = document.getElementById('dialogo-confirmacao');
        if (dialogo) {
            dialogo.remove();
        }
        
        // Criar o diálogo
        dialogo = document.createElement('div');
        dialogo.className = 'modal fade';
        dialogo.id = 'dialogo-confirmacao';
        dialogo.tabIndex = '-1';
        dialogo.setAttribute('aria-hidden', 'true');
        
        dialogo.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${titulo}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
                    </div>
                    <div class="modal-body">
                        <p>${mensagem}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Não</button>
                        <button type="button" class="btn btn-primary" id="btn-confirmar-sim">Sim</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialogo);
        
        // Inicializar o modal com Bootstrap
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const modalObj = new bootstrap.Modal(dialogo);
            modalObj.show();
            
            // Adicionar evento ao botão Sim
            const btnSim = document.getElementById('btn-confirmar-sim');
            if (btnSim) {
                btnSim.addEventListener('click', function() {
                    modalObj.hide();
                    if (typeof callbackSim === 'function') {
                        callbackSim();
                    }
                });
            }
        } else {
            // Se não tiver Bootstrap, mostrar uma confirmação padrão
            if (confirm(mensagem)) {
                if (typeof callbackSim === 'function') {
                    callbackSim();
                }
            }
        }
    }
    
    function mostrarErroCarregamento(mensagemErro) {
        let mensagem = '<strong><i class="fas fa-exclamation-triangle me-2"></i> Atenção</strong> ' +
            'Não foi possível carregar os eventos reais do calendário do banco de dados.';
            
        if (mensagemErro) {
            mensagem += `<br><small class="text-danger">Erro: ${mensagemErro}</small>`;
        }
        
        mensagem += '<br><small>Por favor, tente recarregar a página ou clique no botão "Atualizar Eventos" abaixo.</small>';
        
        mostrarAlerta('warning', mensagem);
    }
    
    function mostrarAlerta(tipo, mensagem) {
        // Remover alertas existentes
        const alertasAntigos = document.querySelectorAll('.alerta-calendario');
        alertasAntigos.forEach(alerta => alerta.remove());
        
        // Criar novo alerta
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show mt-3 alerta-calendario`;
        alerta.innerHTML = `
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
        `;
        
        // Adicionar após o calendário
        containerCalendario.parentNode.insertBefore(alerta, containerCalendario.nextSibling);
    }
    
    // Função para carregar eventos de demonstração como fallback
    function carregarEventosDemonstracao() {
        console.log("🎬 Gerando eventos de demonstração...");
        mostrarAlerta('info', '<i class="fas fa-film me-2"></i> <strong>Gerando dados</strong> de demonstração...');
        mostrarCarregandoNaTabela();
        
        // Gerar eventos para os próximos 7 dias (apenas dias úteis)
        const hoje = new Date();
        const eventos = [];
        
        for (let i = 0; i < 7; i++) {
            const data = new Date();
            data.setDate(data.getDate() + i);
            const dataFormatada = data.toISOString().split('T')[0];
            
            if (data.getDay() >= 1 && data.getDay() <= 5) {
                if (i % 2 === 0) {
                    eventos.push({
                        id: `os-${1000 + i}`,
                        title: `OS #${Math.floor(1000 + Math.random() * 9000)} - Manutenção`,
                        start: `${dataFormatada}T09:00:00`,
                        end: `${dataFormatada}T11:00:00`,
                        className: 'ordem-pendente',
                        color: '#FF9800'
                    });
                } else {
                    eventos.push({
                        id: `os-${2000 + i}`,
                        title: `OS #${Math.floor(1000 + Math.random() * 9000)} - Instalação`,
                        start: `${dataFormatada}T14:00:00`,
                        end: `${dataFormatada}T16:00:00`,
                        className: 'ordem-em_andamento',
                        color: '#2196F3'
                    });
                }
            }
        }
        
        // Adicionar evento de férias no próximo mês
        const proximoMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 1);
        eventos.push({
            id: 'ferias-1',
            title: 'Férias Programadas',
            start: proximoMes.toISOString().split('T')[0],
            end: new Date(proximoMes.getFullYear(), proximoMes.getMonth(), 15).toISOString().split('T')[0],
            className: 'ferias',
            color: '#FFCA28',
            allDay: true
        });
        
        // Adicionar os eventos ao calendário
        calendar.getApi().removeAllEvents();
        calendar.getApi().addEventSource(eventos);
        
        // Limpar mensagem de carregamento
        limparCarregamentoTabela();
        
        mostrarAlerta('warning', '<i class="fas fa-theater-masks me-2"></i> <strong>Modo de demonstração</strong> ativado. Estes não são dados reais.');
        console.log("🎭 Calendário em modo demonstração");
    }
    
    // Função para atualizar a tabela de eventos
    function atualizarTabelaEventos(eventos) {
        const tabelaEventos = document.getElementById('tabela-eventos');
        if (!tabelaEventos) {
            console.log('⚠️ Tabela de eventos não encontrada no DOM');
            return;
        }
        
        // Limpar tabela atual
        tabelaEventos.innerHTML = '';
        
        // Se não tiver eventos, mostrar mensagem
        if (!eventos || eventos.length === 0) {
            // Obter o mês atual formatado
            let mensagemMes = "este mês";
            const mesAtualEl = document.getElementById('mes-atual');
            if (mesAtualEl && mesAtualEl.textContent) {
                mensagemMes = mesAtualEl.textContent.toLowerCase();
            }
            
            // Mensagem personalizada
            tabelaEventos.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4">
                        <i class="fas fa-calendar-check text-muted mb-3" style="font-size: 2rem;"></i>
                        <p class="mb-0">Nenhum compromisso para ${mensagemMes}</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        // Ordenar eventos por data
        const eventoOrdenados = [...eventos].sort((a, b) => {
            const dataA = new Date(a.start);
            const dataB = new Date(b.start);
            return dataA - dataB;
        });
        
        // Adicionar cada evento à tabela
        eventoOrdenados.forEach(evento => {
            try {
                // Extrair data e hora do evento
                const dataEvento = new Date(evento.start);
                const dataFormatada = dataEvento.toLocaleDateString('pt-BR');
                const horaFormatada = dataEvento.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
                
                // Determinar status e classe CSS com base no status ou classe do evento
                let statusTexto = 'Agendado';
                let statusClass = 'bg-primary';
                
                // Determinar o status com base na cor ou classe do evento
                if (evento.className) {
                    const className = Array.isArray(evento.className) ? evento.className.join(' ') : evento.className;
                    
                    if (className.includes('ordem-aberta')) {
                        statusTexto = 'Em Aberto';
                        statusClass = 'bg-danger';
                    } else if (className.includes('ordem-em_andamento')) {
                        statusTexto = 'Em Andamento';
                        statusClass = 'bg-warning text-dark';
                    } else if (className.includes('ordem-concluida')) {
                        statusTexto = 'Concluída';
                        statusClass = 'bg-success';
                    } else if (className.includes('ferias')) {
                        statusTexto = 'Férias';
                        statusClass = 'bg-info';
                    } else if (className.includes('ausencia')) {
                        statusTexto = 'Ausência';
                        statusClass = 'bg-secondary';
                    }
                } else if (evento.color) {
                    // Determinar status com base na cor
                    if (evento.color === '#fd7e14' || evento.color === '#FF9800') {
                        statusTexto = 'Em Aberto';
                        statusClass = 'bg-danger';
                    } else if (evento.color === '#17a2b8' || evento.color === '#2196F3') {
                        statusTexto = 'Em Andamento';
                        statusClass = 'bg-warning text-dark';
                    } else if (evento.color === '#28a745') {
                        statusTexto = 'Concluída';
                        statusClass = 'bg-success';
                    } else if (evento.color === '#FFCA28') {
                        statusTexto = 'Férias';
                        statusClass = 'bg-info';
                    }
                }
                
                // Usar status do evento se disponível
                if (evento.extendedProps && evento.extendedProps.customData && evento.extendedProps.customData.status) {
                    statusTexto = evento.extendedProps.customData.status;
                } else if (evento.status) {
                    statusTexto = evento.status;
                }
                
                // Criar link para o evento se tiver slug
                let acoesBotao = `
                    <button class="btn btn-sm btn-outline-secondary" disabled>
                        <i class="fas fa-calendar-day"></i>
                    </button>
                `;
                
                if (evento.url || (evento.extendedProps && evento.extendedProps.url)) {
                    const url = evento.url || evento.extendedProps.url;
                    acoesBotao = `
                        <a href="${url}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye"></i>
                        </a>
                    `;
                }
                
                // Criar linha da tabela
                const linha = document.createElement('tr');
                linha.innerHTML = `
                    <td>${dataFormatada}</td>
                    <td>${horaFormatada}</td>
                    <td>${evento.title}</td>
                    <td>
                        <span class="badge ${statusClass}">
                            ${statusTexto}
                        </span>
                    </td>
                    <td>${acoesBotao}</td>
                `;
                
                tabelaEventos.appendChild(linha);
            } catch (error) {
                console.error('Erro ao processar evento para tabela:', error, evento);
            }
        });
        
        console.log(`✅ Tabela atualizada com ${eventoOrdenados.length} eventos`);
    }

    // Adicionar evento para atualizar a tabela quando a visualização do calendário é alterada
    calendar.on('datesSet', function(info) {
        // Obter eventos visíveis no período atual
        const view = calendar.view;
        const viewStart = view.activeStart;
        const viewEnd = view.activeEnd;
        
        const events = calendar.getEvents();
        const visibleEvents = events.filter(event => {
            const start = event.start;
            if (!start) return false;
            return start >= viewStart && start <= viewEnd;
        });
        
        console.log(`🔍 Exibindo ${visibleEvents.length} eventos na visualização atual`);
        
        // Atualizar a tabela apenas com os eventos visíveis no período atual
        atualizarTabelaEventos(visibleEvents);
    });

    // Conectar botões de navegação do mês na tabela ao calendário
    const btnMesAnterior = document.getElementById('btn-mes-anterior');
    const btnProximoMes = document.getElementById('btn-proximo-mes');
    const mesAtualEl = document.getElementById('mes-atual');

    if (btnMesAnterior) {
        btnMesAnterior.addEventListener('click', function() {
            // Navegar para o mês anterior no calendário
            calendar.prev();
            
            // Atualizar o texto do mês atual
            if (mesAtualEl) {
                const dataAtual = calendar.getDate();
                const options = { month: 'long', year: 'numeric' };
                mesAtualEl.textContent = dataAtual.toLocaleDateString('pt-BR', options);
            }
        });
    }

    if (btnProximoMes) {
        btnProximoMes.addEventListener('click', function() {
            // Navegar para o próximo mês no calendário
            calendar.next();
            
            // Atualizar o texto do mês atual
            if (mesAtualEl) {
                const dataAtual = calendar.getDate();
                const options = { month: 'long', year: 'numeric' };
                mesAtualEl.textContent = dataAtual.toLocaleDateString('pt-BR', options);
            }
        });
    }

    // Inicializar o mês atual
    if (mesAtualEl) {
        const dataAtual = calendar.getDate();
        const options = { month: 'long', year: 'numeric' };
        mesAtualEl.textContent = dataAtual.toLocaleDateString('pt-BR', options);
    }

    // Função para mostrar mensagem de carregamento na tabela
    function mostrarCarregandoNaTabela() {
        const tabelaEventos = document.getElementById('tabela-eventos');
        if (!tabelaEventos) return;
        
        tabelaEventos.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-3">
                    <i class="fas fa-spinner fa-spin me-2"></i> Carregando compromissos...
                </td>
            </tr>
        `;
    }

    // Adicionar a função para limpar o carregamento da tabela
    function limparCarregamentoTabela() {
        // Encontrar o elemento da tabela de eventos (não a tabela do calendário)
        const tabelaEventos = document.getElementById('tabela-eventos');
        if (tabelaEventos && tabelaEventos.querySelector('td i.fa-spinner')) {
            // Limpar apenas se tiver o indicador de carregamento
            tabelaEventos.innerHTML = '';
        }
        
        // NÃO limpar a tabela do calendário
        // O bug anterior era porque estávamos selecionando e limpando '.fc-scrollgrid-sync-table'
    }
    
    // Adicionar verificação de visibilidade e rendering do calendário
    window.addEventListener('resize', function() {
        // Verificar a visibilidade após redimensionamento
        setTimeout(verificarVisibilidadeCalendario, 100);
    });
    
    // Função para verificar se o calendário está visível corretamente
    function verificarVisibilidadeCalendario() {
        console.log('🔍 Verificando visibilidade do calendário após redimensionamento...');
        
        const calendarEl = document.querySelector('.fc');
        if (!calendarEl) return;
        
        // Verificar se o calendário tem dimensões visíveis
        const rect = calendarEl.getBoundingClientRect();
        const isVisible = (rect.width > 0 && rect.height > 0);
        
        if (!isVisible || rect.width < 100 || rect.height < 100) {
            console.log('⚠️ Calendário não está visível ou tem dimensões muito pequenas. Forçando renderização...');
            
            // Forçar nova renderização do calendário
            setTimeout(function() {
                calendar.updateSize();
                
                // Se mesmo assim não estiver visível, tentar mostrar/esconder para forçar o repaint
                if (calendarEl.style.display !== 'none') {
                    calendarEl.style.display = 'none';
                    setTimeout(function() {
                        calendarEl.style.display = 'block';
                        calendar.updateSize();
                        
                        // Verificar se há eventos para mostrar
                        verificarVisualizacaoCalendario();
                    }, 50);
                }
            }, 50);
        }
    }
    
    // Função para recuperar de problemas de rendering do calendário
    function verificarRenderingCalendario() {
        console.log('🔍 Verificando o rendering do calendário...');
        
        const calendarEl = document.querySelector('.fc-view-harness');
        if (!calendarEl) return;
        
        const calendarHeight = calendarEl.offsetHeight;
        const calendarWidth = calendarEl.offsetWidth;
        
        console.log(`📊 Dimensões do calendário: ${calendarWidth}x${calendarHeight}px`);
        
        // Se o calendário tem dimensões muito pequenas ou zero
        if (calendarHeight < 100 || calendarWidth < 100) {
            console.log('⚠️ Problema detectado: calendario com dimensões incorretas');
            
            // Tentar corrigir através de um resize forçado
            const originalDisplay = calendarEl.style.display;
            
            // Alternar a visibilidade para forçar o recálculo
            calendarEl.style.display = 'none';
            
            setTimeout(function() {
                calendarEl.style.display = originalDisplay || 'block';
                
                // Forçar atualização do tamanho
                calendar.updateSize();
                
                // Adicionar um placeholder temporário se estiver vazio
                const viewEl = document.querySelector('.fc-view');
                if (viewEl && !viewEl.children.length) {
                    console.log('⚠️ Vista do calendário sem conteúdo, adicionando placeholder...');
                    
                    // Criar um elemento temporário para forçar o tamanho
                    const placeholderDiv = document.createElement('div');
                    placeholderDiv.className = 'calendar-placeholder';
                    placeholderDiv.style.cssText = 'height:400px; display:flex; align-items:center; justify-content:center;';
                    placeholderDiv.innerHTML = '<div class="text-center"><i class="fas fa-sync-alt fa-spin mb-3" style="font-size:2rem;"></i><div>Carregando calendário...</div><button class="btn btn-sm btn-primary mt-3" id="btn-fix-calendar">Mostrar Calendário</button></div>';
                    
                    viewEl.appendChild(placeholderDiv);
                    
                    // Adicionar evento para o botão de correção
                    const btnFix = document.getElementById('btn-fix-calendar');
                    if (btnFix) {
                        btnFix.addEventListener('click', function() {
                            placeholderDiv.remove();
                            calendar.render();
                            calendar.updateSize();
                            calendar.gotoDate(new Date());
                            carregarEventosReais(0);
                        });
                    }
                }
            }, 100);
        }
    }
    
    // Chamar a verificação inicial após o carregamento
    setTimeout(verificarVisibilidadeCalendario, 1000);
});