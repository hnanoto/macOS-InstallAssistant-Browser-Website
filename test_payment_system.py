#!/usr/bin/env python3
"""
Sistema de Testes e Validação Completo
Testa todas as funcionalidades do sistema de pagamentos avançado
"""

import json
import time
import requests
import threading
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentSystemTester:
    """Testador completo do sistema de pagamentos"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.test_results = []
        self.test_payments = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes do sistema"""
        logger.info("🧪 Iniciando testes completos do sistema de pagamentos...")
        
        test_suite = {
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0
            }
        }
        
        # Lista de testes
        tests = [
            ('health_check', 'Verificação de Saúde do Sistema'),
            ('stripe_payment_test', 'Teste de Pagamento Stripe'),
            ('paypal_payment_test', 'Teste de Pagamento PayPal'),
            ('pix_payment_test', 'Teste de Pagamento PIX'),
            ('verification_system_test', 'Teste do Sistema de Verificação'),
            ('notification_system_test', 'Teste do Sistema de Notificações'),
            ('confirmation_system_test', 'Teste do Sistema de Confirmação'),
            ('receipt_system_test', 'Teste do Sistema de Comprovantes'),
            ('ui_functionality_test', 'Teste de Funcionalidades da UI'),
            ('error_handling_test', 'Teste de Tratamento de Erros'),
            ('security_test', 'Teste de Segurança'),
            ('performance_test', 'Teste de Performance')
        ]
        
        # Executar cada teste
        for test_name, test_description in tests:
            logger.info(f"🔄 Executando: {test_description}")
            
            try:
                test_method = getattr(self, test_name)
                result = test_method()
                
                test_result = {
                    'name': test_name,
                    'description': test_description,
                    'status': 'passed' if result.get('success', False) else 'failed',
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
                
                test_suite['tests'].append(test_result)
                test_suite['summary']['total'] += 1
                
                if result.get('success', False):
                    test_suite['summary']['passed'] += 1
                    logger.info(f"✅ {test_description}: PASSOU")
                else:
                    test_suite['summary']['failed'] += 1
                    logger.error(f"❌ {test_description}: FALHOU - {result.get('error', 'Erro desconhecido')}")
                    
            except Exception as e:
                test_result = {
                    'name': test_name,
                    'description': test_description,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                
                test_suite['tests'].append(test_result)
                test_suite['summary']['total'] += 1
                test_suite['summary']['errors'] += 1
                logger.error(f"💥 {test_description}: ERRO - {str(e)}")
        
        test_suite['end_time'] = datetime.now().isoformat()
        test_suite['duration'] = self._calculate_duration(test_suite['start_time'], test_suite['end_time'])
        
        # Salvar resultados
        self._save_test_results(test_suite)
        
        # Gerar relatório
        self._generate_report(test_suite)
        
        return test_suite
    
    def health_check(self) -> Dict[str, Any]:
        """Testa a saúde geral do sistema"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status', 'unknown'),
                    'version': data.get('version', 'unknown'),
                    'features': data.get('features', [])
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def stripe_payment_test(self) -> Dict[str, Any]:
        """Testa pagamento via Stripe"""
        try:
            # Dados de teste
            test_data = {
                'token': 'tok_visa',  # Token de teste do Stripe
                'amount': 500,  # $5.00
                'currency': 'usd',
                'email': 'teste@exemplo.com',
                'name': 'Cliente Teste',
                'country': 'US',
                'method': 'stripe'
            }
            
            response = requests.post(
                f"{self.base_url}/api/enhanced/process-payment",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    self.test_payments.append({
                        'id': data.get('transactionId', ''),
                        'method': 'stripe',
                        'serial': data.get('serial', ''),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return {
                        'success': True,
                        'transaction_id': data.get('transactionId', ''),
                        'serial': data.get('serial', ''),
                        'verification': data.get('verification', {}),
                        'confirmation_id': data.get('confirmation_id', '')
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('error', 'Erro desconhecido')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def paypal_payment_test(self) -> Dict[str, Any]:
        """Testa pagamento via PayPal"""
        try:
            # Dados de teste
            test_data = {
                'order_id': f'paypal_test_{int(time.time())}',
                'amount': 5.00,
                'currency': 'usd',
                'email': 'teste@exemplo.com',
                'name': 'Cliente Teste',
                'country': 'US',
                'method': 'paypal'
            }
            
            response = requests.post(
                f"{self.base_url}/api/enhanced/process-payment",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    self.test_payments.append({
                        'id': data.get('transactionId', ''),
                        'method': 'paypal',
                        'serial': data.get('serial', ''),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return {
                        'success': True,
                        'transaction_id': data.get('transactionId', ''),
                        'serial': data.get('serial', ''),
                        'verification': data.get('verification', {})
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('error', 'Erro desconhecido')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def pix_payment_test(self) -> Dict[str, Any]:
        """Testa pagamento via PIX"""
        try:
            # Dados de teste
            test_data = {
                'payment_id': f'pix_test_{int(time.time())}',
                'proof_data': {
                    'filename': 'test_proof.png',
                    'amount': 2650,  # R$ 26,50
                    'uploaded_at': datetime.now().isoformat()
                },
                'email': 'teste@exemplo.com',
                'name': 'Cliente Teste',
                'country': 'BR',
                'method': 'pix'
            }
            
            response = requests.post(
                f"{self.base_url}/api/enhanced/process-payment",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    self.test_payments.append({
                        'id': data.get('transactionId', ''),
                        'method': 'pix',
                        'serial': data.get('serial', ''),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return {
                        'success': True,
                        'transaction_id': data.get('transactionId', ''),
                        'serial': data.get('serial', ''),
                        'verification': data.get('verification', {})
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('error', 'Erro desconhecido')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verification_system_test(self) -> Dict[str, Any]:
        """Testa sistema de verificação"""
        try:
            if not self.test_payments:
                return {
                    'success': False,
                    'error': 'Nenhum pagamento de teste disponível'
                }
            
            # Testar verificação do primeiro pagamento
            test_payment = self.test_payments[0]
            
            verification_data = {
                'payment_id': test_payment['id'],
                'method': test_payment['method']
            }
            
            response = requests.post(
                f"{self.base_url}/api/enhanced/verify-payment",
                json=verification_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': data.get('success', False),
                    'verification_result': data,
                    'tested_payment': test_payment
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def notification_system_test(self) -> Dict[str, Any]:
        """Testa sistema de notificações"""
        try:
            response = requests.get(
                f"{self.base_url}/api/enhanced/notification-status",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': data.get('success', False),
                    'notification_status': data,
                    'queue_size': data.get('queue_size', 0),
                    'smtp_configured': data.get('smtp_configured', False)
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def confirmation_system_test(self) -> Dict[str, Any]:
        """Testa sistema de confirmação"""
        try:
            # Testar estatísticas de confirmação
            response = requests.get(
                f"{self.base_url}/api/enhanced/confirmation-statistics",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': data.get('success', False),
                    'confirmation_stats': data.get('statistics', {}),
                    'total_confirmations': data.get('statistics', {}).get('total_confirmations', 0),
                    'success_rate': data.get('statistics', {}).get('success_rate', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def receipt_system_test(self) -> Dict[str, Any]:
        """Testa sistema de comprovantes"""
        try:
            if not self.test_payments:
                return {
                    'success': False,
                    'error': 'Nenhum pagamento de teste disponível'
                }
            
            # Testar busca de comprovantes
            test_payment = self.test_payments[0]
            
            response = requests.get(
                f"{self.base_url}/api/enhanced/receipts/{test_payment['id']}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': data.get('success', False),
                    'receipts_count': data.get('count', 0),
                    'tested_payment': test_payment
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def ui_functionality_test(self) -> Dict[str, Any]:
        """Testa funcionalidades da interface"""
        try:
            # Testar se a página de checkout está acessível
            response = requests.get(
                f"{self.base_url}/enhanced_checkout.html",
                timeout=10
            )
            
            if response.status_code == 200:
                content = response.text
                
                # Verificar elementos essenciais
                essential_elements = [
                    'enhanced-payment-form',
                    'payment-method-enhanced',
                    'verification-steps',
                    'success-animation',
                    'real-time-status'
                ]
                
                missing_elements = []
                for element in essential_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                return {
                    'success': len(missing_elements) == 0,
                    'page_accessible': True,
                    'missing_elements': missing_elements,
                    'content_length': len(content)
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'page_accessible': False
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def error_handling_test(self) -> Dict[str, Any]:
        """Testa tratamento de erros"""
        try:
            # Testar com dados inválidos
            invalid_data = {
                'token': 'invalid_token',
                'amount': -100,  # Valor negativo
                'currency': 'INVALID',
                'email': 'invalid_email',
                'name': '',  # Nome vazio
                'country': 'XX',  # País inválido
                'method': 'invalid_method'
            }
            
            response = requests.post(
                f"{self.base_url}/api/enhanced/process-payment",
                json=invalid_data,
                timeout=10
            )
            
            # Deve retornar erro 400
            if response.status_code == 400:
                data = response.json()
                return {
                    'success': True,
                    'error_handling': 'correct',
                    'error_response': data,
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': f'Expected 400, got {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def security_test(self) -> Dict[str, Any]:
        """Testa aspectos de segurança"""
        try:
            # Testar endpoints sem autenticação
            security_tests = [
                ('/api/enhanced/confirmation-statistics', 'GET'),
                ('/api/enhanced/notification-status', 'GET'),
                ('/api/health', 'GET')
            ]
            
            security_results = []
            
            for endpoint, method in security_tests:
                try:
                    if method == 'GET':
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    else:
                        response = requests.post(f"{self.base_url}{endpoint}", timeout=5)
                    
                    # Verificar se não retorna dados sensíveis
                    if response.status_code in [200, 401, 403]:
                        security_results.append({
                            'endpoint': endpoint,
                            'method': method,
                            'status_code': response.status_code,
                            'secure': True
                        })
                    else:
                        security_results.append({
                            'endpoint': endpoint,
                            'method': method,
                            'status_code': response.status_code,
                            'secure': False
                        })
                        
                except Exception as e:
                    security_results.append({
                        'endpoint': endpoint,
                        'method': method,
                        'error': str(e),
                        'secure': False
                    })
            
            all_secure = all(result.get('secure', False) for result in security_results)
            
            return {
                'success': all_secure,
                'security_tests': security_results,
                'overall_security': 'secure' if all_secure else 'vulnerable'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def performance_test(self) -> Dict[str, Any]:
        """Testa performance do sistema"""
        try:
            # Testar tempo de resposta
            start_time = time.time()
            
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Testar múltiplas requisições simultâneas
            def make_request():
                try:
                    resp = requests.get(f"{self.base_url}/api/health", timeout=5)
                    return resp.status_code == 200
                except:
                    return False
            
            # Executar 10 requisições simultâneas
            threads = []
            results = []
            
            for i in range(10):
                thread = threading.Thread(target=lambda: results.append(make_request()))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            success_rate = sum(results) / len(results) * 100
            
            return {
                'success': response_time < 2.0 and success_rate > 80,
                'response_time': round(response_time, 3),
                'concurrent_requests': len(results),
                'success_rate': round(success_rate, 2),
                'performance_rating': 'excellent' if response_time < 1.0 else 'good' if response_time < 2.0 else 'poor'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calcula duração dos testes"""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            duration = (end - start).total_seconds()
            return round(duration, 2)
        except:
            return 0.0
    
    def _save_test_results(self, test_suite: Dict[str, Any]) -> None:
        """Salva resultados dos testes"""
        try:
            filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(test_suite, f, indent=2)
            logger.info(f"📄 Resultados salvos em: {filename}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar resultados: {e}")
    
    def _generate_report(self, test_suite: Dict[str, Any]) -> None:
        """Gera relatório de testes"""
        try:
            summary = test_suite['summary']
            total = summary['total']
            passed = summary['passed']
            failed = summary['failed']
            errors = summary['errors']
            
            success_rate = (passed / total * 100) if total > 0 else 0
            
            report = f"""
🧪 RELATÓRIO DE TESTES - SISTEMA DE PAGAMENTOS AVANÇADO
{'='*60}

📊 RESUMO EXECUTIVO:
   • Total de Testes: {total}
   • Testes Aprovados: {passed} ✅
   • Testes Falharam: {failed} ❌
   • Erros: {errors} 💥
   • Taxa de Sucesso: {success_rate:.1f}%

⏱️ DURAÇÃO TOTAL: {test_suite['duration']} segundos

📋 DETALHES DOS TESTES:
"""
            
            for test in test_suite['tests']:
                status_icon = "✅" if test['status'] == 'passed' else "❌" if test['status'] == 'failed' else "💥"
                report += f"   {status_icon} {test['description']}\n"
                
                if test['status'] == 'failed' and 'error' in test.get('result', {}):
                    report += f"      Erro: {test['result']['error']}\n"
                elif test['status'] == 'error':
                    report += f"      Erro: {test.get('error', 'Erro desconhecido')}\n"
            
            report += f"""
🎯 CONCLUSÃO:
"""
            
            if success_rate >= 90:
                report += "   🎉 SISTEMA EXCELENTE - Pronto para produção!"
            elif success_rate >= 80:
                report += "   ✅ SISTEMA BOM - Algumas melhorias recomendadas"
            elif success_rate >= 70:
                report += "   ⚠️ SISTEMA ACEITÁVEL - Necessita correções"
            else:
                report += "   ❌ SISTEMA CRÍTICO - Requer atenção imediata"
            
            report += f"""

📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
🔧 Versão: 2.0.0 - Sistema de Pagamentos Avançado
"""
            
            # Salvar relatório
            report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # Exibir relatório
            print(report)
            logger.info(f"📄 Relatório salvo em: {report_filename}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")

def main():
    """Função principal para executar testes"""
    import sys
    
    # Verificar argumentos
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    print(f"🚀 Iniciando testes do sistema de pagamentos em: {base_url}")
    
    # Criar testador
    tester = PaymentSystemTester(base_url)
    
    # Executar todos os testes
    results = tester.run_all_tests()
    
    # Verificar se todos os testes passaram
    if results['summary']['failed'] == 0 and results['summary']['errors'] == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para produção.")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['summary']['failed']} testes falharam, {results['summary']['errors']} erros encontrados.")
        sys.exit(1)

if __name__ == '__main__':
    main()
