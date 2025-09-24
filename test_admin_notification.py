#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para verificar notificações de administrador
Quando um comprovante é enviado pelo usuário
"""

import requests
import json
import os
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:5001"

def test_admin_notification():
    print("🧪 TESTE DE NOTIFICAÇÃO ADMIN")
    print("=" * 50)
    
    try:
        # 1. Criar um pagamento PIX de teste
        print("\n📝 1. Criando pagamento PIX de teste...")
        
        pix_data = {
            'amount': 2500,  # R$ 25,00
            'currency': 'BRL',
            'email': 'cliente.teste@gmail.com',
            'name': 'Cliente Teste Admin',
            'country': 'BR',
            'customer_email': 'cliente.teste@gmail.com',
            'customer_name': 'Cliente Teste Admin',
            'description': 'Teste de notificação admin'
        }
        
        pix_response = requests.post(f"{BASE_URL}/api/create-pix-payment", json=pix_data)
        
        if pix_response.status_code != 200:
            print(f"❌ Erro ao criar pagamento PIX: {pix_response.status_code}")
            print(f"📄 Resposta: {pix_response.text}")
            return False
        
        pix_result = pix_response.json()
        payment_id = pix_result['payment_id']
        print(f"✅ Pagamento PIX criado: {payment_id}")
        
        # 2. Simular upload de comprovante
        print("\n📤 2. Enviando comprovante de teste...")
        
        # Usar uma imagem existente
        image_path = "/Users/henrique/Desktop/Backup-Matrix/Captura de Tela 2025-09-20 às 10.44.28.png"
        
        if not os.path.exists(image_path):
            print(f"❌ Imagem de teste não encontrada: {image_path}")
            return False
        
        print(f"📷 Usando imagem: {os.path.basename(image_path)}")
        
        # Preparar dados para upload
        upload_data = {
            'payment_id': payment_id,
            'email': 'cliente.teste@gmail.com'
        }
        
        with open(image_path, 'rb') as f:
            files = {
                'file': (os.path.basename(image_path), f.read(), 'image/png')
            }
            
            upload_response = requests.post(
                f"{BASE_URL}/api/upload-payment-proof",
                data=upload_data,
                files=files
            )
        
        print(f"📊 Status do upload: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            print("✅ Comprovante enviado com sucesso!")
            print(f"📄 Resposta: {json.dumps(upload_result, indent=2, ensure_ascii=False)}")
            
            print("\n📧 VERIFICAÇÃO IMPORTANTE:")
            print("=" * 40)
            print("🔍 Verifique o e-mail: hackintoshandbeyond@gmail.com")
            print("📬 Deve ter chegado uma notificação com:")
            print(f"   • Assunto: 🔔 Comprovante PIX Enviado - Aguardando Aprovação - {payment_id}")
            print(f"   • Cliente: Cliente Teste Admin (cliente.teste@gmail.com)")
            print(f"   • Arquivo: {os.path.basename(image_path)}")
            print(f"   • Valor: R$ 25,00")
            print("\n📱 Se não chegou, verifique:")
            print("   • Pasta de spam/lixo eletrônico")
            print("   • Configuração SMTP no servidor")
            print("   • Logs do servidor para erros")
            
            return True
        else:
            print(f"❌ Erro no upload: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def check_server_status():
    """Verificar se o servidor está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor está rodando")
            return True
        else:
            print(f"❌ Servidor retornou status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao servidor")
        print("🔧 Certifique-se de que o servidor está rodando em http://localhost:5001")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar servidor: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTE DE NOTIFICAÇÃO ADMIN - COMPROVANTE PIX")
    print("=" * 60)
    
    # Verificar se servidor está rodando
    if not check_server_status():
        print("\n🔧 Inicie o servidor primeiro:")
        print("cd '/Users/henrique/Desktop/Backup-Matrix/Layout-NOVO-Processo/Andamento-Projeto -Cursor/website/api'")
        print("python3 payment_api.py")
        exit(1)
    
    # Executar teste
    success = test_admin_notification()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("📧 Verifique o e-mail hackintoshandbeyond@gmail.com")
    else:
        print("❌ TESTE FALHOU")
        print("🔧 Verifique os logs do servidor para mais detalhes")