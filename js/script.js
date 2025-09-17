// Navigation
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            hamburger.classList.toggle('active');
        });
    }
    
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                const headerHeight = document.querySelector('header').offsetHeight;
                const targetPosition = targetSection.offsetTop - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                if (navMenu.classList.contains('active')) {
                    navMenu.classList.remove('active');
                    hamburger.classList.remove('active');
                }
            }
        });
    });
    
    // Demo tabs functionality
    const demoTabs = document.querySelectorAll('.demo-tab');
    const demoPanels = document.querySelectorAll('.demo-panel');
    
    demoTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and panels
            demoTabs.forEach(t => t.classList.remove('active'));
            demoPanels.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding panel
            this.classList.add('active');
            const targetPanel = document.getElementById(`demo-${targetTab}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
    
    // Header background on scroll
    window.addEventListener('scroll', function() {
        const header = document.querySelector('header');
        if (window.scrollY > 100) {
            header.style.background = 'rgba(255, 255, 255, 0.98)';
        } else {
            header.style.background = 'rgba(255, 255, 255, 0.95)';
        }
    });
});

// Demo simulation functions
function simulateInterface() {
    showDemoModal('Interface Principal', [
        '🖥️ Carregando interface principal...',
        '📋 Listando versões do macOS disponíveis...',
        '✅ macOS Sonoma 14.2.1 - Disponível',
        '✅ macOS Ventura 13.6.3 - Disponível', 
        '✅ macOS Monterey 12.7.2 - Disponível',
        '🔍 Filtros aplicados com sucesso',
        '📊 Interface carregada - Pronto para download!'
    ]);
}

function simulateDownloads() {
    showDemoModal('Gerenciador de Downloads', [
        '📥 Iniciando download do macOS Sonoma...',
        '🚀 Velocidade: 45.2 MB/s',
        '📊 Progresso: 15% (1.2 GB de 8.1 GB)',
        '⏸️ Download pausado pelo usuário',
        '▶️ Download retomado',
        '🔍 Verificando integridade do arquivo...',
        '✅ Checksum SHA256 verificado com sucesso!',
        '🎉 Download concluído!'
    ]);
}

function simulateSerial() {
    showDemoModal('Gerador de Serial', [
        '🔑 Iniciando gerador de serial...',
        '📧 Email: demo@exemplo.com',
        '🔐 Gerando serial único...',
        '✨ Serial gerado: A3F2-B8C1-9D4E-7F6A',
        '🔍 Validando serial...',
        '✅ Serial válido e único',
        '📄 Exportando para CSV...',
        '💾 Arquivo salvo: serials_demo.csv',
        '🎯 Sistema de licenciamento ativo!'
    ]);
}

function showDemoModal(title, steps) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'demo-modal';
    modal.innerHTML = `
        <div class="demo-modal-content">
            <div class="demo-modal-header">
                <h3>🎮 Demo: ${title}</h3>
                <button class="demo-modal-close">&times;</button>
            </div>
            <div class="demo-modal-body">
                <div class="demo-terminal"></div>
            </div>
        </div>
    `;
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
        .demo-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            animation: fadeIn 0.3s ease;
        }
        
        .demo-modal-content {
            background: #1e1e1e;
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        .demo-modal-header {
            background: #2d2d2d;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #444;
        }
        
        .demo-modal-header h3 {
            color: #fff;
            margin: 0;
            font-size: 1.2rem;
        }
        
        .demo-modal-close {
            background: none;
            border: none;
            color: #fff;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.3s ease;
        }
        
        .demo-modal-close:hover {
            background: #444;
        }
        
        .demo-modal-body {
            padding: 20px;
        }
        
        .demo-terminal {
            background: #000;
            border-radius: 8px;
            padding: 20px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.6;
            color: #00ff00;
            min-height: 300px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .demo-terminal-line {
            margin-bottom: 8px;
            opacity: 0;
            animation: typeIn 0.5s ease forwards;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes typeIn {
            from { 
                opacity: 0;
                transform: translateX(-10px);
            }
            to { 
                opacity: 1;
                transform: translateX(0);
            }
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(modal);
    
    // Close modal functionality
    const closeBtn = modal.querySelector('.demo-modal-close');
    const closeModal = () => {
        modal.remove();
        style.remove();
    };
    
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    
    // Simulate terminal output
    const terminal = modal.querySelector('.demo-terminal');
    let stepIndex = 0;
    
    function addStep() {
        if (stepIndex < steps.length) {
            const line = document.createElement('div');
            line.className = 'demo-terminal-line';
            line.textContent = `$ ${steps[stepIndex]}`;
            line.style.animationDelay = `${stepIndex * 0.1}s`;
            terminal.appendChild(line);
            
            stepIndex++;
            setTimeout(addStep, 800);
        } else {
            // Add completion message
            setTimeout(() => {
                const completeLine = document.createElement('div');
                completeLine.className = 'demo-terminal-line';
                completeLine.textContent = '$ Demo concluída! Pressione ESC ou clique fora para fechar.';
                completeLine.style.color = '#ffff00';
                completeLine.style.fontWeight = 'bold';
                terminal.appendChild(completeLine);
            }, 1000);
        }
    }
    
    // Start simulation
    setTimeout(addStep, 500);
    
    // ESC key to close
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', escHandler);
        }
    });
}

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll('.feature-card, .support-card, .download-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Download tracking
document.addEventListener('DOMContentLoaded', () => {
    const downloadLinks = document.querySelectorAll('a[download]');
    downloadLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Track download event
            console.log('Download iniciado:', link.href);
            
            // Show download notification
            showNotification('📥 Download iniciado! Verifique sua pasta de Downloads.', 'success');
        });
    });
});

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10001;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        }
        
        .notification-success {
            background: #28a745;
        }
        
        .notification-info {
            background: #007AFF;
        }
        
        .notification-warning {
            background: #ffc107;
            color: #000;
        }
        
        .notification-error {
            background: #dc3545;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(notification);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
            style.remove();
        }, 300);
    }, 4000);
}