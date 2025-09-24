#!/usr/bin/env python3
"""
🔍 TESTE COMPREHENSIVO - ENVIO DE COMPROVANTES
==============================================

Este script testa todos os aspectos do sistema de upload de comprovantes:
- Criação de pagamentos
- Upload de arquivos
- Limites de tamanho
- Formatos suportados
- Conectividade de rede
- Configurações do sistema
"""

import requests
import time
import os
from datetime import datetime

class UploadComprehensiveTester:
    def __init__(self, railway_url="https://web-production-1513a.up.railway.app"):
        self.railway_url = railway_url
        self.results = []
        self.test_files = []
        
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
    
    def create_test_files(self):
        """Cria arquivos de teste"""
        print("\n📁 CRIANDO ARQUIVOS DE TESTE")
        print("=" * 40)
        
        # Arquivo pequeno (1KB)
        with open("test_small.pdf", "w") as f:
            f.write("Teste de comprovante pequeno" * 50)
        self.test_files.append(("test_small.pdf", "Arquivo pequeno (1KB)"))
        
        # Arquivo médio (1MB)
        with open("test_medium.pdf", "wb") as f:
            f.write(b"0" * (1024 * 1024))
        self.test_files.append(("test_medium.pdf", "Arquivo médio (1MB)"))
        
        # Arquivo grande (15MB - dentro do limite)
        with open("test_large.pdf", "wb") as f:
            f.write(b"0" * (15 * 1024 * 1024))
        self.test_files.append(("test_large.pdf", "Arquivo grande (15MB)"))
        
        # Arquivo muito grande (20MB - fora do limite)
        with open("test_oversized.pdf", "wb") as f:
            f.write(b"0" * (20 * 1024 * 1024))
        self.test_files.append(("test_oversized.pdf", "Arquivo muito grande (20MB)"))
        
        # Arquivo com formato inválido
        with open("test_invalid.txt", "w") as f:
            f.write("Arquivo com formato inválido")
        self.test_files.append(("test_invalid.txt", "Arquivo formato inválido (.txt)"))
        
        self.log_test("Criação de arquivos de teste", "SUCESSO", f"{len(self.test_files)} arquivos criados")
    
    def test_railway_health(self):
        """Testa saúde do Railway"""
        print("\n🏥 TESTANDO SAÚDE DO RAILWAY")
        print("=" * 40)
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.railway_url}/api/health", timeout=10)
            end_time = time.time()
            
            latency = (end_time - start_time) * 1000  # em ms
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Railway Health Check", "SUCESSO", 
                             f"Status: {health_data.get('status')}, Latência: {latency:.0f}ms")
                return True
            else:
                self.log_test("Railway Health Check", "FALHOU", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Railway Health Check", "FALHOU", str(e))
            return False
    
    def test_payment_creation(self):
        """Testa criação de pagamentos"""
        print("\n💳 TESTANDO CRIAÇÃO DE PAGAMENTOS")
        print("=" * 40)
        
        payment_data = {
            "email": "teste.comprehensive@gmail.com",
            "name": "Cliente Teste Comprehensive",
            "country": "BR",
            "amount": 100,
            "currency": "BRL"
        }
        
        try:
            response = requests.post(
                f"{self.railway_url}/api/create-pix-payment",
                json=payment_data,
                timeout=15
            )
            
            if response.status_code == 200:
                payment_info = response.json()
                payment_id = payment_info.get('payment_id')
                
                if payment_id:
                    self.log_test("Criação de Pagamento PIX", "SUCESSO", 
                                 f"Payment ID: {payment_id}")
                    return payment_id
                else:
                    self.log_test("Criação de Pagamento PIX", "FALHOU", "Payment ID não encontrado")
                    return None
            else:
                self.log_test("Criação de Pagamento PIX", "FALHOU", 
                             f"Status: {response.status_code}, Resposta: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Criação de Pagamento PIX", "FALHOU", str(e))
            return None
    
    def test_file_upload(self, payment_id, filename, description):
        """Testa upload de arquivo específico"""
        try:
            if not os.path.exists(filename):
                self.log_test(f"Upload {description}", "FALHOU", "Arquivo não encontrado")
                return False
            
            file_size = os.path.getsize(filename)
            
            with open(filename, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf')}
                data = {
                    'payment_id': payment_id,
                    'email': 'teste.comprehensive@gmail.com'
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.railway_url}/api/upload-payment-proof",
                    files=files,
                    data=data,
                    timeout=60
                )
                end_time = time.time()
                
                upload_time = end_time - start_time
                upload_speed = (file_size / 1024 / 1024) / upload_time if upload_time > 0 else 0
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log_test(f"Upload {description}", "SUCESSO", 
                                     f"Tamanho: {file_size/1024/1024:.1f}MB, "
                                     f"Tempo: {upload_time:.1f}s, "
                                     f"Velocidade: {upload_speed:.1f}MB/s")
                        return True
                    else:
                        self.log_test(f"Upload {description}", "FALHOU", 
                                     f"Erro: {result.get('error', 'Erro desconhecido')}")
                        return False
                else:
                    self.log_test(f"Upload {description}", "FALHOU", 
                                 f"Status: {response.status_code}, Resposta: {response.text[:200]}")
                    return False
                    
        except Exception as e:
            self.log_test(f"Upload {description}", "FALHOU", str(e))
            return False
    
    def test_all_file_uploads(self, payment_id):
        """Testa upload de todos os arquivos"""
        print("\n📤 TESTANDO UPLOAD DE ARQUIVOS")
        print("=" * 40)
        
        for filename, description in self.test_files:
            self.test_file_upload(payment_id, filename, description)
            time.sleep(1)  # Pausa entre uploads
    
    def test_notification_system(self):
        """Testa sistema de notificações"""
        print("\n🔔 TESTANDO SISTEMA DE NOTIFICAÇÕES")
        print("=" * 40)
        
        try:
            response = requests.get(f"{self.railway_url}/api/notifications", timeout=10)
            
            if response.status_code == 200:
                notifications = response.json()
                count = notifications.get('count', 0)
                
                self.log_test("Sistema de Notificações", "SUCESSO", 
                             f"{count} notificações armazenadas")
                
                # Verificar se há notificações recentes
                recent_notifications = [n for n in notifications.get('notifications', []) 
                                      if 'teste.comprehensive' in n.get('email', '')]
                
                if recent_notifications:
                    self.log_test("Notificações de Teste", "SUCESSO", 
                                 f"{len(recent_notifications)} notificações de teste encontradas")
                else:
                    self.log_test("Notificações de Teste", "AVISO", 
                                 "Nenhuma notificação de teste encontrada")
                
                return True
            else:
                self.log_test("Sistema de Notificações", "FALHOU", 
                             f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Sistema de Notificações", "FALHOU", str(e))
            return False
    
    def test_network_performance(self):
        """Testa performance de rede"""
        print("\n🌐 TESTANDO PERFORMANCE DE REDE")
        print("=" * 40)
        
        # Teste de latência
        latencies = []
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(f"{self.railway_url}/api/health", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    latency = (end_time - start_time) * 1000
                    latencies.append(latency)
                
                time.sleep(0.5)
            except Exception as e:
                self.log_test(f"Teste de Latência {i+1}", "FALHOU", str(e))
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            self.log_test("Performance de Rede", "SUCESSO", 
                         f"Latência média: {avg_latency:.0f}ms, "
                         f"Min: {min_latency:.0f}ms, "
                         f"Max: {max_latency:.0f}ms")
        else:
            self.log_test("Performance de Rede", "FALHOU", "Nenhum teste de latência bem-sucedido")
    
    def cleanup_test_files(self):
        """Remove arquivos de teste"""
        print("\n🧹 LIMPEZA DE ARQUIVOS DE TESTE")
        print("=" * 40)
        
        cleaned = 0
        for filename, _ in self.test_files:
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                    cleaned += 1
            except Exception as e:
                print(f"⚠️ Erro ao remover {filename}: {e}")
        
        self.log_test("Limpeza de Arquivos", "SUCESSO", f"{cleaned} arquivos removidos")
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🔍 INICIANDO TESTE COMPREHENSIVO DE UPLOAD")
        print("=" * 60)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"🌐 URL Railway: {self.railway_url}")
        
        # Executar todos os testes
        self.create_test_files()
        
        if not self.test_railway_health():
            print("❌ Railway não está funcionando. Parando testes.")
            return
        
        payment_id = self.test_payment_creation()
        if not payment_id:
            print("❌ Não foi possível criar pagamento. Parando testes.")
            return
        
        self.test_all_file_uploads(payment_id)
        self.test_notification_system()
        self.test_network_performance()
        
        # Limpeza
        self.cleanup_test_files()
        
        # Gerar relatório final
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório final"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - TESTE COMPREHENSIVO DE UPLOAD")
        print("=" * 60)
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['status'] == 'SUCESSO'])
        failed_tests = len([r for r in self.results if r['status'] == 'FALHOU'])
        warning_tests = len([r for r in self.results if r['status'] == 'AVISO'])
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 RESUMO EXECUTIVO:")
        print(f"   • Total de Testes: {total_tests}")
        print(f"   • Testes Bem-sucedidos: {successful_tests} ✅")
        print(f"   • Testes Falharam: {failed_tests} ❌")
        print(f"   • Avisos: {warning_tests} ⚠️")
        print(f"   • Taxa de Sucesso: {success_rate:.1f}%")
        print(f"   • Plataforma: Railway (Produção)")
        
        print(f"\n📋 DETALHES DOS TESTES:")
        for result in self.results:
            status_icon = "✅" if result['status'] == "SUCESSO" else "❌" if result['status'] == "FALHOU" else "⚠️"
            print(f"   {status_icon} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"upload_comprehensive_test_report_{timestamp}.json"
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
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
        if success_rate >= 90:
            print(f"\n🎯 CONCLUSÃO: SISTEMA DE UPLOAD FUNCIONANDO EXCELENTEMENTE")
        elif success_rate >= 70:
            print(f"\n✅ CONCLUSÃO: SISTEMA DE UPLOAD FUNCIONANDO BEM")
        elif success_rate >= 50:
            print(f"\n⚠️ CONCLUSÃO: SISTEMA DE UPLOAD COM PROBLEMAS MENORES")
        else:
            print(f"\n❌ CONCLUSÃO: SISTEMA DE UPLOAD CRÍTICO - REQUER ATENÇÃO")

if __name__ == "__main__":
    import sys
    
    railway_url = sys.argv[1] if len(sys.argv) > 1 else "https://web-production-1513a.up.railway.app"
    
    tester = UploadComprehensiveTester(railway_url)
    tester.run_all_tests()
