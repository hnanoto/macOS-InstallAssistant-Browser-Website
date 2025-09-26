#!/usr/bin/env python3
"""
Script de teste para verificar sincronização do painel de aprovação com servidor Render
"""

import requests
import json
import os
from datetime import datetime

def test_render_sync():
    """Testa a sincronização com o servidor Render"""
    
    # URL base do servidor
    base_url = "https://payment-api-b6th.onrender.com"
    
    print("🔍 Testando sincronização do painel de aprovação com servidor Render...")
    print(f"🌐 URL Base: {base_url}")
    print("-" * 60)
    
    # Teste 1: Health Check
    print("1️⃣ Testando Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health Check: OK")
            print(f"   Status: {data.get('status')}")
            print(f"   App Base URL: {data.get('app_base_url')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            print(f"   Payments Count: {data.get('payments_count')}")
        else:
            print(f"❌ Health Check: Falhou (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Health Check: Erro de conexão - {e}")
    
    print("-" * 60)
    
    # Teste 2: Sync Status
    print("2️⃣ Testando Status de Sincronização...")
    try:
        response = requests.get(f"{base_url}/api/sync-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Sync Status: OK")
            print(f"   Sync Status: {data.get('sync_status')}")
            print(f"   App Base URL: {data.get('app_base_url')}")
            print(f"   Render Environment: {data.get('render_environment')}")
        else:
            print(f"❌ Sync Status: Falhou (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Sync Status: Erro de conexão - {e}")
    
    print("-" * 60)
    
    # Teste 3: Admin Portal
    print("3️⃣ Testando Acesso ao Painel Admin...")
    try:
        response = requests.get(f"{base_url}/admin/portal", timeout=10)
        if response.status_code == 200:
            print("✅ Painel Admin: Acessível")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content Length: {len(response.content)} bytes")
        else:
            print(f"❌ Painel Admin: Falhou (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Painel Admin: Erro de conexão - {e}")
    
    print("-" * 60)
    
    # Teste 4: API de Pagamentos
    print("4️⃣ Testando API de Pagamentos...")
    try:
        response = requests.get(f"{base_url}/api/admin/payments", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API de Pagamentos: OK")
            print(f"   Success: {data.get('success')}")
            print(f"   Count: {data.get('count')}")
        else:
            print(f"❌ API de Pagamentos: Falhou (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ API de Pagamentos: Erro de conexão - {e}")
    
    print("-" * 60)
    
    # Teste 5: Notificações Admin
    print("5️⃣ Testando Notificações Admin...")
    try:
        response = requests.get(f"{base_url}/api/admin/notifications", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Notificações Admin: OK")
            print(f"   Notifications Count: {len(data.get('notifications', []))}")
        else:
            print(f"❌ Notificações Admin: Falhou (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Notificações Admin: Erro de conexão - {e}")
    
    print("-" * 60)
    print("🏁 Teste de sincronização concluído!")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")

if __name__ == "__main__":
    test_render_sync()
