#!/usr/bin/env python3
"""
🧪 TESTE REALISTA DO SISTEMA DE UPLOAD
=====================================

Este script testa o sistema de upload com pagamentos reais criados:
- Cria pagamentos PIX válidos
- Testa upload de comprovantes
- Verifica diferentes tipos de arquivos
- Testa cenários de erro
"""

import requests
import os
import json
import time
from datetime import datetime

class RealisticUploadTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.test_files_dir = "test_files"
        self.results = []
        self.created_payments = []
        
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
    
    def create_pix_payment(self, email, name="Cliente Teste"):
        """Cria um pagamento PIX válido"""
        try:
            pix_data = {
                "email": email,
                "name": name,
                "country": "BR",
                "method": "pix"
            }
            
            response = requests.post(
                f"{self.base_url}/api/enhanced/test-payment",
                json=pix_data,
                timeout=10
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                payment_id = payment_data.get('test_payment', {}).get('id')
                if payment_id:
                    self.created_payments.append(payment_id)
                    return payment_id
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao criar pagamento PIX: {e}")
            return None
    
    def test_file_upload(self, file_path, payment_id, expected_status=200):
        """Testa upload de arquivo específico"""
        try:
            if not os.path.exists(file_path):
                return False, f"Arquivo não encontrado: {file_path}"
            
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f, 'application/octet-stream')}
                data = {'payment_id': payment_id}
                
                response = requests.post(
                    f"{self.base_url}/api/upload-payment-proof",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            return response.status_code == expected_status, f"Status: {response.status_code}, Resposta: {response.text[:200]}"
            
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def test_different_file_types_with_real_payments(self):
        """Testa diferentes tipos de arquivos com pagamentos reais"""
        print("\n📁 TESTANDO DIFERENTES TIPOS DE ARQUIVOS COM PAGAMENTOS REAIS")
        print("=" * 70)
        
        file_types = [
            ("comprovante_pequeno.txt", "Arquivo de texto pequeno"),
            ("comprovante.pdf", "Arquivo PDF"),
            ("comprovante.jpg", "Arquivo de imagem JPG"),
            ("comprovante_medio.txt", "Arquivo de texto médio"),
            ("comprovante_grande.bin", "Arquivo binário grande")
        ]
        
        for filename, description in file_types:
            # Criar pagamento PIX para cada teste
            email = f"teste_{filename.replace('.', '_')}@exemplo.com"
            payment_id = self.create_pix_payment(email, f"Cliente {description}")
            
            if payment_id:
                file_path = f"{self.test_files_dir}/{filename}"
                success, details = self.test_file_upload(file_path, payment_id)
                status = "PASSOU" if success else "FALHOU"
                self.log_test(f"Upload {description}", status, details)
            else:
                self.log_test(f"Upload {description}", "FALHOU", "Não foi possível criar pagamento PIX")
    
    def test_file_size_limits_with_real_payment(self):
        """Testa limites de tamanho com pagamento real"""
        print("\n📏 TESTANDO LIMITES DE TAMANHO COM PAGAMENTO REAL")
        print("=" * 50)
        
        # Criar pagamento PIX
        email = "teste_tamanho@exemplo.com"
        payment_id = self.create_pix_payment(email, "Cliente Teste Tamanho")
        
        if not payment_id:
            self.log_test("Upload arquivo grande", "FALHOU", "Não foi possível criar pagamento PIX")
            return
        
        # Criar arquivo grande (5MB)
        large_file = f"{self.test_files_dir}/comprovante_grande_real.bin"
        try:
            with open(large_file, 'wb') as f:
                f.write(b'0' * (5 * 1024 * 1024))  # 5MB
            
            success, details = self.test_file_upload(large_file, payment_id)
            status = "PASSOU" if success else "FALHOU"
            self.log_test("Upload arquivo grande (5MB)", status, details)
            
            # Limpar arquivo
            os.remove(large_file)
            
        except Exception as e:
            self.log_test("Upload arquivo grande (5MB)", "FALHOU", str(e))
    
    def test_concurrent_uploads_with_real_payments(self):
        """Testa uploads simultâneos com pagamentos reais"""
        print("\n🔄 TESTANDO UPLOADS SIMULTÂNEOS COM PAGAMENTOS REAIS")
        print("=" * 60)
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def upload_worker(worker_id):
            try:
                # Criar pagamento PIX para cada worker
                email = f"teste_concurrent_{worker_id}@exemplo.com"
                payment_id = self.create_pix_payment(email, f"Cliente Concurrent {worker_id}")
                
                if payment_id:
                    success, details = self.test_file_upload(
                        f"{self.test_files_dir}/comprovante_pequeno.txt",
                        payment_id
                    )
                    results_queue.put((worker_id, success, details))
                else:
                    results_queue.put((worker_id, False, "Não foi possível criar pagamento PIX"))
                    
            except Exception as e:
                results_queue.put((worker_id, False, str(e)))
        
        # Iniciar 3 uploads simultâneos
        threads = []
        for i in range(3):
            thread = threading.Thread(target=upload_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        # Verificar resultados
        concurrent_success = 0
        while not results_queue.empty():
            worker_id, success, details = results_queue.get()
            if success:
                concurrent_success += 1
        
        status = "PASSOU" if concurrent_success >= 2 else "FALHOU"
        self.log_test("Uploads simultâneos com pagamentos reais", status, f"{concurrent_success}/3 sucessos")
    
    def test_error_scenarios_with_real_payments(self):
        """Testa cenários de erro com pagamentos reais"""
        print("\n⚠️ TESTANDO CENÁRIOS DE ERRO COM PAGAMENTOS REAIS")
        print("=" * 60)
        
        # Teste 1: Upload sem arquivo
        email = "teste_sem_arquivo@exemplo.com"
        payment_id = self.create_pix_payment(email, "Cliente Sem Arquivo")
        
        if payment_id:
            try:
                response = requests.post(
                    f"{self.base_url}/api/upload-payment-proof",
                    data={'payment_id': payment_id},
                    timeout=10
                )
                success = response.status_code == 400
                self.log_test("Upload sem arquivo (pagamento real)", "PASSOU" if success else "FALHOU", 
                             f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Upload sem arquivo (pagamento real)", "FALHOU", str(e))
        
        # Teste 2: Arquivo com extensão inválida
        email = "teste_extensao_invalida@exemplo.com"
        payment_id = self.create_pix_payment(email, "Cliente Extensão Inválida")
        
        if payment_id:
            try:
                # Criar arquivo com extensão inválida
                invalid_file = f"{self.test_files_dir}/comprovante.exe"
                with open(invalid_file, 'w') as f:
                    f.write("Arquivo executável inválido")
                
                success, details = self.test_file_upload(invalid_file, payment_id, 400)
                status = "PASSOU" if success else "FALHOU"
                self.log_test("Upload com extensão inválida", status, details)
                
                os.remove(invalid_file)
                
            except Exception as e:
                self.log_test("Upload com extensão inválida", "FALHOU", str(e))
    
    def test_upload_performance_with_real_payment(self):
        """Testa performance com pagamento real"""
        print("\n⚡ TESTANDO PERFORMANCE COM PAGAMENTO REAL")
        print("=" * 50)
        
        # Criar pagamento PIX
        email = "teste_performance@exemplo.com"
        payment_id = self.create_pix_payment(email, "Cliente Performance")
        
        if not payment_id:
            self.log_test("Performance do upload", "FALHOU", "Não foi possível criar pagamento PIX")
            return
        
        file_path = f"{self.test_files_dir}/comprovante_medio.txt"
        
        try:
            start_time = time.time()
            success, details = self.test_file_upload(file_path, payment_id)
            end_time = time.time()
            
            duration = end_time - start_time
            file_size = os.path.getsize(file_path)
            speed = file_size / duration / 1024  # KB/s
            
            status = "PASSOU" if success and duration < 5 else "FALHOU"
            self.log_test("Performance do upload (pagamento real)", status, 
                         f"Tempo: {duration:.2f}s, Velocidade: {speed:.2f} KB/s")
            
        except Exception as e:
            self.log_test("Performance do upload (pagamento real)", "FALHOU", str(e))
    
    def test_upload_validation_with_real_payments(self):
        """Testa validação com pagamentos reais"""
        print("\n🔍 TESTANDO VALIDAÇÃO COM PAGAMENTOS REAIS")
        print("=" * 50)
        
        # Teste 1: Payment ID inválido
        try:
            with open(f"{self.test_files_dir}/comprovante_pequeno.txt", 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {'payment_id': 'payment_inexistente_12345'}
                
                response = requests.post(
                    f"{self.base_url}/api/upload-payment-proof",
                    files=files,
                    data=data,
                    timeout=10
                )
            success = response.status_code == 404
            self.log_test("Upload com payment_id inválido (validação)", "PASSOU" if success else "FALHOU",
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Upload com payment_id inválido (validação)", "FALHOU", str(e))
        
        # Teste 2: Upload para pagamento não-PIX
        try:
            # Criar pagamento Stripe (não-PIX)
            stripe_data = {
                "email": "teste_stripe@exemplo.com",
                "name": "Cliente Stripe",
                "country": "US",
                "method": "stripe"
            }
            
            response = requests.post(
                f"{self.base_url}/api/enhanced/test-payment",
                json=stripe_data,
                timeout=10
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                payment_id = payment_data.get('test_payment', {}).get('id')
                
                if payment_id:
                    success, details = self.test_file_upload(
                        f"{self.test_files_dir}/comprovante_pequeno.txt",
                        payment_id,
                        400  # Esperado erro 400 para pagamento não-PIX
                    )
                    status = "PASSOU" if success else "FALHOU"
                    self.log_test("Upload para pagamento não-PIX", status, details)
                else:
                    self.log_test("Upload para pagamento não-PIX", "FALHOU", "Payment ID não encontrado")
            else:
                self.log_test("Upload para pagamento não-PIX", "FALHOU", f"Erro ao criar pagamento: {response.status_code}")
                
        except Exception as e:
            self.log_test("Upload para pagamento não-PIX", "FALHOU", str(e))
    
    def run_all_tests(self):
        """Executa todos os testes realistas"""
        print("🧪 INICIANDO TESTES REALISTAS DO SISTEMA DE UPLOAD")
        print("=" * 60)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"🌐 URL Base: {self.base_url}")
        print(f"📁 Diretório de Testes: {self.test_files_dir}")
        
        # Verificar se diretório de testes existe
        if not os.path.exists(self.test_files_dir):
            print(f"❌ Diretório de testes não encontrado: {self.test_files_dir}")
            return
        
        # Executar todos os testes
        self.test_upload_validation_with_real_payments()
        self.test_different_file_types_with_real_payments()
        self.test_file_size_limits_with_real_payment()
        self.test_concurrent_uploads_with_real_payments()
        self.test_error_scenarios_with_real_payments()
        self.test_upload_performance_with_real_payment()
        
        # Gerar relatório final
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - TESTES REALISTAS DE UPLOAD")
        print("=" * 60)
        
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
        print(f"   • Pagamentos Criados: {len(self.created_payments)}")
        
        print(f"\n📋 DETALHES DOS TESTES:")
        for result in self.results:
            status_icon = "✅" if result['status'] == "PASSOU" else "❌" if result['status'] == "FALHOU" else "⚠️"
            print(f"   {status_icon} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Salvar resultados em arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"realistic_upload_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'warning_tests': warning_tests,
                    'success_rate': success_rate,
                    'created_payments': len(self.created_payments)
                },
                'created_payments': self.created_payments,
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_file}")
        
        # Conclusão
        if success_rate >= 80:
            print(f"\n🎯 CONCLUSÃO: SISTEMA DE UPLOAD FUNCIONANDO EXCELENTEMENTE")
        elif success_rate >= 60:
            print(f"\n✅ CONCLUSÃO: SISTEMA DE UPLOAD FUNCIONANDO BEM")
        elif success_rate >= 40:
            print(f"\n⚠️ CONCLUSÃO: SISTEMA DE UPLOAD COM PROBLEMAS MENORES")
        else:
            print(f"\n❌ CONCLUSÃO: SISTEMA DE UPLOAD CRÍTICO - REQUER ATENÇÃO")

if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    tester = RealisticUploadTester(base_url)
    tester.run_all_tests()
