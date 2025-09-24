#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO DO SISTEMA DE UPLOAD
=====================================

Este script testa todos os aspectos do sistema de upload:
- Diferentes tipos de arquivos
- Diferentes tamanhos de arquivos
- Cenários de erro
- Validação de upload
- Feedback ao usuário
"""

import requests
import os
import json
import time
from datetime import datetime

class UploadTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.test_files_dir = "test_files"
        self.results = []
        
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
    
    def test_file_upload(self, file_path, payment_id="test_upload", expected_status=200):
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
    
    def test_upload_validation(self):
        """Testa validação de upload"""
        print("\n🔍 TESTANDO VALIDAÇÃO DE UPLOAD")
        print("=" * 50)
        
        # Teste 1: Upload sem arquivo
        try:
            response = requests.post(
                f"{self.base_url}/api/upload-payment-proof",
                data={'payment_id': 'test_no_file'},
                timeout=10
            )
            success = response.status_code == 400
            self.log_test("Upload sem arquivo", "PASSOU" if success else "FALHOU", 
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Upload sem arquivo", "FALHOU", str(e))
        
        # Teste 2: Upload com payment_id inválido
        try:
            with open(f"{self.test_files_dir}/comprovante_pequeno.txt", 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {'payment_id': 'payment_inexistente'}
                
                response = requests.post(
                    f"{self.base_url}/api/upload-payment-proof",
                    files=files,
                    data=data,
                    timeout=10
                )
            success = response.status_code == 404
            self.log_test("Upload com payment_id inválido", "PASSOU" if success else "FALHOU",
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Upload com payment_id inválido", "FALHOU", str(e))
    
    def test_different_file_types(self):
        """Testa diferentes tipos de arquivos"""
        print("\n📁 TESTANDO DIFERENTES TIPOS DE ARQUIVOS")
        print("=" * 50)
        
        file_types = [
            ("comprovante_pequeno.txt", "Arquivo de texto pequeno"),
            ("comprovante.pdf", "Arquivo PDF"),
            ("comprovante.jpg", "Arquivo de imagem JPG"),
            ("comprovante_medio.txt", "Arquivo de texto médio"),
            ("comprovante_grande.bin", "Arquivo binário grande")
        ]
        
        for filename, description in file_types:
            file_path = f"{self.test_files_dir}/{filename}"
            success, details = self.test_file_upload(file_path, f"test_{filename}")
            status = "PASSOU" if success else "FALHOU"
            self.log_test(f"Upload {description}", status, details)
    
    def test_file_size_limits(self):
        """Testa limites de tamanho de arquivo"""
        print("\n📏 TESTANDO LIMITES DE TAMANHO")
        print("=" * 50)
        
        # Criar arquivo muito grande (10MB)
        large_file = f"{self.test_files_dir}/comprovante_muito_grande.bin"
        try:
            with open(large_file, 'wb') as f:
                f.write(b'0' * (10 * 1024 * 1024))  # 10MB
            
            success, details = self.test_file_upload(large_file, "test_large_file")
            status = "PASSOU" if success else "FALHOU"
            self.log_test("Upload arquivo muito grande (10MB)", status, details)
            
            # Limpar arquivo
            os.remove(large_file)
            
        except Exception as e:
            self.log_test("Upload arquivo muito grande (10MB)", "FALHOU", str(e))
    
    def test_concurrent_uploads(self):
        """Testa uploads simultâneos"""
        print("\n🔄 TESTANDO UPLOADS SIMULTÂNEOS")
        print("=" * 50)
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def upload_worker(worker_id):
            try:
                success, details = self.test_file_upload(
                    f"{self.test_files_dir}/comprovante_pequeno.txt",
                    f"test_concurrent_{worker_id}"
                )
                results_queue.put((worker_id, success, details))
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
        self.log_test("Uploads simultâneos", status, f"{concurrent_success}/3 sucessos")
    
    def test_upload_with_payment_flow(self):
        """Testa upload integrado com fluxo de pagamento"""
        print("\n💳 TESTANDO UPLOAD COM FLUXO DE PAGAMENTO")
        print("=" * 50)
        
        try:
            # 1. Criar pagamento PIX
            pix_data = {
                "email": "teste_upload@exemplo.com",
                "name": "Cliente Teste Upload",
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
                    # 2. Fazer upload do comprovante
                    success, details = self.test_file_upload(
                        f"{self.test_files_dir}/comprovante_pequeno.txt",
                        payment_id
                    )
                    
                    status = "PASSOU" if success else "FALHOU"
                    self.log_test("Upload com fluxo de pagamento PIX", status, details)
                else:
                    self.log_test("Upload com fluxo de pagamento PIX", "FALHOU", "Payment ID não encontrado")
            else:
                self.log_test("Upload com fluxo de pagamento PIX", "FALHOU", f"Erro ao criar pagamento: {response.status_code}")
                
        except Exception as e:
            self.log_test("Upload com fluxo de pagamento PIX", "FALHOU", str(e))
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        print("\n⚠️ TESTANDO TRATAMENTO DE ERROS")
        print("=" * 50)
        
        # Teste 1: Arquivo corrompido
        try:
            corrupted_file = f"{self.test_files_dir}/arquivo_corrompido.txt"
            with open(corrupted_file, 'wb') as f:
                f.write(b'\x00\x01\x02\x03\xFF\xFE\xFD')  # Dados binários corrompidos
            
            success, details = self.test_file_upload(corrupted_file, "test_corrupted")
            status = "PASSOU" if success else "FALHOU"
            self.log_test("Upload arquivo corrompido", status, details)
            
            os.remove(corrupted_file)
            
        except Exception as e:
            self.log_test("Upload arquivo corrompido", "FALHOU", str(e))
        
        # Teste 2: Nome de arquivo com caracteres especiais
        try:
            special_file = f"{self.test_files_dir}/comprovante_especial_@#$%.txt"
            with open(special_file, 'w') as f:
                f.write("Comprovante com nome especial")
            
            success, details = self.test_file_upload(special_file, "test_special_name")
            status = "PASSOU" if success else "FALHOU"
            self.log_test("Upload com nome especial", status, details)
            
            os.remove(special_file)
            
        except Exception as e:
            self.log_test("Upload com nome especial", "FALHOU", str(e))
    
    def test_upload_performance(self):
        """Testa performance do upload"""
        print("\n⚡ TESTANDO PERFORMANCE DO UPLOAD")
        print("=" * 50)
        
        file_path = f"{self.test_files_dir}/comprovante_medio.txt"
        
        try:
            start_time = time.time()
            success, details = self.test_file_upload(file_path, "test_performance")
            end_time = time.time()
            
            duration = end_time - start_time
            file_size = os.path.getsize(file_path)
            speed = file_size / duration / 1024  # KB/s
            
            status = "PASSOU" if success and duration < 5 else "FALHOU"
            self.log_test("Performance do upload", status, 
                         f"Tempo: {duration:.2f}s, Velocidade: {speed:.2f} KB/s")
            
        except Exception as e:
            self.log_test("Performance do upload", "FALHOU", str(e))
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🧪 INICIANDO TESTES COMPLETOS DO SISTEMA DE UPLOAD")
        print("=" * 60)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"🌐 URL Base: {self.base_url}")
        print(f"📁 Diretório de Testes: {self.test_files_dir}")
        
        # Verificar se diretório de testes existe
        if not os.path.exists(self.test_files_dir):
            print(f"❌ Diretório de testes não encontrado: {self.test_files_dir}")
            return
        
        # Executar todos os testes
        self.test_upload_validation()
        self.test_different_file_types()
        self.test_file_size_limits()
        self.test_concurrent_uploads()
        self.test_upload_with_payment_flow()
        self.test_error_handling()
        self.test_upload_performance()
        
        # Gerar relatório final
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - TESTES DE UPLOAD")
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
        
        print(f"\n📋 DETALHES DOS TESTES:")
        for result in self.results:
            status_icon = "✅" if result['status'] == "PASSOU" else "❌" if result['status'] == "FALHOU" else "⚠️"
            print(f"   {status_icon} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Salvar resultados em arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"upload_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'warning_tests': warning_tests,
                    'success_rate': success_rate
                },
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_file}")
        
        # Conclusão
        if success_rate >= 80:
            print(f"\n🎯 CONCLUSÃO: SISTEMA DE UPLOAD FUNCIONANDO BEM")
        elif success_rate >= 60:
            print(f"\n⚠️ CONCLUSÃO: SISTEMA DE UPLOAD COM PROBLEMAS MENORES")
        else:
            print(f"\n❌ CONCLUSÃO: SISTEMA DE UPLOAD CRÍTICO - REQUER ATENÇÃO")

if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    tester = UploadTester(base_url)
    tester.run_all_tests()