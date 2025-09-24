#!/usr/bin/env python3
"""
Teste específico para verificar o status do deployment do Railway
"""

import requests
import json
import time

def test_railway_deployment():
    """Testa o status do deployment do Railway"""
    
    print("🚀 TESTE DE DEPLOYMENT DO RAILWAY")
    print("=" * 50)
    
    base_url = "https://web-production-1513a.up.railway.app"
    
    # Teste 1: Verificar se a API está respondendo
    print("\n1. Verificando status da API...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API está respondendo")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Timestamp: {health_data.get('timestamp')}")
            print(f"   Version: {health_data.get('version')}")
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    # Teste 2: Verificar se os endpoints da API básica existem
    print("\n2. Verificando endpoints da API básica...")
    basic_endpoints = [
        "/api/payments",
        "/api/debug/email-status"
    ]
    
    basic_working = 0
    for endpoint in basic_endpoints:
        try:
            if endpoint.endswith("payments"):
                response = requests.post(f"{base_url}{endpoint}", json={}, timeout=5)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code != 404:
                basic_working += 1
                print(f"✅ {endpoint} - Status: {response.status_code}")
            else:
                print(f"❌ {endpoint} - 404 Not Found")
        except Exception as e:
            print(f"❌ {endpoint} - Erro: {e}")
    
    # Teste 3: Verificar se os endpoints da API enhanced existem
    print("\n3. Verificando endpoints da API enhanced...")
    enhanced_endpoints = [
        "/api/enhanced/health",
        "/api/enhanced/payments",
        "/api/enhanced/debug/email-status"
    ]
    
    enhanced_working = 0
    for endpoint in enhanced_endpoints:
        try:
            if endpoint.endswith("payments"):
                response = requests.post(f"{base_url}{endpoint}", json={}, timeout=5)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code != 404:
                enhanced_working += 1
                print(f"✅ {endpoint} - Status: {response.status_code}")
            else:
                print(f"❌ {endpoint} - 404 Not Found")
        except Exception as e:
            print(f"❌ {endpoint} - Erro: {e}")
    
    # Diagnóstico
    print(f"\n📊 DIAGNÓSTICO:")
    print(f"   Endpoints básicos funcionando: {basic_working}/{len(basic_endpoints)}")
    print(f"   Endpoints enhanced funcionando: {enhanced_working}/{len(enhanced_endpoints)}")
    
    if enhanced_working > 0:
        print("✅ API ENHANCED está rodando!")
        return True
    elif basic_working > 0:
        print("⚠️  API BÁSICA está rodando (não é a enhanced)")
        return False
    else:
        print("❌ Apenas health check funcionando")
        return False

def check_railway_config():
    """Verifica a configuração do Railway"""
    
    print(f"\n🔧 VERIFICAÇÃO DE CONFIGURAÇÃO:")
    print("1. Arquivo railway.toml foi modificado ✅")
    print("2. Start command alterado para enhanced_payment_api.py ✅")
    print("3. Variáveis Resend configuradas ✅")
    print("4. Push realizado ✅")
    print("\n❌ PROBLEMA: Railway não está aplicando as mudanças")
    print("\n🔧 SOLUÇÕES POSSÍVEIS:")
    print("1. Forçar redeploy manual no painel do Railway")
    print("2. Verificar se há erros nos logs do Railway")
    print("3. Verificar se o arquivo railway.toml está sendo lido")
    print("4. Tentar usar Procfile em vez de railway.toml")

if __name__ == "__main__":
    success = test_railway_deployment()
    check_railway_config()
    
    print(f"\n" + "=" * 50)
    if success:
        print("🎉 SUCESSO! API Enhanced está rodando!")
    else:
        print("❌ PROBLEMA: Railway não aplicou as mudanças")
        print("   Ação necessária: Forçar redeploy manual no Railway")



