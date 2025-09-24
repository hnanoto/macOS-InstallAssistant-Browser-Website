#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO ESPECÍFICO - PROBLEMA SMTP
========================================

Este script diagnostica especificamente o problema de conectividade SMTP
e testa diferentes configurações para resolver o erro [Errno 101].
"""

import smtplib
import socket
import ssl
import time
from datetime import datetime

class SMTPDiagnostico:
    def __init__(self):
        self.results = []
        self.configs = [
            {
                "name": "Gmail SMTP (Porta 587 - TLS)",
                "server": "smtp.gmail.com",
                "port": 587,
                "use_tls": True,
                "use_ssl": False
            },
            {
                "name": "Gmail SMTP (Porta 465 - SSL)",
                "server": "smtp.gmail.com",
                "port": 465,
                "use_tls": False,
                "use_ssl": True
            },
            {
                "name": "Gmail SMTP (Porta 25 - SMTP Padrão)",
                "server": "smtp.gmail.com",
                "port": 25,
                "use_tls": True,
                "use_ssl": False
            },
            {
                "name": "Gmail SMTP (IP Direto - 587)",
                "server": "74.125.200.108",  # IP do Gmail
                "port": 587,
                "use_tls": True,
                "use_ssl": False
            }
        ]
        
    def log_test(self, test_name, status, details=""):
        """Registra resultado do teste"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "SUCESSO" else "❌" if status == "FALHOU" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Detalhes: {details}")
    
    def test_dns_resolution(self):
        """Testa resolução DNS"""
        print("\n🌐 TESTANDO RESOLUÇÃO DNS")
        print("=" * 40)
        
        try:
            ip = socket.gethostbyname('smtp.gmail.com')
            self.log_test("Resolução DNS smtp.gmail.com", "SUCESSO", f"IP: {ip}")
            return True
        except socket.gaierror as e:
            self.log_test("Resolução DNS smtp.gmail.com", "FALHOU", str(e))
            return False
    
    def test_port_connectivity(self, host, port):
        """Testa conectividade de porta"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return True, "Porta acessível"
            else:
                return False, f"Porta inacessível (código: {result})"
        except Exception as e:
            return False, str(e)
    
    def test_smtp_configuration(self, config):
        """Testa configuração SMTP específica"""
        print(f"\n📧 TESTANDO: {config['name']}")
        print("-" * 50)
        
        # Teste 1: Conectividade de porta
        host = config['server']
        port = config['port']
        
        port_ok, port_msg = self.test_port_connectivity(host, port)
        if not port_ok:
            self.log_test(f"Conectividade {config['name']}", "FALHOU", port_msg)
            return False
        
        self.log_test(f"Conectividade {config['name']}", "SUCESSO", port_msg)
        
        # Teste 2: Conexão SMTP
        try:
            if config['use_ssl']:
                server = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                server = smtplib.SMTP(host, port, timeout=10)
            
            if config['use_tls']:
                server.starttls()
            
            self.log_test(f"Conexão SMTP {config['name']}", "SUCESSO", "Conexão estabelecida")
            
            # Teste 3: Login (sem credenciais reais)
            try:
                # Tentar login com credenciais de teste
                server.login('test@example.com', 'test')
                self.log_test(f"Login SMTP {config['name']}", "SUCESSO", "Login funcionando")
            except smtplib.SMTPAuthenticationError:
                self.log_test(f"Login SMTP {config['name']}", "SUCESSO", "Servidor aceita login (credenciais incorretas)")
            except Exception as e:
                self.log_test(f"Login SMTP {config['name']}", "FALHOU", str(e))
            
            server.quit()
            return True
            
        except smtplib.SMTPConnectError as e:
            self.log_test(f"Conexão SMTP {config['name']}", "FALHOU", f"Erro de conexão: {e}")
            return False
        except smtplib.SMTPException as e:
            self.log_test(f"Conexão SMTP {config['name']}", "FALHOU", f"Erro SMTP: {e}")
            return False
        except Exception as e:
            self.log_test(f"Conexão SMTP {config['name']}", "FALHOU", f"Erro geral: {e}")
            return False
    
    def test_railway_network_restrictions(self):
        """Testa restrições de rede do Railway"""
        print("\n🚂 TESTANDO RESTRIÇÕES DE REDE DO RAILWAY")
        print("=" * 50)
        
        # Teste de conectividade básica
        test_hosts = [
            ("google.com", 80),
            ("gmail.com", 443),
            ("smtp.gmail.com", 587),
            ("smtp.gmail.com", 465),
            ("smtp.gmail.com", 25)
        ]
        
        for host, port in test_hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    self.log_test(f"Conectividade {host}:{port}", "SUCESSO", "Porta acessível")
                else:
                    self.log_test(f"Conectividade {host}:{port}", "FALHOU", f"Porta bloqueada (código: {result})")
            except Exception as e:
                self.log_test(f"Conectividade {host}:{port}", "FALHOU", str(e))
    
    def test_alternative_smtp_servers(self):
        """Testa servidores SMTP alternativos"""
        print("\n🔄 TESTANDO SERVIDORES SMTP ALTERNATIVOS")
        print("=" * 50)
        
        alternative_servers = [
            {
                "name": "Outlook SMTP",
                "server": "smtp-mail.outlook.com",
                "port": 587,
                "use_tls": True
            },
            {
                "name": "Yahoo SMTP",
                "server": "smtp.mail.yahoo.com",
                "port": 587,
                "use_tls": True
            },
            {
                "name": "SendGrid SMTP",
                "server": "smtp.sendgrid.net",
                "port": 587,
                "use_tls": True
            }
        ]
        
        for server_config in alternative_servers:
            try:
                server = smtplib.SMTP(server_config['server'], server_config['port'], timeout=10)
                if server_config['use_tls']:
                    server.starttls()
                
                self.log_test(f"Servidor {server_config['name']}", "SUCESSO", "Conexão estabelecida")
                server.quit()
                
            except Exception as e:
                self.log_test(f"Servidor {server_config['name']}", "FALHOU", str(e))
    
    def generate_recommendations(self):
        """Gera recomendações baseadas nos testes"""
        print("\n💡 RECOMENDAÇÕES BASEADAS NOS TESTES")
        print("=" * 50)
        
        successful_configs = [r for r in self.results if r['status'] == 'SUCESSO' and 'SMTP' in r['test']]
        failed_configs = [r for r in self.results if r['status'] == 'FALHOU' and 'SMTP' in r['test']]
        
        if successful_configs:
            print("✅ CONFIGURAÇÕES QUE FUNCIONAM:")
            for config in successful_configs:
                print(f"   • {config['test']}")
        
        if failed_configs:
            print("\n❌ CONFIGURAÇÕES QUE FALHARAM:")
            for config in failed_configs:
                print(f"   • {config['test']}: {config['details']}")
        
        print("\n🔧 SOLUÇÕES RECOMENDADAS:")
        print("   1. Usar porta 465 com SSL em vez de 587 com TLS")
        print("   2. Gerar nova App Password do Gmail")
        print("   3. Ativar SendGrid como alternativa")
        print("   4. Configurar Resend como backup")
        print("   5. Usar IP direto do Gmail se DNS falhar")
    
    def run_all_tests(self):
        """Executa todos os testes de diagnóstico"""
        print("🔍 INICIANDO DIAGNÓSTICO COMPLETO DO PROBLEMA SMTP")
        print("=" * 60)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        
        # Executar todos os testes
        self.test_dns_resolution()
        self.test_railway_network_restrictions()
        
        for config in self.configs:
            self.test_smtp_configuration(config)
        
        self.test_alternative_smtp_servers()
        
        # Gerar recomendações
        self.generate_recommendations()
        
        # Gerar relatório final
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório final"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - DIAGNÓSTICO SMTP")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['status'] == 'SUCESSO'])
        failed_tests = len([r for r in self.results if r['status'] == 'FALHOU'])
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 RESUMO:")
        print(f"   • Total de Testes: {total_tests}")
        print(f"   • Testes Bem-sucedidos: {successful_tests} ✅")
        print(f"   • Testes Falharam: {failed_tests} ❌")
        print(f"   • Taxa de Sucesso: {success_rate:.1f}%")
        
        print(f"\n📋 DETALHES DOS TESTES:")
        for result in self.results:
            status_icon = "✅" if result['status'] == "SUCESSO" else "❌" if result['status'] == "FALHOU" else "⚠️"
            print(f"   {status_icon} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"smtp_diagnostico_report_{timestamp}.json"
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'failed_tests': failed_tests,
                    'success_rate': success_rate
                },
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_file}")

if __name__ == "__main__":
    diagnostico = SMTPDiagnostico()
    diagnostico.run_all_tests()
