#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste Completo do Sistema de Pagamentos
Testa todo o fluxo: criação, verificação, confirmação e notificações
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configurações
API_BASE_URL = "http://localhost:5001"
TEST_EMAIL = "teste@exemplo.com"
TEST_AMOUNT = 100.00

class PaymentFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.payment_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] {status} - {test_name}"
        if details:
            message += f" | {details}"
        print(message)
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': timestamp
        })
    
    def test_api_health(self):
        """Teste 1: Verificar se a API está funcionando"""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/health")
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f" | Uptime: {data.get('uptime', 'N/A')}"
            self.log_test("API Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("API Health Check", False, f"Erro: {str(e)}")
            return False
    
    def test_create_payment(self):
        """Teste 2: Criar um novo pagamento PIX"""
        try:
            payment_data = {
                "email": TEST_EMAIL,
                "amount": TEST_AMOUNT,
                "name": "Usuário Teste",
                "country": "BR"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/create-pix-payment",
                json=payment_data
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.payment_id = data.get('payment_id')
                details = f"Payment ID: {self.payment_id}"
            else:
                details = f"Status: {response.status_code} | {response.text}"
            
            self.log_test("Criar Pagamento", success, details)
            return success
        except Exception as e:
            self.log_test("Criar Pagamento", False, f"Erro: {str(e)}")
            return False
    
    def test_payment_status(self):
        """Teste 3: Verificar status do pagamento"""
        if not self.payment_id:
            self.log_test("Verificar Status", False, "Payment ID não disponível")
            return False
        
        try:
            response = self.session.get(
                f"{API_BASE_URL}/api/payment-status/{self.payment_id}"
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                status = data.get('status', 'unknown')
                details = f"Status: {status}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Verificar Status", success, details)
            return success
        except Exception as e:
            self.log_test("Verificar Status", False, f"Erro: {str(e)}")
            return False
    
    def test_transaction_verification(self):
        """Teste 4: Verificação de transação em tempo real"""
        if not self.payment_id:
            self.log_test("Verificação de Transação", False, "Payment ID não disponível")
            return False
        
        try:
            verification_data = {
                "payment_id": self.payment_id,
                "transaction_hash": "test_hash_123456",
                "amount": TEST_AMOUNT
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/verify-transaction",
                json=verification_data
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                verified = data.get('verified', False)
                details = f"Verificado: {verified}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Verificação de Transação", success, details)
            return success
        except Exception as e:
            self.log_test("Verificação de Transação", False, f"Erro: {str(e)}")
            return False
    
    def test_auto_confirmation(self):
        """Teste 5: Confirmação automática de pagamento"""
        if not self.payment_id:
            self.log_test("Confirmação Automática", False, "Payment ID não disponível")
            return False
        
        try:
            confirmation_data = {
                "payment_id": self.payment_id,
                "confirmed": True,
                "confirmation_method": "automatic_test"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/auto-confirm-payment",
                json=confirmation_data
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                confirmed = data.get('confirmed', False)
                serial = data.get('serial', 'N/A')
                details = f"Confirmado: {confirmed} | Serial: {serial}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Confirmação Automática", success, details)
            return success
        except Exception as e:
            self.log_test("Confirmação Automática", False, f"Erro: {str(e)}")
            return False
    
    def test_notification_system(self):
        """Teste 6: Sistema de notificações"""
        try:
            # Primeiro, verificar status do sistema de notificações
            response = self.session.get(f"{API_BASE_URL}/api/notifications/status")
            
            if response.status_code != 200:
                self.log_test("Sistema de Notificações", False, "Sistema não disponível")
                return False
            
            # Testar envio de notificação
            if self.payment_id:
                notification_data = {
                    "payment_id": self.payment_id
                }
                
                response = self.session.post(
                    f"{API_BASE_URL}/api/notifications/auto-process",
                    json=notification_data
                )
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    notifications_sent = data.get('notifications_sent', [])
                    details = f"Notificações enviadas: {len(notifications_sent)}"
                else:
                    details = f"Status: {response.status_code}"
            else:
                success = True
                details = "Sistema disponível (sem payment_id para teste)"
            
            self.log_test("Sistema de Notificações", success, details)
            return success
        except Exception as e:
            self.log_test("Sistema de Notificações", False, f"Erro: {str(e)}")
            return False
    
    def test_transaction_logs(self):
        """Teste 7: Sistema de logs de transações"""
        try:
            response = self.session.get(f"{API_BASE_URL}/api/transaction-logs")
            
            success = response.status_code == 200
            if success:
                data = response.json()
                logs_count = len(data.get('logs', []))
                details = f"Logs encontrados: {logs_count}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Sistema de Logs", success, details)
            return success
        except Exception as e:
            self.log_test("Sistema de Logs", False, f"Erro: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 Iniciando Teste Completo do Sistema de Pagamentos")
        print("=" * 60)
        
        tests = [
            self.test_api_health,
            self.test_create_payment,
            self.test_payment_status,
            self.test_transaction_verification,
            self.test_auto_confirmation,
            self.test_notification_system,
            self.test_transaction_logs
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(1)  # Pausa entre testes
        
        print("\n" + "=" * 60)
        print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! Sistema funcionando perfeitamente.")
            return True
        else:
            print(f"⚠️ {total - passed} teste(s) falharam. Verifique os logs acima.")
            return False
    
    def generate_report(self):
        """Gerar relatório detalhado"""
        print("\n📋 RELATÓRIO DETALHADO:")
        print("-" * 40)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} [{result['timestamp']}] {result['test']}")
            if result['details']:
                print(f"   └─ {result['details']}")
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📈 Taxa de Sucesso: {percentage:.1f}% ({passed}/{total})")

def main():
    """Função principal"""
    print("Sistema de Teste do Fluxo de Pagamentos")
    print(f"Testando API em: {API_BASE_URL}")
    print()
    
    tester = PaymentFlowTester()
    
    try:
        success = tester.run_all_tests()
        tester.generate_report()
        
        # Código de saída
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()