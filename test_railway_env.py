#!/usr/bin/env python3
"""
Script para testar as variáveis de ambiente do Railway
e verificar se o Resend está configurado corretamente
"""

import os
import requests
import json

def test_railway_environment():
    """Testa as variáveis de ambiente do Railway"""
    
    print("🔍 TESTANDO VARIÁVEIS DE AMBIENTE DO RAILWAY")
    print("=" * 50)
    
    # URL base do Railway
    base_url = "https://web-production-1513a.up.railway.app"
    
    # Teste 1: Verificar se a API está respondendo
    print("\n1. Testando conectividade com Railway...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ API Railway está respondendo")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ API Railway retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com Railway: {e}")
        return False
    
    # Teste 2: Criar um pagamento para testar o fluxo completo
    print("\n2. Criando pagamento de teste...")
    try:
        payment_data = {
            "amount": 100.00,
            "currency": "BRL",
            "payment_method": "pix",
            "customer_email": "hackintoshandbeyond@gmail.com",
            "customer_name": "Teste Railway"
        }
        
        response = requests.post(
            f"{base_url}/api/payments",
            json=payment_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            payment = response.json()
            payment_id = payment.get('id')
            print(f"✅ Pagamento criado: {payment_id}")
            
            # Teste 3: Fazer upload de comprovante
            print("\n3. Testando upload de comprovante...")
            
            # Criar arquivo de teste
            test_file_content = b"Teste de comprovante Railway - " + str(payment_id).encode()
            
            files = {
                'file': ('comprovante_test.txt', test_file_content, 'text/plain')
            }
            
            upload_response = requests.post(
                f"{base_url}/api/payments/{payment_id}/upload-proof",
                files=files,
                timeout=30
            )
            
            if upload_response.status_code == 200:
                print("✅ Upload realizado com sucesso")
                upload_result = upload_response.json()
                print(f"   Resultado: {upload_result}")
                
                # Verificar se a notificação foi enviada
                if upload_result.get('notification_sent'):
                    print("✅ Notificação enviada com sucesso")
                else:
                    print("❌ Notificação NÃO foi enviada")
                    print(f"   Detalhes: {upload_result}")
                
            else:
                print(f"❌ Erro no upload: {upload_response.status_code}")
                print(f"   Resposta: {upload_response.text}")
                
        else:
            print(f"❌ Erro ao criar pagamento: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False
    
    # Teste 4: Verificar logs do Railway (se possível)
    print("\n4. Verificando configuração de email...")
    print("   Para verificar se o Resend está configurado, precisamos:")
    print("   - Verificar se as variáveis de ambiente estão corretas")
    print("   - Verificar se o serviço foi reiniciado")
    print("   - Verificar se não há conflitos de configuração")
    
    return True

def check_railway_variables():
    """Verifica as variáveis que devem estar configuradas no Railway"""
    
    print("\n📋 VARIÁVEIS QUE DEVEM ESTAR CONFIGURADAS NO RAILWAY:")
    print("=" * 60)
    
    required_vars = {
        "RESEND_API_KEY": "re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1",
        "USE_RESEND": "true",
        "USE_SENDGRID": "false",
        "SMTP_ENABLED": "false",
        "EMAIL_PROVIDER": "resend"
    }
    
    print("✅ Variáveis obrigatórias:")
    for var, value in required_vars.items():
        print(f"   {var}={value}")
    
    print("\n❌ Variáveis que devem ser REMOVIDAS:")
    smtp_vars = [
        "SMTP_SERVER",
        "SMTP_PORT", 
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "FROM_EMAIL"
    ]
    
    for var in smtp_vars:
        print(f"   {var} (deve ser removida)")
    
    print("\n🔧 INSTRUÇÕES PARA CORRIGIR:")
    print("1. Acesse o painel do Railway")
    print("2. Vá em Variables")
    print("3. REMOVA todas as variáveis SMTP")
    print("4. CONFIGURE apenas as variáveis Resend")
    print("5. Salve e faça REDEPLOY")
    print("6. Aguarde o serviço reiniciar completamente")

if __name__ == "__main__":
    print("🚀 DIAGNÓSTICO COMPLETO DO RAILWAY")
    print("=" * 50)
    
    # Verificar variáveis
    check_railway_variables()
    
    # Testar ambiente
    test_railway_environment()
    
    print("\n" + "=" * 50)
    print("📊 RESUMO DO DIAGNÓSTICO:")
    print("Se o upload funcionou mas o email não foi enviado,")
    print("o problema está na configuração das variáveis de ambiente.")
    print("O Railway ainda está tentando usar SMTP em vez do Resend.")

