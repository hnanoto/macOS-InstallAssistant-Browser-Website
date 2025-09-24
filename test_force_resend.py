#!/usr/bin/env python3
"""
🚀 TESTE FORÇADO DO RESEND
=========================

Este script força o envio de email via Resend diretamente.
"""

import requests
import json
from datetime import datetime

def test_force_resend():
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
                "payment_id": "test_force_resend_123",
                "method": "pix",
                "amount": 100,
                "currency": "BRL",
                "filename": "test_force_resend.pdf",
                "force_resend": True
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

def main():
    print("🚀 TESTE FORÇADO DO RESEND")
    print("=" * 60)
    print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
    
    success = test_force_resend()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCESSO: Email enviado via Resend!")
        print("📧 Verifique seu Gmail agora!")
    else:
        print("❌ FALHA: Email não foi enviado")
        print("🔧 Solução: Redeploy no Railway")

if __name__ == "__main__":
    main()

