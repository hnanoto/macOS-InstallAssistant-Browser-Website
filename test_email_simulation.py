#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para demonstrar a diferença entre modo simulação e envio real
"""

import requests
import json

def test_email_simulation():
    """Testa o envio de email em modo simulação"""
    print("🧪 TESTE: Modo Simulação vs Envio Real")
    print("=" * 50)
    
    # Dados do teste
    test_data = {
        "email": "teste@exemplo.com",
        "name": "Usuario Teste",
        "method": "pix"
    }
    
    try:
        # 1. Processar compra
        print("📝 1. Processando compra...")
        response = requests.post(
            "http://localhost:5001/api/swift/process-purchase",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Erro: {response.status_code}")
            return
        
        purchase_result = response.json()
        payment_id = purchase_result.get('payment_id')
        print(f"✅ Compra processada: {payment_id}")
        
        # 2. Confirmar pagamento (isso simula o envio de email)
        print("\n💳 2. Confirmando pagamento...")
        confirm_data = {
            "payment_id": payment_id,
            "email": test_data["email"]
        }
        
        response = requests.post(
            "http://localhost:5001/api/swift/confirm-payment",
            json=confirm_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Erro: {response.status_code}")
            return
        
        confirm_result = response.json()
        print(f"✅ Pagamento confirmado!")
        
        # 3. Mostrar resultados
        email_sent = confirm_result.get('email_sent', False)
        serial = confirm_result.get('serial')
        
        print(f"\n📊 RESULTADOS:")
        print(f"📧 Email enviado: {'✅ SIM' if email_sent else '❌ NÃO'}")
        print(f"🔑 Serial gerado: {serial}")
        
        print(f"\n🔍 EXPLICAÇÃO:")
        if email_sent:
            print("✅ O sistema retornou 'email_sent: true'")
            print("⚠️  MAS o email foi apenas SIMULADO (não enviado realmente)")
            print("💡 Para envio real, configure SMTP_PASSWORD no arquivo .env")
        else:
            print("❌ O sistema retornou 'email_sent: false'")
            print("🔧 Verifique os logs do servidor para mais detalhes")
        
        print(f"\n📋 PRÓXIMOS PASSOS:")
        print("1. Configure uma senha de aplicativo do Gmail")
        print("2. Atualize SMTP_PASSWORD no arquivo .env")
        print("3. Reinicie o servidor")
        print("4. Teste novamente")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_email_simulation()
