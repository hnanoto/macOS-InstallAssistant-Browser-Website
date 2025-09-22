#!/usr/bin/env python3
"""
Teste de configuração do Railway
Verifica se todas as variáveis de ambiente estão configuradas corretamente
"""

import os
import requests
import json
from datetime import datetime

def test_railway_environment():
    """Testa se estamos rodando no Railway"""
    print("🔍 Verificando ambiente Railway...")
    
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    port = os.getenv('PORT')
    
    print(f"✅ Railway detectado: {is_railway}")
    print(f"✅ Porta Railway: {port}")
    
    return is_railway

def test_email_configuration():
    """Testa configuração de email"""
    print("\n📧 Verificando configuração de email...")
    
    # Verificar variáveis SMTP
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    
    print(f"SMTP_SERVER: {smtp_server}")
    print(f"SMTP_PORT: {smtp_port}")
    print(f"SMTP_USERNAME: {smtp_username}")
    print(f"SMTP_PASSWORD: {'✅ Configurado' if smtp_password else '❌ Não configurado'}")
    print(f"FROM_EMAIL: {from_email}")
    
    # Verificar Resend
    resend_key = os.getenv('RESEND_API_KEY')
    print(f"RESEND_API_KEY: {'✅ Configurado' if resend_key else '❌ Não configurado'}")
    
    # Verificar SendGrid
    sendgrid_key = os.getenv('SENDGRID_API_KEY')
    print(f"SENDGRID_API_KEY: {'✅ Configurado' if sendgrid_key else '❌ Não configurado'}")
    
    # Verificar configuração de email
    email_configured = bool(
        (smtp_password and smtp_password.strip() and smtp_password != 'your_app_password_here') or
        (resend_key and resend_key.strip()) or
        (sendgrid_key and sendgrid_key.strip())
    )
    
    print(f"\n📧 Email configurado: {'✅ SIM' if email_configured else '❌ NÃO'}")
    
    return email_configured

def test_api_endpoints():
    """Testa endpoints da API"""
    print("\n🌐 Testando endpoints da API...")
    
    # Determinar URL base
    if os.getenv('RAILWAY_ENVIRONMENT'):
        base_url = os.getenv('APP_BASE_URL', 'https://web-production-1513a.up.railway.app')
    else:
        base_url = 'http://localhost:5001'
    
    print(f"Base URL: {base_url}")
    
    # Testar health check
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check: OK")
            return True
        else:
            print(f"❌ Health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

def test_email_debug_endpoints():
    """Testa endpoints de debug de email"""
    print("\n🧪 Testando endpoints de debug de email...")
    
    # Determinar URL base
    if os.getenv('RAILWAY_ENVIRONMENT'):
        base_url = os.getenv('APP_BASE_URL', 'https://web-production-1513a.up.railway.app')
    else:
        base_url = 'http://localhost:5001'
    
    endpoints = [
        '/api/debug/smtp',
        '/api/debug/resend-test',
        '/api/debug/sendgrid-test'
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            results[endpoint] = {
                'status': response.status_code,
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            results[endpoint] = {'error': str(e)}
            print(f"❌ {endpoint}: {e}")
    
    return results

def test_email_sending():
    """Testa envio de email"""
    print("\n📤 Testando envio de email...")
    
    # Determinar URL base
    if os.getenv('RAILWAY_ENVIRONMENT'):
        base_url = os.getenv('APP_BASE_URL', 'https://web-production-1513a.up.railway.app')
    else:
        base_url = 'http://localhost:5001'
    
    test_data = {
        "email": "hackintoshandbeyond@gmail.com",
        "subject": "Teste Railway - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": "Este é um teste de email do Railway"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/debug/test-email",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email enviado: {result}")
            return True
        else:
            print(f"❌ Erro no envio: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def generate_railway_config():
    """Gera configuração para o Railway"""
    print("\n⚙️ Gerando configuração para Railway...")
    
    config = {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "hackintoshandbeyond@gmail.com",
        "SMTP_PASSWORD": "pvqd jzvt sjyz azwn",
        "FROM_EMAIL": "hackintoshandbeyond@gmail.com",
        "EMAIL_FROM": "hackintoshandbeyond@gmail.com",
        "EMAIL_TO_DEFAULT": "hackintoshandbeyond@gmail.com",
        "REPLY_TO_DEFAULT": "hackintoshandbeyond@gmail.com",
        "RESEND_API_KEY": "re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1",
        "RAILWAY_ENVIRONMENT": "production",
        "APP_BASE_URL": "https://web-production-1513a.up.railway.app",
        "DEBUG": "false"
    }
    
    print("📋 Variáveis de ambiente necessárias no Railway:")
    for key, value in config.items():
        if 'PASSWORD' in key or 'API_KEY' in key:
            print(f"{key}=***HIDDEN***")
        else:
            print(f"{key}={value}")
    
    # Salvar em arquivo
    with open('railway_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n💾 Configuração salva em: railway_config.json")
    
    return config

def main():
    """Função principal"""
    print("🚀 TESTE DE CONFIGURAÇÃO DO RAILWAY")
    print("=" * 50)
    
    # Teste 1: Ambiente Railway
    is_railway = test_railway_environment()
    
    # Teste 2: Configuração de email
    email_configured = test_email_configuration()
    
    # Teste 3: Endpoints da API
    api_working = test_api_endpoints()
    
    # Teste 4: Debug endpoints
    debug_results = test_email_debug_endpoints()
    
    # Teste 5: Envio de email
    if api_working:
        email_working = test_email_sending()
    else:
        email_working = False
        print("⚠️ Pulando teste de email - API não está respondendo")
    
    # Teste 6: Gerar configuração
    config = generate_railway_config()
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    print(f"🌐 Ambiente Railway: {'✅' if is_railway else '❌'}")
    print(f"📧 Email configurado: {'✅' if email_configured else '❌'}")
    print(f"🔗 API funcionando: {'✅' if api_working else '❌'}")
    print(f"📤 Email funcionando: {'✅' if email_working else '❌'}")
    
    if not email_configured:
        print("\n⚠️ PROBLEMAS IDENTIFICADOS:")
        print("1. Variáveis de ambiente de email não configuradas no Railway")
        print("2. Configure as variáveis listadas acima no painel do Railway")
        print("3. Redeploy o projeto após configurar as variáveis")
    
    if not api_working:
        print("\n⚠️ PROBLEMAS DE API:")
        print("1. Servidor não está respondendo")
        print("2. Verifique se o deploy foi bem-sucedido")
        print("3. Verifique os logs do Railway")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Configure as variáveis de ambiente no Railway")
    print("2. Redeploy o projeto")
    print("3. Execute este teste novamente")
    print("4. Teste o fluxo completo de pagamento")

if __name__ == "__main__":
    main()