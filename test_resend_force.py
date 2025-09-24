#!/usr/bin/env python3
"""
🚀 TESTE FORÇADO DO RESEND
=========================

Este script força o envio de email via Resend diretamente.
"""

import requests
import json
from datetime import datetime

def test_resend_force():
    """Força o envio via Resend"""
    print("🚀 TESTE FORÇADO DO RESEND")
    print("=" * 50)
    
    try:
        # Teste direto via Resend
        response = requests.post(
            "https://web-production-1513a.up.railway.app/api/debug/test-proof-email",
            json={
                "email": "hackintoshandbeyond@gmail.com",
                "name": "Teste Forçado Resend",
                "payment_id": "test_force_resend_456",
                "method": "pix",
                "amount": 100,
                "currency": "BRL",
                "filename": "test_force_resend.pdf"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Resultado: {result}")
            
            if result.get('success'):
                print("✅ Email enviado com sucesso!")
                return True
            else:
                print(f"❌ Email falhou: {result.get('error')}")
                return False
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_upload_with_email():
    """Testa upload com envio de email"""
    print("\n📤 TESTE DE UPLOAD COM EMAIL")
    print("=" * 50)
    
    try:
        # Criar pagamento
        payment_response = requests.post(
            "https://web-production-1513a.up.railway.app/api/create-pix-payment",
            json={
                "email": "hackintoshandbeyond@gmail.com",
                "name": "Teste Upload Email",
                "country": "BR",
                "amount": 75,
                "currency": "BRL"
            },
            timeout=30
        )
        
        if payment_response.status_code == 200:
            payment_data = payment_response.json()
            payment_id = payment_data.get('payment_id')
            print(f"✅ Pagamento criado: {payment_id}")
            
            # Criar arquivo de teste
            with open('test_upload_email.pdf', 'w') as f:
                f.write("Teste de upload com email")
            
            # Upload do comprovante
            with open('test_upload_email.pdf', 'rb') as f:
                upload_response = requests.post(
                    "https://web-production-1513a.up.railway.app/api/upload-payment-proof",
                    files={'file': f},
                    data={
                        'payment_id': payment_id,
                        'email': 'hackintoshandbeyond@gmail.com'
                    },
                    timeout=30
                )
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                print(f"✅ Upload realizado: {upload_data}")
                return True
            else:
                print(f"❌ Upload falhou: {upload_response.status_code}")
                return False
        else:
            print(f"❌ Criação de pagamento falhou: {payment_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("🚀 TESTE COMPLETO DO RESEND")
    print("=" * 60)
    print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
    
    # Testes
    resend_test = test_resend_force()
    upload_test = test_upload_with_email()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    print(f"✅ Teste Resend: {'FUNCIONANDO' if resend_test else 'FALHANDO'}")
    print(f"✅ Teste Upload: {'FUNCIONANDO' if upload_test else 'FALHANDO'}")
    
    if resend_test or upload_test:
        print("\n🎉 SUCESSO: Sistema funcionando!")
        print("📧 Verifique seu Gmail agora!")
    else:
        print("\n❌ FALHA: Sistema não está funcionando")
        print("🔧 Solução: Verificar configuração das variáveis")

if __name__ == "__main__":
    main()

