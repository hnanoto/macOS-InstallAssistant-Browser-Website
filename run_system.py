#!/usr/bin/env python3
"""
Script de Execução do Sistema de Pagamentos Avançado
Inicia todos os componentes e executa testes de validação
"""

import os
import sys
import time
import subprocess
import threading
from datetime import datetime
import json

def print_banner():
    """Exibe banner do sistema"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚀 SISTEMA DE PAGAMENTOS AVANÇADO 🚀                     ║
║                                                                              ║
║  ✅ Verificação de Transações Robusta                                        ║
║  ✅ Confirmação de Recebimento Automática                                    ║
║  ✅ Notificações Automáticas para Ambas as Partes                           ║
║  ✅ Interface Intuitiva e Livre de Erros                                     ║
║  ✅ Sistema de Testes e Validação Completo                                   ║
║                                                                              ║
║  Versão: 2.0.0 - Sistema Totalmente Funcional                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Verifica dependências necessárias"""
    print("🔍 Verificando dependências...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'stripe',
        'python-dotenv',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ Pacotes faltando: {', '.join(missing_packages)}")
        print("📦 Instale com: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ Todas as dependências estão instaladas!")
    return True

def check_environment():
    """Verifica configuração do ambiente"""
    print("\n🔧 Verificando configuração do ambiente...")
    
    # Verificar arquivo .env
    if os.path.exists('.env'):
        print("  ✅ Arquivo .env encontrado")
    else:
        print("  ⚠️ Arquivo .env não encontrado - usando configurações padrão")
    
    # Verificar diretórios necessários
    directories = ['uploads', 'logs']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  📁 Diretório criado: {directory}")
        else:
            print(f"  ✅ Diretório existe: {directory}")
    
    # Verificar SerialGenerator
    serial_generator_path = os.path.join(os.path.dirname(__file__), '../../macOS-InstallAssistant-Browser-2/macOS-InstallAssistant-Browser-2/SerialGenerator')
    if os.path.exists(serial_generator_path):
        print("  ✅ SerialGenerator encontrado")
    else:
        print("  ⚠️ SerialGenerator não encontrado - usando implementação Python")
    
    return True

def start_api_server():
    """Inicia servidor da API"""
    print("\n🚀 Iniciando servidor da API...")
    
    try:
        # Iniciar servidor em thread separada
        def run_server():
            os.system("python enhanced_payment_api.py")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Aguardar servidor iniciar
        print("⏳ Aguardando servidor iniciar...")
        time.sleep(5)
        
        # Verificar se servidor está rodando
        import requests
        try:
            response = requests.get("http://localhost:5001/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Servidor da API iniciado com sucesso!")
                return True
            else:
                print(f"❌ Servidor retornou status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao conectar com servidor: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return False

def run_tests():
    """Executa testes do sistema"""
    print("\n🧪 Executando testes do sistema...")
    
    try:
        # Executar testes
        result = subprocess.run([
            sys.executable, "test_payment_system.py", "http://localhost:5001"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Todos os testes passaram!")
            print("\n📊 Resultados dos testes:")
            print(result.stdout)
            return True
        else:
            print("❌ Alguns testes falharam!")
            print("\n📊 Resultados dos testes:")
            print(result.stdout)
            if result.stderr:
                print("\n❌ Erros:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Testes expiraram (timeout de 5 minutos)")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return False

def show_system_status():
    """Mostra status do sistema"""
    print("\n📊 Status do Sistema:")
    
    try:
        import requests
        
        # Verificar saúde da API
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API Status: {data.get('status', 'unknown')}")
            print(f"  📦 Versão: {data.get('version', 'unknown')}")
            print(f"  🎯 Recursos: {len(data.get('features', []))}")
        else:
            print(f"  ❌ API Status: HTTP {response.status_code}")
        
        # Verificar status de notificações
        try:
            response = requests.get("http://localhost:5001/api/enhanced/notification-status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"  📧 Notificações: {data.get('queue_size', 0)} na fila")
                print(f"  🔧 SMTP: {'Configurado' if data.get('smtp_configured', False) else 'Não configurado'}")
        except:
            print("  ⚠️ Status de notificações: Indisponível")
        
        # Verificar estatísticas de confirmação
        try:
            response = requests.get("http://localhost:5001/api/enhanced/confirmation-statistics", timeout=5)
            if response.status_code == 200:
                data = response.json()
                stats = data.get('statistics', {})
                print(f"  ✅ Confirmações: {stats.get('confirmed', 0)} confirmadas")
                print(f"  ⏳ Pendentes: {stats.get('pending', 0)}")
                print(f"  📈 Taxa de sucesso: {stats.get('success_rate', 0)}%")
        except:
            print("  ⚠️ Estatísticas de confirmação: Indisponível")
            
    except Exception as e:
        print(f"  ❌ Erro ao verificar status: {e}")

def show_usage_instructions():
    """Mostra instruções de uso"""
    print("\n📖 INSTRUÇÕES DE USO:")
    print("=" * 50)
    
    print("\n🌐 URLs Disponíveis:")
    print("  • API Principal: http://localhost:5001")
    print("  • Checkout Avançado: http://localhost:5001/enhanced_checkout.html")
    print("  • Health Check: http://localhost:5001/api/health")
    print("  • Status do Sistema: http://localhost:5001/api/enhanced/system-health")
    
    print("\n🔧 Comandos Úteis:")
    print("  • Testar sistema: python test_payment_system.py")
    print("  • Verificar logs: tail -f logs/*.log")
    print("  • Parar servidor: Ctrl+C")
    
    print("\n📧 Configuração de Email:")
    print("  • Edite o arquivo .env com suas credenciais SMTP")
    print("  • Ou configure SendGrid/Resend para melhor confiabilidade")
    
    print("\n🧪 Testes Disponíveis:")
    print("  • Teste completo: python test_payment_system.py")
    print("  • Teste específico: python -c \"from test_payment_system import *; tester = PaymentSystemTester(); print(tester.health_check())\"")
    
    print("\n📊 Monitoramento:")
    print("  • Logs em tempo real: tail -f notifications.json")
    print("  • Estatísticas: curl http://localhost:5001/api/enhanced/confirmation-statistics")
    print("  • Status: curl http://localhost:5001/api/enhanced/notification-status")

def main():
    """Função principal"""
    print_banner()
    
    print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
    
    # Verificar dependências
    if not check_dependencies():
        print("\n❌ Dependências faltando. Instale os pacotes necessários e tente novamente.")
        sys.exit(1)
    
    # Verificar ambiente
    if not check_environment():
        print("\n❌ Problemas na configuração do ambiente.")
        sys.exit(1)
    
    # Iniciar servidor
    if not start_api_server():
        print("\n❌ Falha ao iniciar servidor da API.")
        sys.exit(1)
    
    # Mostrar status
    show_system_status()
    
    # Perguntar se deve executar testes
    print("\n" + "=" * 50)
    response = input("🧪 Deseja executar os testes do sistema? (s/n): ").lower().strip()
    
    if response in ['s', 'sim', 'y', 'yes']:
        if run_tests():
            print("\n🎉 Sistema totalmente funcional e testado!")
        else:
            print("\n⚠️ Sistema funcionando, mas alguns testes falharam.")
    else:
        print("\n⏭️ Pulando testes. Execute 'python test_payment_system.py' quando necessário.")
    
    # Mostrar instruções
    show_usage_instructions()
    
    print("\n" + "=" * 50)
    print("🚀 Sistema de Pagamentos Avançado está rodando!")
    print("📖 Consulte SISTEMA_PAGAMENTOS_AVANCADO.md para documentação completa")
    print("🛑 Pressione Ctrl+C para parar o servidor")
    print("=" * 50)
    
    try:
        # Manter servidor rodando
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Parando servidor...")
        print("✅ Sistema finalizado com sucesso!")

if __name__ == '__main__':
    main()
