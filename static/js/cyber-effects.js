/**
 * CyberOS - Efeitos Visuais
 * Animações e efeitos interativos para uma interface futurista
 * Versão 1.0
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('%c🔒 CyberOS v1.0 %c| Sistema Futurista de Gestão', 
        'background: #7B68EE; color: white; padding: 5px; border-radius: 4px 0 0 4px;',
        'background: #111827; color: #00FFFF; padding: 5px; border-radius: 0 4px 4px 0;');
    
    // Inicializa todos os efeitos
    initCardEffects();
    initButtonEffects();
    initDynamicCounters();
    initTypewriterEffect();
    initLiveTimers();
    addDataVisualizationEffects();
    initNotificationSystem();
    initAudioEffects();
    
    // Easter egg
    console.log('%c🔑 Dica: Experimente digitar "matrix" no console', 'color: #00FFFF');
});

/**
 * Efeitos de hover para cards
 */
function initCardEffects() {
    const cards = document.querySelectorAll('.cyber-card');
    
    cards.forEach(card => {
        // Efeito de hover 3D
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const angleX = (y - centerY) / 15;
            const angleY = (centerX - x) / 15;
            
            this.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) translateY(-5px)`;
            this.style.boxShadow = `0 10px 20px rgba(123, 104, 238, 0.2), 
                                   ${(x - centerX) / 30}px ${(y - centerY) / 30}px 5px rgba(0, 255, 255, 0.1)`;
        });
        
        // Reset ao sair do hover
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });
}

/**
 * Efeito de ondulação para botões
 */
function initButtonEffects() {
    const buttons = document.querySelectorAll('.cyber-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Cria o elemento de efeito
            const ripple = document.createElement('span');
            ripple.classList.add('cyber-ripple');
            this.appendChild(ripple);
            
            // Posiciona o efeito na posição do clique
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            // Remove o elemento após a animação
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

/**
 * Contadores animados para estatísticas
 */
function initDynamicCounters() {
    const counters = document.querySelectorAll('.cyber-counter');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'), 10);
        const duration = parseInt(counter.getAttribute('data-duration') || '2000', 10);
        const decimals = parseInt(counter.getAttribute('data-decimals') || '0', 10);
        const prefix = counter.getAttribute('data-prefix') || '';
        const suffix = counter.getAttribute('data-suffix') || '';
        
        let startTimestamp = null;
        const startValue = 0;
        
        // Só inicia a contagem quando o elemento estiver visível
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    requestAnimationFrame(step);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        observer.observe(counter);
        
        // Função de animação
        function step(timestamp) {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const currentValue = Math.floor(progress * (target - startValue) + startValue);
            
            counter.textContent = `${prefix}${currentValue.toFixed(decimals)}${suffix}`;
            
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }
    });
}

/**
 * Efeito de digitação para textos
 */
function initTypewriterEffect() {
    const elements = document.querySelectorAll('.cyber-type');
    
    elements.forEach(element => {
        const text = element.textContent;
        const speed = parseInt(element.getAttribute('data-speed') || '50', 10);
        
        element.textContent = '';
        
        // Só inicia a digitação quando o elemento estiver visível
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    let i = 0;
                    const interval = setInterval(() => {
                        if (i < text.length) {
                            element.textContent += text.charAt(i);
                            i++;
                        } else {
                            clearInterval(interval);
                            element.classList.add('cyber-type-done');
                        }
                    }, speed);
                    
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        observer.observe(element);
    });
}

/**
 * Timers e relógios em tempo real
 */
function initLiveTimers() {
    const liveClocks = document.querySelectorAll('.cyber-clock');
    const countdowns = document.querySelectorAll('.cyber-countdown');
    
    // Relógios em tempo real
    if (liveClocks.length > 0) {
        setInterval(() => {
            const now = new Date();
            
            liveClocks.forEach(clock => {
                const format = clock.getAttribute('data-format') || 'time';
                let timeString = '';
                
                if (format === 'time') {
                    timeString = now.toLocaleTimeString();
                } else if (format === 'date') {
                    timeString = now.toLocaleDateString();
                } else if (format === 'datetime') {
                    timeString = now.toLocaleString();
                }
                
                clock.textContent = timeString;
            });
        }, 1000);
    }
    
    // Contadores regressivos
    countdowns.forEach(countdown => {
        const targetDate = new Date(countdown.getAttribute('data-target')).getTime();
        
        const timer = setInterval(() => {
            const now = new Date().getTime();
            const distance = targetDate - now;
            
            if (distance < 0) {
                clearInterval(timer);
                countdown.textContent = countdown.getAttribute('data-complete-text') || 'Concluído';
                countdown.classList.add('cyber-countdown-complete');
                return;
            }
            
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);
            
            countdown.innerHTML = `
                <span class="cyber-countdown-item">${days}<small>d</small></span>
                <span class="cyber-countdown-item">${hours}<small>h</small></span>
                <span class="cyber-countdown-item">${minutes}<small>m</small></span>
                <span class="cyber-countdown-item">${seconds}<small>s</small></span>
            `;
        }, 1000);
    });
}

/**
 * Efeitos para visualizações de dados
 */
function addDataVisualizationEffects() {
    // Verificar se a biblioteca Chart.js está disponível
    if (typeof Chart !== 'undefined') {
        // Definir cores temáticas para os gráficos
        Chart.defaults.color = '#a0aec0';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        
        // Temas personalizados para os gráficos
        const cyberChartTheme = {
            backgroundColor: 'rgba(123, 104, 238, 0.2)',
            borderColor: '#7B68EE',
            pointBackgroundColor: '#00FFFF',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: '#00FFFF'
        };
        
        // Procurar por canvas para gráficos
        const chartCanvases = document.querySelectorAll('.cyber-chart');
        
        chartCanvases.forEach(canvas => {
            const type = canvas.getAttribute('data-type') || 'line';
            const dataUrl = canvas.getAttribute('data-url');
            
            if (dataUrl) {
                // Carrega dados da URL
                fetch(dataUrl)
                    .then(response => response.json())
                    .then(data => {
                        // Cria gráfico com os dados carregados
                        createChart(canvas, type, data);
                    })
                    .catch(error => {
                        console.error('Erro ao carregar dados do gráfico:', error);
                        canvas.innerHTML = 'Erro ao carregar dados';
                    });
            } else {
                // Verifica se há dados em um elemento próximo
                const dataElement = document.getElementById(canvas.getAttribute('data-source'));
                if (dataElement) {
                    try {
                        const data = JSON.parse(dataElement.textContent);
                        createChart(canvas, type, data);
                    } catch (e) {
                        console.error('Erro ao processar dados do gráfico:', e);
                    }
                }
            }
        });
        
        function createChart(canvas, type, data) {
            // Configuração base do gráfico
            const config = {
                type: type,
                data: data,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: {
                                font: {
                                    family: "'Roboto', sans-serif"
                                }
                            }
                        }
                    }
                }
            };
            
            // Configurações específicas por tipo
            if (type === 'line') {
                config.options.elements = {
                    line: {
                        tension: 0.4,
                        borderWidth: 2
                    },
                    point: {
                        radius: 3,
                        hoverRadius: 6
                    }
                };
            }
            
            new Chart(canvas, config);
        }
    }
    
    // Animação para barras de progresso
    const progressBars = document.querySelectorAll('.cyber-progress-fill');
    
    progressBars.forEach(bar => {
        const targetPercent = bar.getAttribute('data-percent') || '0';
        
        // Anima a barra quando visível
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        bar.style.width = targetPercent + '%';
                    }, 200);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        observer.observe(bar);
    });
}

/**
 * Sistema de notificações
 */
function initNotificationSystem() {
    // Checar se existe um container para notificações
    let notificationContainer = document.querySelector('#cyber-notification-container');
    
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'cyber-notification-container';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.right = '1.5rem';
        notificationContainer.style.bottom = '1.5rem';
        notificationContainer.style.zIndex = '9999';
        document.body.appendChild(notificationContainer);
    }
    
    // Função global para mostrar notificações
    window.showCyberNotification = function(options) {
        const defaults = {
            title: 'Notificação',
            message: 'Esta é uma notificação do sistema',
            type: 'info', // info, success, warning, error
            duration: 5000,
            icon: null
        };
        
        const settings = { ...defaults, ...options };
        
        // Criar o elemento de notificação
        const notification = document.createElement('div');
        notification.className = `cyber-notification cyber-notification-${settings.type}`;
        
        // Determinar o ícone com base no tipo
        let iconClass = 'fas fa-info-circle';
        if (settings.icon) {
            iconClass = settings.icon;
        } else {
            switch (settings.type) {
                case 'success':
                    iconClass = 'fas fa-check-circle';
                    break;
                case 'warning':
                    iconClass = 'fas fa-exclamation-triangle';
                    break;
                case 'error':
                    iconClass = 'fas fa-times-circle';
                    break;
            }
        }
        
        // Estrutura da notificação
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="${iconClass}"></i>
            </div>
            <div class="notification-content">
                <h4>${settings.title}</h4>
                <p>${settings.message}</p>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Adicionar ao container
        notificationContainer.appendChild(notification);
        
        // Mostrar com animação
        setTimeout(() => {
            notification.classList.add('visible');
        }, 10);
        
        // Configurar o fechamento
        const closeButton = notification.querySelector('.notification-close');
        closeButton.addEventListener('click', () => {
            closeNotification(notification);
        });
        
        // Fechar automaticamente após a duração
        if (settings.duration > 0) {
            setTimeout(() => {
                closeNotification(notification);
            }, settings.duration);
        }
        
        // Retornar referência
        return notification;
    };
    
    // Função para fechar notificação com animação
    function closeNotification(notification) {
        notification.classList.remove('visible');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
}

/**
 * Efeitos de áudio para interações
 */
function initAudioEffects() {
    const audioEnabled = localStorage.getItem('cyberAudioEnabled') !== 'false';
    
    // Precarregar sons
    const sounds = {
        click: new Audio('/static/audio/click.mp3'),
        notify: new Audio('/static/audio/notify.mp3'),
        success: new Audio('/static/audio/success.mp3'),
        error: new Audio('/static/audio/error.mp3')
    };
    
    // Verificar e lidar com erros de carregamento
    for (const key in sounds) {
        sounds[key].addEventListener('error', function() {
            console.warn(`Áudio ${key} não pôde ser carregado. Desativando efeitos sonoros.`);
            delete sounds[key];
        });
    }
    
    // Adicionar áudio aos botões
    if (audioEnabled) {
        document.querySelectorAll('.cyber-btn').forEach(button => {
            button.addEventListener('click', () => {
                playSound('click');
            });
        });
    }
    
    // Sobrescrever a função de notificação para adicionar sons
    const originalShowNotification = window.showCyberNotification;
    if (originalShowNotification) {
        window.showCyberNotification = function(options) {
            const notification = originalShowNotification(options);
            
            // Tocar som adequado para o tipo de notificação
            if (options.type === 'success') {
                playSound('success');
            } else if (options.type === 'error') {
                playSound('error');
            } else {
                playSound('notify');
            }
            
            return notification;
        };
    }
    
    // Função para reproduzir sons
    function playSound(soundName) {
        if (!audioEnabled || !sounds[soundName]) return;
        
        try {
            const sound = sounds[soundName];
            sound.currentTime = 0;
            sound.play().catch(e => {
                // Lidar com error comum de autoplay
                console.warn('Erro ao reproduzir áudio:', e);
            });
        } catch (e) {
            console.error('Erro ao reproduzir som:', e);
        }
    }
    
    // Adicionar controle de áudio ao objeto global
    window.cyberAudio = {
        enable: function() {
            localStorage.setItem('cyberAudioEnabled', 'true');
            return true;
        },
        disable: function() {
            localStorage.setItem('cyberAudioEnabled', 'false');
            return false;
        },
        toggle: function() {
            const newState = localStorage.getItem('cyberAudioEnabled') === 'false';
            localStorage.setItem('cyberAudioEnabled', newState.toString());
            return newState;
        },
        playSound: playSound
    };
}

/**
 * Easter Egg - Efeito Matrix
 */
const matrixInitialized = false;

function initMatrix() {
    if (matrixInitialized) return;
    
    const canvas = document.createElement('canvas');
    canvas.id = 'matrix-effect';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '9998';
    canvas.style.opacity = '0.8';
    canvas.style.pointerEvents = 'none';
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    // Ajustar tamanho do canvas
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    
    // Caracteres para o efeito
    const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
    const columns = Math.floor(canvas.width / 20);
    const drops = [];
    
    // Inicializar posições
    for (let i = 0; i < columns; i++) {
        drops[i] = Math.random() * -100;
    }
    
    // Desenhar o efeito
    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#0F0';
        ctx.font = '15px monospace';
        
        for (let i = 0; i < drops.length; i++) {
            // Caractere aleatório
            const text = chars[Math.floor(Math.random() * chars.length)];
            ctx.fillText(text, i * 20, drops[i] * 20);
            
            // Reiniciar quando sair da tela
            if (drops[i] * 20 > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            
            // Mover para baixo
            drops[i]++;
        }
    }
    
    // Animar
    const interval = setInterval(draw, 35);
    
    // Remover após 10 segundos
    setTimeout(() => {
        clearInterval(interval);
        canvas.remove();
    }, 10000);
    
    return true;
}

// Adicionar o Easter Egg ao console
window.matrix = function() {
    console.log('%c 🔓 Iniciando sequência Matrix...', 'color: #00FF00; font-weight: bold');
    initMatrix();
    return '%c SISTEMA INVADIDO! ', 'background: #00FF00; color: black; font-weight: bold; padding: 3px;';
}; 