#!/usr/bin/env python3
"""
Script para testar o sistema após a correção do Railway
"""

import requests
import json
import time

def test_complete_system():
    """Testa o sistema completo após a correção"""
    
    print("🚀 TESTE COMPLETO APÓS CORREÇÃO DO RAILWAY")
    print("=" * 50)
    
    base_url = "https://web-production-1513a.up.railway.app"
    
    # Teste 1: Verificar se a API correta está rodando
    print("\n1. Verificando se a API completa está rodando...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ API está respondendo")
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    # Teste 2: Verificar se os endpoints de pagamento existem
    print("\n2. Verificando endpoints de pagamento...")
    try:
        # Tentar criar um pagamento
        payment_data = {
            "amount": 100.00,
            "currency": "BRL",
            "payment_method": "pix",
            "customer_email": "hackintoshandbeyond@gmail.com",
            "customer_name": "Teste Pós-Correção"
        }
        
        response = requests.post(
            f"{base_url}/api/payments",
            json=payment_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 201:
            payment = response.json()
            payment_id = payment.get('id')
            print(f"✅ Pagamento criado: {payment_id}")
            
            # Teste 3: Upload de comprovante
            print(f"\n3. Testando upload para pagamento {payment_id}...")
            
            # Criar arquivo de teste
            test_content = f"Comprovante teste pós-correção - {payment_id}".encode()
            
            files = {
                'file': ('comprovante_pos_correcao.txt', test_content, 'text/plain')
            }
            
            upload_response = requests.post(
                f"{base_url}/api/payments/{payment_id}/upload-proof",
                files=files,
                timeout=30
            )
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                print("✅ Upload realizado com sucesso!")
                print(f"   Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # Verificar se a notificação foi enviada
                if result.get('notification_sent'):
                    print("✅ Notificação enviada com sucesso!")
                    print("   Verifique sua caixa de entrada em alguns minutos.")
                    return True
                else:
                    print("❌ Notificação NÃO foi enviada")
                    print("   O problema ainda persiste.")
                    return False
                
            else:
                print(f"❌ Erro no upload: {upload_response.status_code}")
                print(f"   Resposta: {upload_response.text}")
                return False
                
        else:
            print(f"❌ Erro ao criar pagamento: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def check_email_configuration():
    """Verifica se a configuração de email está correta"""
    
    print("\n4. Verificando configuração de email...")
    
    # Tentar acessar endpoint de debug se existir
    try:
        response = requests.get(f"{base_url}/api/debug/email-status", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print("✅ Configuração de email:")
            print(f"   {json.dumps(config, indent=2, ensure_ascii=False)}")
        else:
            print("   Endpoint de debug não disponível")
    except:
        print("   Endpoint de debug não disponível")
    
    print("\n📋 Verificações manuais necessárias:")
    print("1. Acesse o painel do Railway")
    print("2. Verifique se as variáveis estão corretas:")
    print("   - RESEND_API_KEY=re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1")
    print("   - USE_RESEND=true")
    print("   - EMAIL_PROVIDER=resend")
    print("   - SMTP_ENABLED=false")
    print("   - USE_SENDGRID=false")
    print("3. Verifique se as variáveis SMTP foram removidas")
    print("4. Verifique os logs do Railway para erros")

if __name__ == "__main__":
    print("🔧 TESTE APÓS CORREÇÃO DO RAILWAY")
    print("Execute este script após:")
    print("1. Corrigir o railway-variables.json")
    print("2. Remover variáveis SMTP do Railway")
    print("3. Configurar apenas variáveis Resend")
    print("4. Fazer redeploy completo")
    print("=" * 50)
    
    success = test_complete_system()
    check_email_configuration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCESSO! Sistema funcionando corretamente!")
        print("   - API completa rodando")
        print("   - Upload funcionando")
        print("   - Email sendo enviado via Resend")
    else:
        print("❌ PROBLEMA PERSISTE!")
        print("   Verifique se todas as correções foram aplicadas:")
        print("   1. railway-variables.json corrigido")
        print("   2. Variáveis SMTP removidas")
        print("   3. Redeploy realizado")
        print("   4. Logs do Railway verificados")



