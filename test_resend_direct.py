#!/usr/bin/env python3
"""
🔄 TESTE DIRETO DO RESEND
========================

Este script testa o Resend diretamente para verificar se está funcionando.
"""

import requests
import json
from datetime import datetime

def test_resend_direct():
    """Testa Resend diretamente"""
    print("🔄 TESTANDO RESEND DIRETAMENTE")
    print("=" * 50)
    
    # API Key do Resend
    api_key = "re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1"
    
    try:
        import resend
        
        resend.api_key = api_key
        
        params = {
            "from": "onboarding@resend.dev",
            "to": ["hackintoshandbeyond@gmail.com"],
            "subject": "TESTE DIRETO - Resend Funcionando",
            "html": f'''
            <h2>🎉 Resend Funcionando!</h2>
            <p>Este email foi enviado diretamente via Resend.</p>
            <p>Se você receber este email, o Resend está funcionando perfeitamente.</p>
            <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
            '''
        }
        
        response = resend.Emails.send(params)
        
        if response:
            print("✅ Resend funcionando! Email enviado com sucesso.")
            print(f"   Response: {response}")
            return True
        else:
            print("❌ Resend falhou: Nenhuma resposta")
            return False
            
    except ImportError:
        print("❌ Resend não instalado")
        return False
    except Exception as e:
        print(f"❌ Erro no Resend: {e}")
        return False

def test_railway_resend():
    """Testa Resend via Railway"""
    print("\n🌐 TESTANDO RESEND VIA RAILWAY")
    print("=" * 50)
    
    try:
        # Teste via endpoint de notificação
        response = requests.post(
            "https://web-production-1513a.up.railway.app/api/debug/test-proof-email",
            json={
                "email": "hackintoshandbeyond@gmail.com",
                "name": "Teste Resend",
                "payment_id": "test_resend_123",
                "method": "pix",
                "amount": 100,
                "currency": "BRL",
                "filename": "test_resend.pdf"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Resultado do teste: {result}")
            
            if result.get('success'):
                print("✅ Email enviado com sucesso via Railway")
                return True
            else:
                print(f"❌ Email falhou: {result.get('error')}")
                return False
        else:
            print(f"❌ Erro no teste de email: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de email: {e}")
        return False

def main():
    print("🔄 TESTE COMPLETO DO RESEND")
    print("=" * 60)
    print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
    
    # Testes
    resend_direct = test_resend_direct()
    railway_resend = test_railway_resend()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    print(f"✅ Resend Direto: {'FUNCIONANDO' if resend_direct else 'FALHANDO'}")
    print(f"✅ Resend Railway: {'FUNCIONANDO' if railway_resend else 'FALHANDO'}")
    
    if resend_direct and not railway_resend:
        print("\n🔧 DIAGNÓSTICO:")
        print("   • Resend funciona localmente")
        print("   • Resend não está configurado no Railway")
        print("   • Verifique as variáveis de ambiente no Railway")
        
    elif not resend_direct:
        print("\n🔧 DIAGNÓSTICO:")
        print("   • Resend não está funcionando")
        print("   • Verifique a API Key")
        print("   • Verifique a conta Resend")
        
    elif railway_resend:
        print("\n🎉 SUCESSO:")
        print("   • Sistema de email funcionando!")
        print("   • Verifique seu Gmail")
        
    else:
        print("\n❌ PROBLEMA:")
        print("   • Sistema de email não está funcionando")
        print("   • Requer investigação adicional")

if __name__ == "__main__":
    main()

