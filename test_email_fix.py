#!/usr/bin/env python3
"""
Script de teste para verificar se as correções de e-mail estão funcionando
"""

import requests
import json
import time

# Configuração
BASE_URL = "https://web-production-1513a.up.railway.app"
# BASE_URL = "http://localhost:5001"  # Para teste local

def test_smtp_config():
    """Testa a configuração SMTP"""
    print("🔍 Testando configuração SMTP...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/debug/smtp", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Configuração SMTP:")
            print(f"   Servidor: {config['smtp_server']}:{config['smtp_port']}")
            print(f"   Usuário: {config['smtp_username']}")
            print(f"   Senha configurada: {config['smtp_password_set']}")
            print(f"   Email remetente: {config['from_email']}")
            return config['smtp_password_set']
        else:
            print(f"❌ Erro ao obter configuração SMTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar configuração SMTP: {e}")
        return False

def test_email_sending():
    """Testa o envio de e-mail"""
    print("\n📧 Testando envio de e-mail...")
    
    try:
        payload = {
            "email": "hackintoshandbeyond@gmail.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/debug/test-email",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print(f"✅ E-mail de teste enviado com sucesso!")
                print(f"   Destinatário: {result['test_email']}")
                return True
            else:
                print(f"❌ Falha ao enviar e-mail: {result.get('error', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar envio de e-mail: {e}")
        return False

def test_proof_email():
    """Testa o envio de e-mail de comprovante"""
    print("\n📋 Testando envio de e-mail de comprovante...")
    
    try:
        payload = {
            "payment_id": "pix_test_20250919_120000_test",
            "email": "test@example.com",
            "name": "Cliente Teste",
            "filename": "comprovante_teste.png"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/debug/test-proof-email",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print(f"✅ E-mail de comprovante enviado com sucesso!")
                print(f"   Payment ID: {result['payment_id']}")
                print(f"   Email: {result['email']}")
                print(f"   Email configurado: {result['email_configured']}")
                return True
            else:
                print(f"❌ Falha ao enviar e-mail de comprovante: {result.get('error', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar e-mail de comprovante: {e}")
        return False

def test_quick_approve():
    """Testa a aprovação rápida de pagamento"""
    print("\n🚀 Testando aprovação rápida de pagamento...")
    
    try:
        # Primeiro, vamos ver se há pagamentos pendentes
        response = requests.get(f"{BASE_URL}/api/admin/pending-payments", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            pending_payments = result.get('pending_payments', [])
            
            if pending_payments:
                # Usar o primeiro pagamento pendente
                payment = pending_payments[0]
                payment_id = payment['payment_id']
                
                print(f"   Encontrado pagamento pendente: {payment_id}")
                
                # Aprovar o pagamento
                approve_payload = {"payment_id": payment_id}
                
                approve_response = requests.post(
                    f"{BASE_URL}/api/debug/quick-approve",
                    json=approve_payload,
                    timeout=30
                )
                
                if approve_response.status_code == 200:
                    approve_result = approve_response.json()
                    if approve_result['success']:
                        print(f"✅ Pagamento aprovado com sucesso!")
                        print(f"   Payment ID: {approve_result['payment_id']}")
                        print(f"   Status: {approve_result['status']}")
                        print(f"   Serial: {approve_result.get('serial', 'N/A')}")
                        print(f"   Email: {approve_result.get('email', 'N/A')}")
                        return True
                    else:
                        print(f"❌ Falha ao aprovar pagamento: {approve_result.get('error', 'Erro desconhecido')}")
                        return False
                else:
                    print(f"❌ Erro HTTP na aprovação: {approve_response.status_code}")
                    print(f"   Resposta: {approve_response.text}")
                    return False
            else:
                print("⚠️ Nenhum pagamento pendente encontrado para testar")
                return True  # Não é um erro, só não há nada para testar
        else:
            print(f"❌ Erro ao buscar pagamentos pendentes: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar aprovação rápida: {e}")
        return False

def test_health():
    """Testa se o servidor está funcionando"""
    print("🏥 Testando saúde do servidor...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Servidor funcionando: {health['status']}")
            print(f"   Versão: {health['version']}")
            print(f"   Timestamp: {health['timestamp']}")
            return True
        else:
            print(f"❌ Servidor com problemas: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar servidor: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 Iniciando testes de correção de e-mail...")
    print(f"🌐 URL base: {BASE_URL}")
    print("=" * 60)
    
    # Teste 1: Saúde do servidor
    server_ok = test_health()
    if not server_ok:
        print("\n❌ Servidor não está funcionando. Abortando testes.")
        return
    
    # Teste 2: Configuração SMTP
    smtp_configured = test_smtp_config()
    if not smtp_configured:
        print("\n⚠️ SMTP não está configurado. Configure as variáveis de ambiente no Railway.")
        print("   Consulte o arquivo RAILWAY_EMAIL_SETUP.md para instruções.")
        return
    
    # Teste 3: Envio de e-mail
    email_ok = test_email_sending()
    
    # Teste 4: E-mail de comprovante
    proof_email_ok = test_proof_email()
    
    # Teste 5: Aprovação rápida
    quick_approve_ok = test_quick_approve()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES:")
    print(f"   Servidor: {'✅ OK' if server_ok else '❌ FALHA'}")
    print(f"   SMTP Configurado: {'✅ OK' if smtp_configured else '❌ FALHA'}")
    print(f"   E-mail de Teste: {'✅ OK' if email_ok else '❌ FALHA'}")
    print(f"   E-mail de Comprovante: {'✅ OK' if proof_email_ok else '❌ FALHA'}")
    print(f"   Aprovação Rápida: {'✅ OK' if quick_approve_ok else '❌ FALHA'}")
    
    if all([server_ok, smtp_configured, email_ok, proof_email_ok, quick_approve_ok]):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   O sistema de e-mail está funcionando corretamente.")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM!")
        print("   Verifique a configuração no Railway e os logs do servidor.")
    
    print("\n📋 Próximos passos:")
    print("   1. Verifique se os e-mails chegaram na caixa de entrada")
    print("   2. Teste o fluxo completo de upload de comprovante")
    print("   3. Monitore os logs do Railway para erros")

if __name__ == "__main__":
    main()