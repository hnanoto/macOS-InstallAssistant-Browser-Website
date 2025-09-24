#!/usr/bin/env python3
"""
Script para verificar se a correção do Railway foi aplicada corretamente
Testa todos os componentes críticos do sistema com endpoints reais
"""

import requests
import json
import time
from datetime import datetime

def test_health_check():
    """Testa o health check da aplicação"""
    print("🏥 Testando Health Check...")
    try:
        response = requests.get("https://web-production-1513a.up.railway.app/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health Check: OK")
            return True
        else:
            print(f"❌ Health Check: Falhou ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Health Check: Erro - {e}")
        return False

def test_smtp_config():
    """Testa a configuração SMTP"""
    print("📧 Testando configuração SMTP...")
    try:
        response = requests.get("https://web-production-1513a.up.railway.app/api/debug/smtp", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Verificar se todas as configurações estão presentes
            required_fields = ['smtp_server', 'smtp_port', 'smtp_username', 'from_email']
            missing_fields = []
            
            for field in required_fields:
                if field not in data or not data[field]:
                    missing_fields.append(field)
            
            if not missing_fields:
                print("✅ Configuração SMTP: Completa")
                print(f"   📍 Servidor: {data.get('smtp_server')}")
                print(f"   📍 Porta: {data.get('smtp_port')}")
                print(f"   📍 Usuário: {data.get('smtp_username')}")
                print(f"   📍 Email From: {data.get('from_email')}")
                return True
            else:
                print(f"❌ Configuração SMTP: Campos faltando - {missing_fields}")
                return False
        else:
            print(f"❌ Configuração SMTP: Erro HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Configuração SMTP: Erro - {e}")
        return False

def test_email_sending():
    """Testa o envio de email usando endpoint real"""
    print("📮 Testando envio de email...")
    try:
        test_data = {
            "to": "hackintoshandbeyond@gmail.com",
            "subject": "Teste Railway - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Este é um teste automático do sistema de emails no Railway."
        }
        
        response = requests.post(
            "https://web-production-1513a.up.railway.app/api/debug/test-email",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Envio de Email: Sucesso")
                print(f"   📍 Método: {result.get('method', 'N/A')}")
                return True
            else:
                print(f"❌ Envio de Email: Falhou - {result.get('error', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Envio de Email: Erro HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Envio de Email: Erro - {e}")
        return False

def test_sendgrid_api():
    """Testa a API do SendGrid"""
    print("📧 Testando SendGrid API...")
    try:
        response = requests.get("https://web-production-1513a.up.railway.app/api/debug/sendgrid-test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ SendGrid API: Funcionando")
                return True
            else:
                print(f"❌ SendGrid API: {data.get('error', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ SendGrid API: Erro HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SendGrid API: Erro - {e}")
        return False

def test_resend_api():
    """Testa a API do Resend"""
    print("🔄 Testando Resend API...")
    try:
        response = requests.get("https://web-production-1513a.up.railway.app/api/debug/resend-test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Resend API: Funcionando")
                return True
            else:
                print(f"❌ Resend API: {data.get('error', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Resend API: Erro HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Resend API: Erro - {e}")
        return False

def test_file_upload():
    """Testa o upload de comprovante de pagamento"""
    print("📁 Testando upload de comprovante...")
    try:
        # Criar um arquivo de teste simples
        test_content = f"Teste de upload - {datetime.now().isoformat()}"
        files = {'proof': ('test_proof.txt', test_content, 'text/plain')}
        data = {'payment_id': 'test_payment_123'}
        
        response = requests.post(
            "https://web-production-1513a.up.railway.app/api/upload-payment-proof",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Upload de Comprovante: Sucesso")
                print(f"   📍 Arquivo: {result.get('filename', 'N/A')}")
                return True
            else:
                print(f"❌ Upload de Comprovante: {result.get('error', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Upload de Comprovante: Erro HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Upload de Comprovante: Erro - {e}")
        return False

def test_admin_panel():
    """Testa o acesso ao painel admin"""
    print("👤 Testando painel admin...")
    try:
        response = requests.get("https://web-production-1513a.up.railway.app/admin", timeout=10)
        if response.status_code == 200:
            print("✅ Painel Admin: Acessível")
            return True
        else:
            print(f"❌ Painel Admin: Erro HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Painel Admin: Erro - {e}")
        return False

def test_payment_endpoints():
    """Testa os endpoints de pagamento"""
    print("💳 Testando endpoints de pagamento...")
    try:
        response = requests.get("https://web-production-1513a.up.railway.app/api/admin/pending-payments", timeout=10)
        if response.status_code == 200:
            print("✅ Endpoints de Pagamento: Funcionando")
            data = response.json()
            print(f"   📍 Pagamentos pendentes: {len(data.get('payments', []))}")
            return True
        else:
            print(f"❌ Endpoints de Pagamento: Erro HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Endpoints de Pagamento: Erro - {e}")
        return False

def test_notifications():
    """Testa o sistema de notificações"""
    print("🔔 Testando sistema de notificações...")
    try:
        response = requests.get("https://web-production-1513a.up.railway.app/api/notifications", timeout=10)
        if response.status_code == 200:
            print("✅ Sistema de Notificações: Funcionando")
            data = response.json()
            print(f"   📍 Notificações: {len(data.get('notifications', []))}")
            return True
        else:
            print(f"❌ Sistema de Notificações: Erro HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Sistema de Notificações: Erro - {e}")
        return False

def generate_report(results):
    """Gera relatório final"""
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DA VERIFICAÇÃO")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"📈 Total de Testes: {total_tests}")
    print(f"✅ Testes Passaram: {passed_tests}")
    print(f"❌ Testes Falharam: {failed_tests}")
    print(f"📊 Taxa de Sucesso: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 DETALHES:")
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
    
    if failed_tests == 0:
        print("\n🎉 PARABÉNS! Todos os testes passaram!")
        print("   O Railway está funcionando perfeitamente!")
        print("   ✅ Sistema de emails configurado")
        print("   ✅ Upload de arquivos funcionando")
        print("   ✅ Painel admin acessível")
        print("   ✅ APIs de pagamento operacionais")
    elif failed_tests <= 2:
        print("\n⚠️  QUASE LÁ! Alguns testes falharam.")
        print("   O sistema está funcionando parcialmente.")
        print("   Verifique as configurações dos itens que falharam.")
    else:
        print("\n🚨 ATENÇÃO! Muitos testes falharam.")
        print("   Revise as instruções em RAILWAY_FIX_INSTRUCTIONS.md")
    
    print("\n📝 PRÓXIMOS PASSOS:")
    if failed_tests == 0:
        print("1. ✅ Sistema funcionando corretamente!")
        print("2. 📊 Monitore os logs para garantir estabilidade")
        print("3. 🧪 Teste com usuários reais")
        print("4. 🔄 Configure monitoramento contínuo")
    elif failed_tests <= 2:
        print("1. 🔍 Foque nos testes que falharam")
        print("2. ⚙️  Verifique configurações específicas")
        print("3. 🔄 Execute este teste novamente")
    else:
        print("1. 📋 Verifique as variáveis de ambiente no Railway")
        print("2. 🔄 Confirme se o redeploy foi feito")
        print("3. 📊 Verifique os logs do Railway")
        print("4. 🧪 Execute este teste novamente")

def main():
    """Função principal"""
    print("🔍 VERIFICAÇÃO COMPLETA DO RAILWAY")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 URL: https://web-production-1513a.up.railway.app")
    print()
    
    # Executar todos os testes
    results = {}
    
    results["Health Check"] = test_health_check()
    time.sleep(1)
    
    results["Configuração SMTP"] = test_smtp_config()
    time.sleep(1)
    
    results["SendGrid API"] = test_sendgrid_api()
    time.sleep(1)
    
    results["Resend API"] = test_resend_api()
    time.sleep(1)
    
    results["Envio de Email"] = test_email_sending()
    time.sleep(2)
    
    results["Upload de Comprovante"] = test_file_upload()
    time.sleep(1)
    
    results["Painel Admin"] = test_admin_panel()
    time.sleep(1)
    
    results["Endpoints de Pagamento"] = test_payment_endpoints()
    time.sleep(1)
    
    results["Sistema de Notificações"] = test_notifications()
    
    # Gerar relatório
    generate_report(results)
    
    # Salvar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"railway_verification_report_{timestamp}.json"
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "url": "https://web-production-1513a.up.railway.app",
        "results": results,
        "summary": {
            "total_tests": len(results),
            "passed_tests": sum(1 for result in results.values() if result),
            "failed_tests": sum(1 for result in results.values() if not result),
            "success_rate": (sum(1 for result in results.values() if result) / len(results)) * 100
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n💾 Relatório salvo em: {report_file}")

if __name__ == "__main__":
    main()