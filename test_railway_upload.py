#!/usr/bin/env python3
"""
🧪 TESTE DO SISTEMA DE UPLOAD NO RAILWAY
========================================

Este script testa o sistema de upload na plataforma Railway de produção.
"""

import requests
import os
import json
import time
from datetime import datetime

class RailwayUploadTester:
    def __init__(self, railway_url="https://web-production-1513a.up.railway.app"):
        self.railway_url = railway_url
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
    
    def test_upload_endpoint_availability(self):
        """Testa se o endpoint de upload está disponível"""
        print("\n📤 TESTANDO DISPONIBILIDADE DO ENDPOINT DE UPLOAD")
        print("=" * 60)
        
        try:
            # Teste sem arquivo para verificar se o endpoint existe
            response = requests.post(
                f"{self.railway_url}/api/upload-payment-proof",
                data={'payment_id': 'test_endpoint'},
                timeout=10
            )
            
            # Esperamos um erro 400 (arquivo não enviado), não 404 (endpoint não encontrado)
            if response.status_code == 400:
                self.log_test("Endpoint de Upload Disponível", "PASSOU", "Endpoint responde corretamente")
                return True
            elif response.status_code == 404:
                self.log_test("Endpoint de Upload Disponível", "FALHOU", "Endpoint não encontrado")
                return False
            else:
                self.log_test("Endpoint de Upload Disponível", "FALHOU", f"Status inesperado: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Endpoint de Upload Disponível", "FALHOU", str(e))
            return False
    
    def test_upload_validation_railway(self):
        """Testa validação de upload no Railway"""
        print("\n🔍 TESTANDO VALIDAÇÃO DE UPLOAD NO RAILWAY")
        print("=" * 50)
        
        # Teste 1: Upload sem arquivo
        try:
            response = requests.post(
                f"{self.railway_url}/api/upload-payment-proof",
                data={'payment_id': 'test_no_file'},
                timeout=10
            )
            success = response.status_code == 400
            self.log_test("Upload sem arquivo (Railway)", "PASSOU" if success else "FALHOU", 
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Upload sem arquivo (Railway)", "FALHOU", str(e))
        
        # Teste 2: Upload com payment_id inválido
        try:
            with open(f"{self.test_files_dir}/comprovante_pequeno.txt", 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {'payment_id': 'payment_inexistente_railway'}
                
                response = requests.post(
                    f"{self.railway_url}/api/upload-payment-proof",
                    files=files,
                    data=data,
                    timeout=10
                )
            success = response.status_code == 404
            self.log_test("Upload com payment_id inválido (Railway)", "PASSOU" if success else "FALHOU",
                         f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Upload com payment_id inválido (Railway)", "FALHOU", str(e))
    
    def test_file_types_railway(self):
        """Testa diferentes tipos de arquivos no Railway"""
        print("\n📁 TESTANDO TIPOS DE ARQUIVOS NO RAILWAY")
        print("=" * 50)
        
        file_types = [
            ("comprovante_pequeno.txt", "Arquivo de texto pequeno"),
            ("comprovante.pdf", "Arquivo PDF"),
            ("comprovante.jpg", "Arquivo de imagem JPG")
        ]
        
        for filename, description in file_types:
            try:
                with open(f"{self.test_files_dir}/{filename}", 'rb') as f:
                    files = {'file': (filename, f, 'application/octet-stream')}
                    data = {'payment_id': 'test_railway_file_type'}
                    
                    response = requests.post(
                        f"{self.railway_url}/api/upload-payment-proof",
                        files=files,
                        data=data,
                        timeout=15
                    )
                
                # Esperamos erro 404 (payment não encontrado) ou 400 (tipo inválido)
                success = response.status_code in [400, 404]
                status = "PASSOU" if success else "FALHOU"
                self.log_test(f"Upload {description} (Railway)", status, 
                             f"Status: {response.status_code}")
                
            except Exception as e:
                self.log_test(f"Upload {description} (Railway)", "FALHOU", str(e))
    
    def test_upload_performance_railway(self):
        """Testa performance do upload no Railway"""
        print("\n⚡ TESTANDO PERFORMANCE DO UPLOAD NO RAILWAY")
        print("=" * 50)
        
        try:
            start_time = time.time()
            
            with open(f"{self.test_files_dir}/comprovante_pequeno.txt", 'rb') as f:
                files = {'file': ('test_performance.txt', f, 'text/plain')}
                data = {'payment_id': 'test_railway_performance'}
                
                response = requests.post(
                    f"{self.railway_url}/api/upload-payment-proof",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Esperamos erro 404 (payment não encontrado)
            success = response.status_code == 404
            status = "PASSOU" if success else "FALHOU"
            
            self.log_test("Performance do upload (Railway)", status, 
                         f"Tempo: {duration:.2f}s, Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Performance do upload (Railway)", "FALHOU", str(e))
    
    def test_railway_error_handling(self):
        """Testa tratamento de erros no Railway"""
        print("\n⚠️ TESTANDO TRATAMENTO DE ERROS NO RAILWAY")
        print("=" * 50)
        
        # Teste 1: Arquivo muito grande
        try:
            # Criar arquivo grande (1MB)
            large_content = b'0' * (1024 * 1024)  # 1MB
            files = {'file': ('large_file.txt', large_content, 'text/plain')}
            data = {'payment_id': 'test_railway_large'}
            
            response = requests.post(
                f"{self.railway_url}/api/upload-payment-proof",
                files=files,
                data=data,
                timeout=60
            )
            
            success = response.status_code in [400, 404, 413]  # 413 = Payload Too Large
            status = "PASSOU" if success else "FALHOU"
            self.log_test("Upload arquivo grande (Railway)", status, 
                         f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Upload arquivo grande (Railway)", "FALHOU", str(e))
        
        # Teste 2: Tipo de arquivo inválido
        try:
            files = {'file': ('test.exe', b'executable content', 'application/octet-stream')}
            data = {'payment_id': 'test_railway_invalid_type'}
            
            response = requests.post(
                f"{self.railway_url}/api/upload-payment-proof",
                files=files,
                data=data,
                timeout=15
            )
            
            success = response.status_code in [400, 404]
            status = "PASSOU" if success else "FALHOU"
            self.log_test("Upload tipo inválido (Railway)", status, 
                         f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Upload tipo inválido (Railway)", "FALHOU", str(e))
    
    def run_all_tests(self):
        """Executa todos os testes no Railway"""
        print("🧪 INICIANDO TESTES DO SISTEMA DE UPLOAD NO RAILWAY")
        print("=" * 60)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"🌐 URL Railway: {self.railway_url}")
        print(f"📁 Diretório de Testes: {self.test_files_dir}")
        
        # Verificar se diretório de testes existe
        if not os.path.exists(self.test_files_dir):
            print(f"❌ Diretório de testes não encontrado: {self.test_files_dir}")
            return
        
        # Executar todos os testes
        if not self.test_railway_health():
            print("❌ Railway não está funcionando. Parando testes.")
            return
        
        self.test_upload_endpoint_availability()
        self.test_upload_validation_railway()
        self.test_file_types_railway()
        self.test_upload_performance_railway()
        self.test_railway_error_handling()
        
        # Gerar relatório final
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - TESTES DE UPLOAD NO RAILWAY")
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
        print(f"   • Plataforma: Railway (Produção)")
        
        print(f"\n📋 DETALHES DOS TESTES:")
        for result in self.results:
            status_icon = "✅" if result['status'] == "PASSOU" else "❌" if result['status'] == "FALHOU" else "⚠️"
            print(f"   {status_icon} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Salvar resultados em arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"railway_upload_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'warning_tests': warning_tests,
                    'success_rate': success_rate,
                    'platform': 'Railway Production'
                },
                'railway_url': self.railway_url,
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_file}")
        
        # Conclusão
        if success_rate >= 80:
            print(f"\n🎯 CONCLUSÃO: SISTEMA DE UPLOAD NO RAILWAY FUNCIONANDO EXCELENTEMENTE")
        elif success_rate >= 60:
            print(f"\n✅ CONCLUSÃO: SISTEMA DE UPLOAD NO RAILWAY FUNCIONANDO BEM")
        elif success_rate >= 40:
            print(f"\n⚠️ CONCLUSÃO: SISTEMA DE UPLOAD NO RAILWAY COM PROBLEMAS MENORES")
        else:
            print(f"\n❌ CONCLUSÃO: SISTEMA DE UPLOAD NO RAILWAY CRÍTICO - REQUER ATENÇÃO")

if __name__ == "__main__":
    import sys
    
    railway_url = sys.argv[1] if len(sys.argv) > 1 else "https://web-production-1513a.up.railway.app"
    
    tester = RailwayUploadTester(railway_url)
    tester.run_all_tests()
