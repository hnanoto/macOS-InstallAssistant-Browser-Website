#!/usr/bin/env python3
"""
Teste completo de todas as opções de e-mail no Railway
"""

import requests
import json
import time

BASE_URL = "https://web-production-1513a.up.railway.app"

def test_sendgrid():
    """Teste 1: SendGrid"""
    print("🧪 Teste 1: SendGrid")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/debug/sendgrid-test", timeout=10)
        result = response.json()
        
        if result.get('success'):
            print("✅ SendGrid funcionando!")
            print(f"   Status: {result.get('status_code')}")
            print(f"   Mensagem: {result.get('message')}")
            return True
        else:
            print("❌ SendGrid falhou!")
            print(f"   Erro: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste SendGrid: {e}")
        return False

def test_notification_system():
    """Teste 2: Sistema de Notificação (Arquivo)"""
    print("\n🧪 Teste 2: Sistema de Notificação (Arquivo)")
    print("=" * 50)
    
    try:
        payload = {
            "email": "hackintoshandbeyond@gmail.com",
            "message": "Teste de notificação via arquivo"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/debug/notification-test", 
            json=payload, 
            timeout=10
        )
        result = response.json()
        
        if result.get('success'):
            print("✅ Sistema de notificação funcionando!")
            print(f"   Mensagem: {result.get('message')}")
            print(f"   Notificação: {result.get('notification')}")
            return True
        else:
            print("❌ Sistema de notificação falhou!")
            print(f"   Erro: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de notificação: {e}")
        return False

def test_webhook_system():
    """Teste 3: Sistema de Webhook"""
    print("\n🧪 Teste 3: Sistema de Webhook")
    print("=" * 50)
    
    try:
        payload = {
            "message": "Teste de webhook para notificações"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/debug/webhook-test", 
            json=payload, 
            timeout=10
        )
        result = response.json()
        
        if result.get('success'):
            print("✅ Sistema de webhook funcionando!")
            print(f"   Mensagem: {result.get('message')}")
            print(f"   URL: {result.get('webhook_url')}")
            return True
        else:
            print("❌ Sistema de webhook falhou!")
            print(f"   Erro: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de webhook: {e}")
        return False

def test_server_health():
    """Teste de saúde do servidor"""
    print("🏥 Testando saúde do servidor...")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        result = response.json()
        
        if result.get('status') == 'healthy':
            print("✅ Servidor funcionando!")
            print(f"   Versão: {result.get('version')}")
            print(f"   Timestamp: {result.get('timestamp')}")
            return True
        else:
            print("❌ Servidor com problemas!")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de saúde: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 TESTE COMPLETO DE TODAS AS OPÇÕES DE E-MAIL")
    print("=" * 60)
    
    # Teste de saúde
    server_ok = test_server_health()
    
    if not server_ok:
        print("\n❌ Servidor não está funcionando. Abortando testes.")
        return
    
    # Testes das opções
    results = {
        'sendgrid': test_sendgrid(),
        'notification': test_notification_system(),
        'webhook': test_webhook_system()
    }
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL DOS TESTES:")
    print("=" * 60)
    
    for option, success in results.items():
        status = "✅ FUNCIONANDO" if success else "❌ FALHOU"
        print(f"   {option.upper()}: {status}")
    
    # Recomendação
    working_options = [option for option, success in results.items() if success]
    
    if working_options:
        print(f"\n🎯 RECOMENDAÇÃO:")
        print(f"   Use: {', '.join(working_options).upper()}")
        
        if 'notification' in working_options:
            print("   📝 Sistema de notificação é a opção mais confiável!")
        elif 'webhook' in working_options:
            print("   📡 Webhook é uma boa alternativa!")
        elif 'sendgrid' in working_options:
            print("   📧 SendGrid funcionando perfeitamente!")
    else:
        print("\n❌ NENHUMA OPÇÃO FUNCIONANDO!")
        print("   Verifique a configuração do Railway.")

if __name__ == "__main__":
    main()
