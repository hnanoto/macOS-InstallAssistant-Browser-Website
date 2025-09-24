#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Confirmação Automática
Testa todos os endpoints e funcionalidades do sistema de confirmação automática
"""

import requests
import json
import time
from datetime import datetime

class AutoConfirmationTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message="", data=None):
        """Log test results"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅ PASSOU" if success else "❌ FALHOU"
        
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'data': data,
            'timestamp': timestamp
        }
        
        self.test_results.append(result)
        print(f"[{timestamp}] {status} - {test_name}")
        if message:
            print(f"    📝 {message}")
        if data and not success:
            print(f"    📊 Dados: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print()
        
    def test_api_health(self):
        """Test API health check"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "API Health Check",
                    True,
                    f"API está funcionando - Status: {data.get('status', 'unknown')}"
                )
                return True
            else:
                self.log_test(
                    "API Health Check",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "API Health Check",
                False,
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    def test_auto_confirmation_status(self):
        """Test auto confirmation status endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/auto-confirmation/status")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test(
                        "Status do Sistema de Confirmação Automática",
                        True,
                        f"Sistema ativo: {data.get('auto_confirmation_enabled', False)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Status do Sistema de Confirmação Automática",
                        False,
                        data.get('error', 'Erro desconhecido'),
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Status do Sistema de Confirmação Automática",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Status do Sistema de Confirmação Automática",
                False,
                f"Erro: {str(e)}"
            )
            return False
    
    def test_start_auto_confirmation(self):
        """Test starting auto confirmation system"""
        try:
            response = self.session.post(f"{self.base_url}/api/auto-confirmation/start")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test(
                        "Iniciar Sistema de Confirmação Automática",
                        True,
                        data.get('message', 'Sistema iniciado')
                    )
                    return True
                else:
                    self.log_test(
                        "Iniciar Sistema de Confirmação Automática",
                        False,
                        data.get('error', 'Erro desconhecido'),
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Iniciar Sistema de Confirmação Automática",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Iniciar Sistema de Confirmação Automática",
                False,
                f"Erro: {str(e)}"
            )
            return False
    
    def test_get_confirmation_rules(self):
        """Test getting confirmation rules"""
        try:
            response = self.session.get(f"{self.base_url}/api/auto-confirmation/rules")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    rules = data.get('rules', {})
                    self.log_test(
                        "Obter Regras de Confirmação",
                        True,
                        f"Regras obtidas para {len(rules)} métodos de pagamento"
                    )
                    return True
                else:
                    self.log_test(
                        "Obter Regras de Confirmação",
                        False,
                        data.get('error', 'Erro desconhecido'),
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Obter Regras de Confirmação",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Obter Regras de Confirmação",
                False,
                f"Erro: {str(e)}"
            )
            return False
    
    def test_update_confirmation_rules(self):
        """Test updating confirmation rules"""
        try:
            test_rules = {
                "auto_confirm_threshold": 100.0,
                "max_confirmation_time": 3600,
                "require_proof_verification": True
            }
            
            response = self.session.put(
                f"{self.base_url}/api/auto-confirmation/rules/pix",
                json={"rules": test_rules}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test(
                        "Atualizar Regras de Confirmação",
                        True,
                        f"Regras atualizadas para método: {data.get('method', 'unknown')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Atualizar Regras de Confirmação",
                        False,
                        data.get('error', 'Erro desconhecido'),
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Atualizar Regras de Confirmação",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Atualizar Regras de Confirmação",
                False,
                f"Erro: {str(e)}"
            )
            return False
    
    def test_force_check_payment(self):
        """Test force checking a payment"""
        try:
            # Use a test payment ID
            test_payment_id = "test_payment_123"
            
            response = self.session.post(
                f"{self.base_url}/api/auto-confirmation/force-check/{test_payment_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                # This might fail if payment doesn't exist, but endpoint should respond
                self.log_test(
                    "Verificação Forçada de Pagamento",
                    True,
                    f"Verificação executada para payment_id: {test_payment_id}"
                )
                return True
            else:
                self.log_test(
                    "Verificação Forçada de Pagamento",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Verificação Forçada de Pagamento",
                False,
                f"Erro: {str(e)}"
            )
            return False
    
    def test_stop_auto_confirmation(self):
        """Test stopping auto confirmation system"""
        try:
            response = self.session.post(f"{self.base_url}/api/auto-confirmation/stop")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test(
                        "Parar Sistema de Confirmação Automática",
                        True,
                        data.get('message', 'Sistema parado')
                    )
                    return True
                else:
                    self.log_test(
                        "Parar Sistema de Confirmação Automática",
                        False,
                        data.get('error', 'Erro desconhecido'),
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Parar Sistema de Confirmação Automática",
                    False,
                    f"Status code: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Parar Sistema de Confirmação Automática",
                False,
                f"Erro: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all auto confirmation tests"""
        print("🤖 INICIANDO TESTES DO SISTEMA DE CONFIRMAÇÃO AUTOMÁTICA")
        print("=" * 60)
        print(f"🕒 Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 URL Base: {self.base_url}")
        print("=" * 60)
        print()
        
        # List of tests to run
        tests = [
            self.test_api_health,
            self.test_auto_confirmation_status,
            self.test_start_auto_confirmation,
            self.test_get_confirmation_rules,
            self.test_update_confirmation_rules,
            self.test_force_check_payment,
            self.test_stop_auto_confirmation
        ]
        
        # Run tests
        for test in tests:
            test()
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        print("=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"✅ Testes que passaram: {passed}/{total}")
        print(f"❌ Testes que falharam: {total - passed}/{total}")
        print(f"📈 Taxa de sucesso: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 TODOS OS TESTES PASSARAM! Sistema de confirmação automática funcionando corretamente.")
        else:
            print("\n⚠️ ALGUNS TESTES FALHARAM. Verifique os logs acima para mais detalhes.")
            print("\n❌ Testes que falharam:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        return passed == total

def main():
    """Main function"""
    tester = AutoConfirmationTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()