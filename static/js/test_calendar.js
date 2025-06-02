/**
 * Script para testar o funcionamento do calendário
 * Este arquivo verifica se o calendário está sendo inicializado corretamente
 */

console.log("🔍 Script de diagnóstico do calendário carregado");

// Executar verificação quando a página estiver carregada
document.addEventListener('DOMContentLoaded', function() {
    console.log("📋 Iniciando diagnóstico do calendário");
    
    // Verificar se o FullCalendar está carregado
    if (typeof FullCalendar === 'undefined') {
        console.error("❌ ERRO: A biblioteca FullCalendar não está carregada!");
        mostrarErroNaPagina("A biblioteca FullCalendar não foi carregada. Verifique se o link para o CDN está correto.");
        return;
    } else {
        console.log("✅ FullCalendar está carregado corretamente");
    }
    
    // Verificar se o elemento do calendário existe
    const elementoCalendario = document.getElementById('calendario-disponibilidade');
    if (!elementoCalendario) {
        console.error("❌ ERRO: Elemento do calendário (ID: calendario-disponibilidade) não encontrado!");
        mostrarErroNaPagina("O elemento HTML do calendário não foi encontrado na página.");
        return;
    } else {
        console.log("✅ Elemento do calendário encontrado");
    }
    
    // Verificar se o calendário foi inicializado
    if (typeof window.calendar === 'undefined') {
        console.error("❌ ERRO: Instância do calendário não inicializada!");
        mostrarErroNaPagina("O calendário não foi inicializado corretamente.");
        
        // Tentar inicializar o calendário
        console.log("🔧 Tentando inicializar o calendário manualmente...");
        
        try {
            // Obter ID do técnico da URL
            const urlParams = new URLSearchParams(window.location.search);
            const tecnicoId = urlParams.get('tecnico_id') || document.querySelector('meta[name="tecnico-id"]')?.getAttribute('content') || '1';
            
            window.calendar = new FullCalendar.Calendar(elementoCalendario, {
                locale: 'pt-br',
                initialView: 'dayGridMonth',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,listWeek'
                },
                events: [
                    {
                        title: 'Evento de Teste',
                        start: new Date().toISOString().split('T')[0],
                        color: '#3498db'
                    }
                ]
            });
            
            window.calendar.render();
            console.log("✅ Calendário inicializado manualmente com sucesso!");
            mostrarSucessoNaPagina("Calendário recuperado e inicializado pelo script de diagnóstico.");
        } catch (erro) {
            console.error("❌ Falha ao inicializar o calendário manualmente:", erro);
            mostrarErroNaPagina("Não foi possível inicializar o calendário: " + erro.message);
        }
    } else {
        console.log("✅ Instância do calendário encontrada");
        
        // Verificar se existem eventos no calendário
        const eventos = window.calendar.getEvents();
        console.log(`📊 Eventos presentes no calendário: ${eventos.length}`);
        
        if (eventos.length === 0) {
            console.warn("⚠️ O calendário não possui eventos");
            
            // Adicionar um evento de teste para verificar se o calendário está funcionando
            window.calendar.addEvent({
                title: 'Evento de Teste (Diagnóstico)',
                start: new Date().toISOString().split('T')[0],
                color: '#3498db'
            });
            
            console.log("✅ Evento de teste adicionado ao calendário");
        }
    }
    
    console.log("🏁 Diagnóstico do calendário concluído");
});

// Função para mostrar erro na página
function mostrarErroNaPagina(mensagem) {
    const container = document.getElementById('calendario-disponibilidade');
    if (container) {
        const alerta = document.createElement('div');
        alerta.className = 'alert alert-danger mt-3';
        alerta.innerHTML = `
            <strong>Erro no calendário:</strong> ${mensagem}
            <p class="mt-2 mb-0">
                <button class="btn btn-sm btn-outline-danger" onclick="location.reload()">
                    Recarregar Página
                </button>
            </p>
        `;
        container.parentNode.insertBefore(alerta, container);
    }
}

// Função para mostrar sucesso na página
function mostrarSucessoNaPagina(mensagem) {
    const container = document.getElementById('calendario-disponibilidade');
    if (container) {
        const alerta = document.createElement('div');
        alerta.className = 'alert alert-success mt-3';
        alerta.innerHTML = `
            <strong>Sucesso:</strong> ${mensagem}
            <button type="button" class="btn-close float-end" data-bs-dismiss="alert" aria-label="Fechar"></button>
        `;
        container.parentNode.insertBefore(alerta, container);
    }
} 