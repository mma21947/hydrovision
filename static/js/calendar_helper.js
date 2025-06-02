/**
 * Arquivo de suporte para o calendário - adiciona recursos extras
 */
(function() {
    console.log('Carregando recursos adicionais para o calendário...');
    
    // Verificar se o SweetAlert2 está disponível
    if (typeof Swal === 'undefined') {
        // Carregar SweetAlert2 se não estiver disponível
        console.log('Carregando SweetAlert2...');
        
        // Adicionar CSS para o SweetAlert2
        const sweetAlertCss = document.createElement('link');
        sweetAlertCss.rel = 'stylesheet';
        sweetAlertCss.href = 'https://cdn.jsdelivr.net/npm/sweetalert2@11.7.32/dist/sweetalert2.min.css';
        document.head.appendChild(sweetAlertCss);
        
        // Adicionar o script do SweetAlert2
        const sweetAlertScript = document.createElement('script');
        sweetAlertScript.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11.7.32/dist/sweetalert2.all.min.js';
        document.body.appendChild(sweetAlertScript);
        
        sweetAlertScript.onload = function() {
            console.log('SweetAlert2 carregado com sucesso!');
            
            // Configurar o SweetAlert2 com o tema do sistema
            if (typeof Swal !== 'undefined') {
                Swal.mixin({
                    customClass: {
                        confirmButton: 'btn btn-primary me-2',
                        cancelButton: 'btn btn-secondary'
                    },
                    buttonsStyling: false
                });
            }
        };
    }
    
    // CSS personalizado para melhorar o visual do calendário
    const estilosPersonalizados = `
        .fc-event {
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            border-radius: 4px;
        }
        
        .fc-event:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            z-index: 100;
        }
        
        .fc-daygrid-day.fc-day-today {
            background-color: rgba(66, 133, 244, 0.1) !important;
        }
        
        .fc-button-primary {
            background-color: #1976d2 !important;
            border-color: #1565c0 !important;
        }
        
        .fc-button-primary:hover {
            background-color: #1565c0 !important;
        }
        
        .fc-button-primary:disabled {
            background-color: #64b5f6 !important;
            border-color: #42a5f5 !important;
        }
        
        .fc-highlight {
            background-color: rgba(66, 133, 244, 0.2) !important;
        }
    `;
    
    // Adicionar os estilos à página
    const style = document.createElement('style');
    style.textContent = estilosPersonalizados;
    document.head.appendChild(style);
    
    // Função global para criar uma nova ordem de serviço
    window.adicionarNovaOrdem = function(dataStr) {
        // Obter o ID do técnico da URL (se existir)
        const urlParams = new URLSearchParams(window.location.search);
        const tecnicoId = urlParams.get('tecnico_id') || '';
        
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'Nova Ordem de Serviço',
                html: `
                    <form id="nova-ordem-form">
                        <div class="mb-3">
                            <label for="cliente" class="form-label">Cliente</label>
                            <select class="form-select" id="cliente">
                                <option value="">Selecione o cliente...</option>
                                <!-- Aqui seriam carregados os clientes reais do sistema -->
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="servico" class="form-label">Tipo de Serviço</label>
                            <select class="form-select" id="servico">
                                <option value="manutencao">Manutenção</option>
                                <option value="instalacao">Instalação</option>
                                <option value="suporte">Suporte</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="data" class="form-label">Data de Agendamento</label>
                            <input type="date" class="form-control" id="data" value="${dataStr}">
                        </div>
                        <div class="mb-3">
                            <label for="horario" class="form-label">Horário</label>
                            <input type="time" class="form-control" id="horario" value="09:00">
                        </div>
                        <div class="mb-3">
                            <label for="descricao" class="form-label">Descrição</label>
                            <textarea class="form-control" id="descricao" rows="3"></textarea>
                        </div>
                    </form>
                `,
                showCancelButton: true,
                confirmButtonText: 'Continuar',
                cancelButtonText: 'Cancelar',
                focusConfirm: false,
                preConfirm: () => {
                    // Validação básica
                    const cliente = document.getElementById('cliente').value;
                    const data = document.getElementById('data').value;
                    
                    if (!cliente) {
                        Swal.showValidationMessage('Por favor, selecione um cliente');
                        return false;
                    }
                    
                    if (!data) {
                        Swal.showValidationMessage('Por favor, informe a data de agendamento');
                        return false;
                    }
                    
                    return {
                        cliente: cliente,
                        servico: document.getElementById('servico').value,
                        data: data,
                        horario: document.getElementById('horario').value,
                        descricao: document.getElementById('descricao').value
                    };
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    // Redirecionar para a página de criação de ordem
                    let url = '/ordens/nova/';
                    
                    // Adicionar parâmetros à URL
                    const params = new URLSearchParams();
                    
                    if (result.value.cliente) {
                        params.append('cliente_id', result.value.cliente);
                    }
                    
                    if (result.value.data) {
                        params.append('data', result.value.data);
                    }
                    
                    if (result.value.horario) {
                        params.append('horario', result.value.horario);
                    }
                    
                    if (tecnicoId) {
                        params.append('tecnico_id', tecnicoId);
                    }
                    
                    if (result.value.servico) {
                        params.append('servico', result.value.servico);
                    }
                    
                    if (result.value.descricao) {
                        params.append('descricao', result.value.descricao);
                    }
                    
                    // Adicionar parâmetros à URL se existirem
                    if (params.toString()) {
                        url += '?' + params.toString();
                    }
                    
                    // Redirecionar para a página de criação
                    window.location.href = url;
                }
            });
            
            // Carregar clientes da API
            carregarClientes();
        } else {
            // Fallback se o SweetAlert não estiver disponível
            window.location.href = `/ordens/nova/?data=${dataStr}${tecnicoId ? '&tecnico_id=' + tecnicoId : ''}`;
        }
    };
    
    // Função para carregar clientes via API
    function carregarClientes() {
        const selectCliente = document.getElementById('cliente');
        
        if (!selectCliente) return;
        
        // Adicionar opção de carregando
        selectCliente.innerHTML = '<option value="">Carregando clientes...</option>';
        
        // URL da API de clientes
        const apiUrl = '/api/clientes/';
        
        // Fazer requisição para a API
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Falha ao carregar clientes');
                }
                return response.json();
            })
            .then(data => {
                // Limpar select
                selectCliente.innerHTML = '<option value="">Selecione o cliente...</option>';
                
                // Adicionar clientes ao select
                if (data && data.length > 0) {
                    data.forEach(cliente => {
                        const option = document.createElement('option');
                        option.value = cliente.id;
                        option.textContent = cliente.nome;
                        selectCliente.appendChild(option);
                    });
                } else {
                    // Se não houver clientes, mostrar mensagem
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'Nenhum cliente encontrado';
                    option.disabled = true;
                    selectCliente.appendChild(option);
                }
            })
            .catch(error => {
                console.error('Erro ao carregar clientes:', error);
                
                // Mostrar opção de erro
                selectCliente.innerHTML = '<option value="">Erro ao carregar clientes</option>';
                
                // Adicionar opção para tentar novamente
                const option = document.createElement('option');
                option.value = 'retry';
                option.textContent = 'Clique para tentar novamente';
                selectCliente.appendChild(option);
                
                // Adicionar evento para tentar novamente
                selectCliente.addEventListener('change', function(e) {
                    if (e.target.value === 'retry') {
                        carregarClientes();
                    }
                });
            });
    }
    
    console.log('Recursos adicionais carregados com sucesso!');
})(); 