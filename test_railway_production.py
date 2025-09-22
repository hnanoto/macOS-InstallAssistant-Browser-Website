#!/usr/bin/env python3
"""
Teste específico para Railway em produção
Verifica se o sistema de emails está funcionando no Railway
"""

import requests
import json
from datetime import datetime

# URL do Railway em produção
RAILWAY_URL = "https://web-production-1513a.up.railway.app"

def test_railway_health():
    """Testa se o Railway está respondendo"""
    print("🔍 Testando saúde do Railway...")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Railway está online: {data}")
            return True
        else:
            print(f"❌ Railway retornou: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao conectar no Railway: {e}")
        return False

def test_railway_smtp_config():
    """Testa configuração SMTP no Railway"""
    print("\n📧 Testando configuração SMTP no Railway...")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/api/debug/smtp", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Configuração SMTP: {data}")
            
            # Verificar se está configurado
            if data.get('configured'):
                print("✅ SMTP está configurado no Railway")
                return True
            else:
                print("❌ SMTP NÃO está configurado no Railway")
                print("🔧 Variáveis necessárias:")
                print("   - SMTP_SERVER=smtp.gmail.com")
                print("   - SMTP_PORT=587")
                print("   - SMTP_USERNAME=hackintoshandbeyond@gmail.com")
                print("   - SMTP_PASSWORD=pvqd jzvt sjyz azwn")
                print("   - FROM_EMAIL=hackintoshandbeyond@gmail.com")
                return False
        else:
            print(f"❌ Erro na verificação SMTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar SMTP: {e}")
        return False

def test_railway_resend():
    """Testa Resend no Railway"""
    print("\n📤 Testando Resend no Railway...")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/api/debug/resend-test", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resend funcionando: {data}")
            return True
        else:
            print(f"❌ Resend falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no Resend: {e}")
        return False

def test_railway_email_sending():
    """Testa envio de email no Railway"""
    print("\n📧 Testando envio de email no Railway...")
    
    test_data = {
        "email": "hackintoshandbeyond@gmail.com",
        "subject": f"Teste Railway Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "message": "Este é um teste de email enviado do Railway em produção"
    }
    
    try:
        response = requests.post(
            f"{RAILWAY_URL}/api/debug/test-email",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Email enviado com sucesso: {data}")
            return True
        else:
            print(f"❌ Falha no envio: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Detalhes do erro: {error_data}")
            except:
                print(f"❌ Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_railway_upload_proof():
    """Testa upload de comprovante no Railway"""
    print("\n📤 Testando upload de comprovante no Railway...")
    
    # Criar dados de teste
    test_data = {
        'payment_id': f'pix_railway_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'email': 'hackintoshandbeyond@gmail.com',
        'name': 'Teste Railway',
        'amount': '29.90'
    }
    
    # Criar arquivo de teste (simulado)
    test_file_content = b'Test proof file content'
    
    try:
        files = {
            'file': ('test_proof.txt', test_file_content, 'text/plain')
        }
        
        response = requests.post(
            f"{RAILWAY_URL}/api/upload-payment-proof",
            data=test_data,
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload realizado: {data}")
            return True
        else:
            print(f"❌ Falha no upload: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Detalhes: {error_data}")
            except:
                print(f"❌ Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        return False

def test_railway_admin_panel():
    """Testa painel admin no Railway"""
    print("\n👨‍💼 Testando painel admin no Railway...")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/admin", timeout=10)
        
        if response.status_code == 200:
            print("✅ Painel admin acessível")
            return True
        else:
            print(f"❌ Painel admin: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no painel admin: {e}")
        return False

def test_railway_pending_payments():
    """Testa listagem de pagamentos pendentes"""
    print("\n📋 Testando pagamentos pendentes no Railway...")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/api/admin/pending-payments", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pagamentos pendentes: {len(data.get('payments', []))} encontrados")
            return True
        else:
            print(f"❌ Erro nos pagamentos: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na consulta: {e}")
        return False

def generate_railway_fix_instructions():
    """Gera instruções para corrigir o Railway"""
    print("\n🔧 INSTRUÇÕES PARA CORRIGIR O RAILWAY")
    print("=" * 50)
    
    instructions = """
1. ACESSE O PAINEL DO RAILWAY:
   - Vá para https://railway.app
   - Faça login com sua conta
   - Selecione seu projeto

2. CONFIGURE AS VARIÁVEIS DE AMBIENTE:
   - Clique em "Variables" no painel lateral
   - Adicione as seguintes variáveis:

   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=hackintoshandbeyond@gmail.com
   SMTP_PASSWORD=pvqd jzvt sjyz azwn
   FROM_EMAIL=hackintoshandbeyond@gmail.com
   EMAIL_FROM=hackintoshandbeyond@gmail.com
   EMAIL_TO_DEFAULT=hackintoshandbeyond@gmail.com
   REPLY_TO_DEFAULT=hackintoshandbeyond@gmail.com
   RESEND_API_KEY=re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1
   RAILWAY_ENVIRONMENT=production
   APP_BASE_URL=https://web-production-1513a.up.railway.app
   DEBUG=false

3. REDEPLOY O PROJETO:
   - Após configurar as variáveis, clique em "Deploy"
   - Aguarde o deploy terminar (pode levar alguns minutos)

4. TESTE NOVAMENTE:
   - Execute este script novamente
   - Verifique se os emails estão sendo enviados

5. MONITORE OS LOGS:
   - Vá em "Deployments" > "View Logs"
   - Procure por mensagens de email
   - Verifique se há erros de SMTP
"""
    
    print(instructions)
    
    # Salvar instruções em arquivo
    with open('railway_fix_instructions.txt', 'w') as f:
        f.write(instructions)
    
    print("💾 Instruções salvas em: railway_fix_instructions.txt")

def main():
    """Função principal"""
    print("🚀 TESTE DO RAILWAY EM PRODUÇÃO")
    print("=" * 50)
    print(f"🌐 URL: {RAILWAY_URL}")
    print("=" * 50)
    
    # Executar testes
    tests = [
        ("Health Check", test_railway_health),
        ("Configuração SMTP", test_railway_smtp_config),
        ("Resend API", test_railway_resend),
        ("Envio de Email", test_railway_email_sending),
        ("Upload de Comprovante", test_railway_upload_proof),
        ("Painel Admin", test_railway_admin_panel),
        ("Pagamentos Pendentes", test_railway_pending_payments)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Erro no teste {test_name}: {e}")
            results[test_name] = False
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{total} testes passaram")
    
    if passed < total:
        print("\n⚠️ PROBLEMAS IDENTIFICADOS:")
        for test_name, result in results.items():
            if not result:
                print(f"   ❌ {test_name}")
        
        generate_railway_fix_instructions()
    else:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   O Railway está funcionando corretamente!")

if __name__ == "__main__":
    main()