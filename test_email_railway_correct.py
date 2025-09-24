#!/usr/bin/env python3
"""
📧 TESTE CORRETO DO SERVIÇO DE EMAIL NO RAILWAY
===============================================

Este script testa o serviço de email no Railway usando os endpoints corretos da API básica.
"""

import requests
import json
import time
from datetime import datetime

class RailwayEmailCorrectTester:
    def __init__(self, railway_url="https://web-production-1513a.up.railway.app"):
        self.railway_url = railway_url
        self.results = []
        self.test_emails = [
            "teste.email.producao@gmail.com",
            "hackintoshandbeyond@gmail.com",
            "teste.entrega@outlook.com"
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
        
        status_icon = "✅" if status == "PASSOU" else "❌" if status == "FALHOU" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Detalhes: {details}")
    
    def test_railway_health(self):
        """Testa se o Railway está funcionando"""
        print("\n🏥 TESTANDO SAÚDE DO RAILWAY")
        print("=" * 40)
        
        try:
            response = requests.get(f"{self.railway_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Railway Health Check", "PASSOU", 
                             f"Status: {health_data.get('status')}, Versão: {health_data.get('version')}")
                return True
            else:
                self.log_test("Railway Health Check", "FALHOU", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Railway Health Check", "FALHOU", str(e))
            return False
    
    def test_email_endpoints_availability(self):
        """Testa se os endpoints de email estão disponíveis"""
        print("\n📧 TESTANDO DISPONIBILIDADE DOS ENDPOINTS DE EMAIL")
        print("=" * 60)
        
        # Endpoints corretos da API básica
        email_endpoints = [
            "/api/send-serial-email",
            "/api/notifications/status",
            "/api/notifications/send",
            "/api/debug/test-email",
            "/api/debug/notification-test"
        ]
        
        for endpoint in email_endpoints:
            try:
                # Teste básico para verificar se o endpoint existe
                if endpoint == "/api/notifications/status":
                    response = requests.get(f"{self.railway_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.railway_url}{endpoint}", json={}, timeout=10)
                
                # Esperamos algum tipo de resposta (não 404)
                if response.status_code != 404:
                    self.log_test(f"Endpoint {endpoint}", "PASSOU", f"Status: {response.status_code}")
                else:
                    self.log_test(f"Endpoint {endpoint}", "FALHOU", "Endpoint não encontrado")
                    
            except Exception as e:
                self.log_test(f"Endpoint {endpoint}", "FALHOU", str(e))
    
    def test_direct_email_sending(self):
        """Testa envio direto de email usando endpoint correto"""
        print("\n📤 TESTANDO ENVIO DIRETO DE EMAIL")
        print("=" * 40)
        
        for email in self.test_emails:
            try:
                # Teste de envio de serial usando endpoint correto
                serial_data = {
                    "email": email,
                    "name": "Cliente Teste Produção",
                    "serial": "PROD-1234-5678-9012",
                    "payment_id": "test_email_production"
                }
                
                response = requests.post(
                    f"{self.railway_url}/api/send-serial-email",
                    json=serial_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    self.log_test(f"Email de serial enviado para {email}", "PASSOU", 
                                 "Email deve ter sido entregue")
                else:
                    self.log_test(f"Email de serial enviado para {email}", "FALHOU", 
                                 f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Envio direto para {email}", "FALHOU", str(e))
    
    def test_notification_system(self):
        """Testa sistema de notificações"""
        print("\n🔔 TESTANDO SISTEMA DE NOTIFICAÇÕES")
        print("=" * 45)
        
        # Teste 1: Status do sistema de notificações
        try:
            response = requests.get(f"{self.railway_url}/api/notifications/status", timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("Status do Sistema de Notificações", "PASSOU", 
                             f"Status: {status_data}")
            else:
                self.log_test("Status do Sistema de Notificações", "FALHOU", 
                             f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Status do Sistema de Notificações", "FALHOU", str(e))
        
        # Teste 2: Envio de notificação
        try:
            notification_data = {
                "type": "payment_approved",
                "email": "teste.notificacao@gmail.com",
                "name": "Cliente Notificação",
                "payment_id": "test_notification_123",
                "message": "Seu pagamento foi aprovado!"
            }
            
            response = requests.post(
                f"{self.railway_url}/api/notifications/send",
                json=notification_data,
                timeout=15
            )
            
            if response.status_code == 200:
                self.log_test("Envio de Notificação", "PASSOU", "Notificação enviada")
            else:
                self.log_test("Envio de Notificação", "FALHOU", 
                             f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Envio de Notificação", "FALHOU", str(e))
    
    def test_debug_email_functions(self):
        """Testa funções de debug de email"""
        print("\n🔧 TESTANDO FUNÇÕES DE DEBUG DE EMAIL")
        print("=" * 50)
        
        # Teste 1: Teste de email básico
        try:
            email_data = {
                "to": "teste.debug@gmail.com",
                "subject": "Teste de Email em Produção",
                "body": "Este é um teste do sistema de email em produção."
            }
            
            response = requests.post(
                f"{self.railway_url}/api/debug/test-email",
                json=email_data,
                timeout=15
            )
            
            if response.status_code == 200:
                self.log_test("Teste de Email Debug", "PASSOU", "Email de teste enviado")
            else:
                self.log_test("Teste de Email Debug", "FALHOU", 
                             f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Teste de Email Debug", "FALHOU", str(e))
        
        # Teste 2: Teste de notificação
        try:
            notification_data = {
                "email": "teste.notificacao.debug@gmail.com",
                "name": "Cliente Debug",
                "type": "test"
            }
            
            response = requests.post(
                f"{self.railway_url}/api/debug/notification-test",
                json=notification_data,
                timeout=15
            )
            
            if response.status_code == 200:
                self.log_test("Teste de Notificação Debug", "PASSOU", "Notificação de teste enviada")
            else:
                self.log_test("Teste de Notificação Debug", "FALHOU", 
                             f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Teste de Notificação Debug", "FALHOU", str(e))
    
    def test_email_alternatives(self):
        """Testa alternativas de email (sem SendGrid)"""
        print("\n🔄 TESTANDO ALTERNATIVAS DE EMAIL")
        print("=" * 40)
        
        try:
            email_data = {
                "to": "teste.alternativa@gmail.com",
                "subject": "Teste de Email Alternativo",
                "body": "Teste usando sistema alternativo de email."
            }
            
            response = requests.post(
                f"{self.railway_url}/api/debug/free-email-test",
                json=email_data,
                timeout=15
            )
            
            if response.status_code == 200:
                self.log_test("Teste de Email Alternativo", "PASSOU", "Sistema alternativo funcionando")
            else:
                self.log_test("Teste de Email Alternativo", "FALHOU", 
                             f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Teste de Email Alternativo", "FALHOU", str(e))
    
    def test_email_error_handling(self):
        """Testa tratamento de erros de email"""
        print("\n⚠️ TESTANDO TRATAMENTO DE ERROS DE EMAIL")
        print("=" * 50)
        
        # Teste com email inválido
        try:
            invalid_email_data = {
                "email": "email_invalido",
                "name": "Cliente Teste",
                "serial": "TEST-1234-5678-9012"
            }
            
            response = requests.post(
                f"{self.railway_url}/api/send-serial-email",
                json=invalid_email_data,
                timeout=15
            )
            
            # Esperamos um erro 400 ou similar
            if response.status_code in [400, 422]:
                self.log_test("Tratamento de Email Inválido", "PASSOU", 
                             f"Status: {response.status_code}")
            else:
                self.log_test("Tratamento de Email Inválido", "FALHOU", 
                             f"Status inesperado: {response.status_code}")
                
        except Exception as e:
            self.log_test("Tratamento de Email Inválido", "FALHOU", str(e))
        
        # Teste com dados faltando
        try:
            incomplete_data = {
                "email": "teste@exemplo.com"
                # Faltando name e serial
            }
            
            response = requests.post(
                f"{self.railway_url}/api/send-serial-email",
                json=incomplete_data,
                timeout=15
            )
            
            if response.status_code in [400, 422]:
                self.log_test("Tratamento de Dados Incompletos", "PASSOU", 
                             f"Status: {response.status_code}")
            else:
                self.log_test("Tratamento de Dados Incompletos", "FALHOU", 
                             f"Status inesperado: {response.status_code}")
                
        except Exception as e:
            self.log_test("Tratamento de Dados Incompletos", "FALHOU", str(e))
    
    def test_email_performance(self):
        """Testa performance do sistema de email"""
        print("\n⚡ TESTANDO PERFORMANCE DO SISTEMA DE EMAIL")
        print("=" * 50)
        
        try:
            start_time = time.time()
            
            # Teste de envio de email
            email_data = {
                "email": "teste.performance@gmail.com",
                "name": "Cliente Performance",
                "serial": "PERF-1234-5678-9012"
            }
            
            response = requests.post(
                f"{self.railway_url}/api/send-serial-email",
                json=email_data,
                timeout=30
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code in [200, 400, 404]:  # Qualquer resposta válida
                status = "PASSOU" if duration < 10 else "AVISO"
                self.log_test("Performance do Sistema de Email", status, 
                             f"Tempo: {duration:.2f}s, Status: {response.status_code}")
            else:
                self.log_test("Performance do Sistema de Email", "FALHOU", 
                             f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Performance do Sistema de Email", "FALHOU", str(e))
    
    def run_all_tests(self):
        """Executa todos os testes de email em produção"""
        print("📧 INICIANDO TESTES CORRETOS DO SERVIÇO DE EMAIL EM PRODUÇÃO")
        print("=" * 70)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"🌐 URL Railway: {self.railway_url}")
        print(f"📧 Emails de Teste: {', '.join(self.test_emails)}")
        
        # Executar todos os testes
        if not self.test_railway_health():
            print("❌ Railway não está funcionando. Parando testes.")
            return
        
        self.test_email_endpoints_availability()
        self.test_direct_email_sending()
        self.test_notification_system()
        self.test_debug_email_functions()
        self.test_email_alternatives()
        self.test_email_error_handling()
        self.test_email_performance()
        
        # Gerar relatório final
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL - TESTES CORRETOS DE EMAIL EM PRODUÇÃO")
        print("=" * 70)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASSOU'])
        failed_tests = len([r for r in self.results if r['status'] == 'FALHOU'])
        warning_tests = len([r for r in self.results if r['status'] == 'AVISO'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 RESUMO EXECUTIVO:")
        print(f"   • Total de Testes: {total_tests}")
        print(f"   • Testes Aprovados: {passed_tests} ✅")
        print(f"   • Testes Falharam: {failed_tests} ❌")
        print(f"   • Avisos: {warning_tests} ⚠️")
        print(f"   • Taxa de Sucesso: {success_rate:.1f}%")
        print(f"   • Plataforma: Railway (Produção)")
        print(f"   • Emails Testados: {len(self.test_emails)}")
        
        print(f"\n📋 DETALHES DOS TESTES:")
        for result in self.results:
            status_icon = "✅" if result['status'] == "PASSOU" else "❌" if result['status'] == "FALHOU" else "⚠️"
            print(f"   {status_icon} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Salvar resultados em arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"email_railway_correct_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'warning_tests': warning_tests,
                    'success_rate': success_rate,
                    'platform': 'Railway Production',
                    'test_emails': self.test_emails
                },
                'railway_url': self.railway_url,
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_file}")
        
        # Conclusão
        if success_rate >= 80:
            print(f"\n🎯 CONCLUSÃO: SERVIÇO DE EMAIL EM PRODUÇÃO FUNCIONANDO EXCELENTEMENTE")
        elif success_rate >= 60:
            print(f"\n✅ CONCLUSÃO: SERVIÇO DE EMAIL EM PRODUÇÃO FUNCIONANDO BEM")
        elif success_rate >= 40:
            print(f"\n⚠️ CONCLUSÃO: SERVIÇO DE EMAIL EM PRODUÇÃO COM PROBLEMAS MENORES")
        else:
            print(f"\n❌ CONCLUSÃO: SERVIÇO DE EMAIL EM PRODUÇÃO CRÍTICO - REQUER ATENÇÃO")

if __name__ == "__main__":
    import sys
    
    railway_url = sys.argv[1] if len(sys.argv) > 1 else "https://web-production-1513a.up.railway.app"
    
    tester = RailwayEmailCorrectTester(railway_url)
    tester.run_all_tests()
