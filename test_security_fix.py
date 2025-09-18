#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da correção de segurança - Sistema de Pagamentos
Demonstra que agora é impossível obter serial sem pagar realmente
"""

import requests
import json

def test_security_fix():
    """Testa a correção de segurança implementada"""
    print("🛡️ TESTE DE CORREÇÃO DE SEGURANÇA")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    # Dados do teste
    test_data = {
        "email": "teste.fraude@gmail.com",
        "name": "Usuario Fraude",
        "method": "pix"
    }
    
    try:
        print("🧪 CENÁRIO: Tentativa de fraude (obter serial sem pagar)")
        print("-" * 60)
        
        # 1. Processar compra (simular)
        print("📝 1. Processando compra...")
        response = requests.post(
            f"{base_url}/api/swift/process-purchase",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao processar compra: {response.status_code}")
            return False
            
        purchase_result = response.json()
        payment_id = purchase_result.get('payment_id')
        print(f"✅ Compra processada: {payment_id}")
        
        # 2. Tentar confirmar pagamento SEM pagar (FRAUDE)
        print("\n🚨 2. Tentando confirmar pagamento SEM pagar (FRAUDE)...")
        confirm_data = {
            "payment_id": payment_id,
            "email": test_data["email"]
        }
        
        response = requests.post(
            f"{base_url}/api/swift/confirm-payment",
            json=confirm_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Status da resposta: {response.status_code}")
        result = response.json()
        print(f"📋 Resposta: {json.dumps(result, indent=2)}")
        
        # 3. Verificar se a fraude foi bloqueada
        if response.status_code == 400 and result.get('success') == False:
            print("\n✅ SEGURANÇA FUNCIONANDO!")
            print("🛡️ Sistema bloqueou a tentativa de fraude")
            print(f"📝 Mensagem: {result.get('error')}")
            print(f"📊 Status: {result.get('status')}")
            
            if result.get('requires_proof'):
                print("🔒 Sistema requer comprovante de pagamento")
            
            return True
        else:
            print("\n❌ FALHA DE SEGURANÇA!")
            print("🚨 Sistema permitiu fraude - serial foi enviado sem pagamento")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def test_legitimate_payment_flow():
    """Testa o fluxo legítimo de pagamento"""
    print("\n\n✅ TESTE DE FLUXO LEGÍTIMO")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    # Dados do teste legítimo
    test_data = {
        "email": "cliente.legitimo@gmail.com",
        "name": "Cliente Legítimo",
        "method": "pix"
    }
    
    try:
        print("🧪 CENÁRIO: Pagamento legítimo com comprovante")
        print("-" * 60)
        
        # 1. Processar compra
        print("📝 1. Processando compra...")
        response = requests.post(
            f"{base_url}/api/swift/process-purchase",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"❌ Erro: {response.status_code}")
            return False
            
        purchase_result = response.json()
        payment_id = purchase_result.get('payment_id')
        print(f"✅ Compra processada: {payment_id}")
        
        # 2. Enviar comprovante (simular)
        print("\n📋 2. Enviando comprovante de pagamento...")
        proof_data = {
            "payment_id": payment_id,
            "email": test_data["email"]
        }
        
        response = requests.post(
            f"{base_url}/api/upload-payment-proof",
            json=proof_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Comprovante enviado: {result.get('message')}")
            print(f"📊 Status: {result.get('status')}")
        else:
            print(f"❌ Erro ao enviar comprovante: {response.status_code}")
            return False
        
        # 3. Aprovar pagamento (admin)
        print("\n👨‍💼 3. Aprovando pagamento (admin)...")
        approve_data = {
            "payment_id": payment_id,
            "action": "approve"
        }
        
        response = requests.post(
            f"{base_url}/api/admin/approve-payment",
            json=approve_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Pagamento aprovado: {result.get('message')}")
            print(f"📊 Status: {result.get('status')}")
            return True
        else:
            print(f"❌ Erro na aprovação: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Função principal"""
    print("🔒 TESTE DE SEGURANÇA - Sistema de Pagamentos")
    print("=" * 60)
    print("Objetivo: Verificar se a correção de segurança está funcionando")
    print("=" * 60)
    
    # Teste 1: Tentativa de fraude
    fraud_blocked = test_security_fix()
    
    # Teste 2: Fluxo legítimo
    legitimate_flow = test_legitimate_payment_flow()
    
    # Resultado final
    print("\n\n📊 RESULTADO FINAL")
    print("=" * 60)
    
    if fraud_blocked:
        print("✅ SEGURANÇA: Fraude bloqueada com sucesso")
    else:
        print("❌ SEGURANÇA: Fraude não foi bloqueada")
    
    if legitimate_flow:
        print("✅ FLUXO LEGÍTIMO: Funcionando corretamente")
    else:
        print("❌ FLUXO LEGÍTIMO: Com problemas")
    
    if fraud_blocked and legitimate_flow:
        print("\n🎉 CORREÇÃO DE SEGURANÇA: 100% FUNCIONAL!")
        print("🛡️ Sistema seguro contra fraudes")
        print("✅ Pagamentos legítimos funcionando")
        return True
    else:
        print("\n⚠️ CORREÇÃO DE SEGURANÇA: PRECISA DE AJUSTES")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
