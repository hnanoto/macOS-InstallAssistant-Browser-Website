#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a configuração SMTP está funcionando
e se os emails estão sendo enviados corretamente
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

def test_smtp_configuration():
    """Testa a configuração SMTP"""
    print("🧪 Testando configuração SMTP...")
    
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    
    print(f"📧 Servidor: {smtp_server}")
    print(f"🔌 Porta: {smtp_port}")
    print(f"👤 Usuário: {smtp_username}")
    print(f"🔑 Senha configurada: {'✅ SIM' if smtp_password and smtp_password != 'your_app_password_here' else '❌ NÃO'}")
    
    if smtp_password == 'your_app_password_here':
        print("\n🚨 PROBLEMA ENCONTRADO!")
        print("A senha SMTP ainda está como placeholder.")
        print("Por favor, configure uma senha de aplicativo do Gmail no arquivo .env")
        return False
    
    if not smtp_password:
        print("\n🚨 PROBLEMA ENCONTRADO!")
        print("A senha SMTP não está configurada.")
        return False
    
    print("\n✅ Configuração SMTP parece estar correta!")
    return True

def test_payment_email_flow():
    """Testa o fluxo completo de pagamento e envio de email"""
    print("\n🧪 Testando fluxo de pagamento e email...")
    
    # URL da API
    base_url = "http://localhost:5001"
    
    # Dados do teste
    test_data = {
        "email": "teste@exemplo.com",
        "name": "Usuario Teste",
        "method": "pix"
    }
    
    try:
        # 1. Verificar se a API está rodando
        print("📡 Verificando se a API está rodando...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API não está rodando. Status: {response.status_code}")
            print("💡 Execute: python3 payment_api.py")
            return False
        
        print("✅ API está rodando!")
        
        # 2. Processar compra
        print("\n📝 Processando compra de teste...")
        response = requests.post(
            f"{base_url}/api/swift/process-purchase",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao processar compra: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
        purchase_result = response.json()
        print(f"✅ Compra processada: {purchase_result.get('payment_id', 'N/A')}")
        
        payment_id = purchase_result.get('payment_id')
        if not payment_id:
            print("❌ Payment ID não encontrado")
            return False
            
        # 3. Confirmar pagamento (isso deve enviar o email)
        print("\n💳 Confirmando pagamento (enviando email)...")
        confirm_data = {
            "payment_id": payment_id,
            "email": test_data["email"]
        }
        
        response = requests.post(
            f"{base_url}/api/swift/confirm-payment",
            json=confirm_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao confirmar pagamento: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
        confirm_result = response.json()
        print(f"✅ Pagamento confirmado!")
        
        # 4. Verificar se o email foi enviado
        email_sent = confirm_result.get('email_sent', False)
        notification_sent = confirm_result.get('notification_sent', False)
        serial = confirm_result.get('serial')
        
        print(f"\n📊 Resultados:")
        print(f"📧 Email para cliente enviado: {'✅ SIM' if email_sent else '❌ NÃO'}")
        print(f"📧 Notificação admin enviada: {'✅ SIM' if notification_sent else '❌ NÃO'}")
        print(f"🔑 Serial gerado: {serial}")
        
        if email_sent and notification_sent and serial:
            print("\n🎉 SUCESSO! Emails estão sendo enviados corretamente!")
            return True
        else:
            print("\n⚠️ PROBLEMA! Alguns emails não foram enviados.")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API.")
        print("💡 Certifique-se de que o servidor está rodando:")
        print("   python3 payment_api.py")
        return False
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def main():
    """Função principal"""
    print("🔧 TESTE DE CORREÇÃO - Sistema de Email")
    print("=" * 50)
    
    # Teste 1: Configuração SMTP
    smtp_ok = test_smtp_configuration()
    
    if not smtp_ok:
        print("\n🛑 TESTE INTERROMPIDO")
        print("Configure a senha SMTP antes de continuar.")
        return False
    
    # Teste 2: Fluxo de pagamento e email
    flow_ok = test_payment_email_flow()
    
    print("\n" + "=" * 50)
    if smtp_ok and flow_ok:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de email está funcionando corretamente")
        return True
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique a configuração e tente novamente")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
