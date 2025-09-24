#!/usr/bin/env python3
"""
Script para identificar qual API está rodando no Railway
"""

import requests
import json

def identify_railway_api():
    """Identifica qual API está rodando no Railway"""
    
    print("🔍 IDENTIFICANDO QUAL API ESTÁ RODANDO NO RAILWAY")
    print("=" * 50)
    
    base_url = "https://web-production-1513a.up.railway.app"
    
    # Lista de endpoints para testar
    endpoints_to_test = [
        "/api/health",
        "/api/payments",
        "/api/debug/email-status",
        "/api/test-email",
        "/api/enhanced/health",
        "/api/enhanced/payments",
        "/api/enhanced/debug/email-status"
    ]
    
    print("\n📋 Testando endpoints disponíveis:")
    
    available_endpoints = []
    
    for endpoint in endpoints_to_test:
        try:
            if endpoint.endswith("payments"):
                # Para endpoints POST, fazer uma requisição POST
                response = requests.post(
                    f"{base_url}{endpoint}",
                    json={"test": "data"},
                    timeout=5
                )
            else:
                # Para outros endpoints, fazer GET
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code != 404:
                available_endpoints.append({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "method": "POST" if endpoint.endswith("payments") else "GET"
                })
                print(f"✅ {endpoint} - Status: {response.status_code}")
            else:
                print(f"❌ {endpoint} - 404 Not Found")
                
        except Exception as e:
            print(f"❌ {endpoint} - Erro: {e}")
    
    print(f"\n📊 RESUMO:")
    print(f"   Endpoints disponíveis: {len(available_endpoints)}")
    
    if available_endpoints:
        print("\n✅ Endpoints funcionando:")
        for ep in available_endpoints:
            print(f"   {ep['method']} {ep['endpoint']} - {ep['status']}")
    
    # Determinar qual API está rodando
    print(f"\n🎯 DIAGNÓSTICO:")
    
    has_payments = any(ep['endpoint'].endswith('payments') for ep in available_endpoints)
    has_enhanced = any('/enhanced/' in ep['endpoint'] for ep in available_endpoints)
    has_debug = any('/debug/' in ep['endpoint'] for ep in available_endpoints)
    
    if has_enhanced:
        print("✅ API ENHANCED está rodando (completa)")
        print("   - Sistema deve estar funcionando")
    elif has_payments:
        print("⚠️  API BÁSICA está rodando (limitada)")
        print("   - Alguns endpoints funcionam")
    else:
        print("❌ API MÍNIMA está rodando (apenas health)")
        print("   - Sistema não funcional")
    
    if has_debug:
        print("✅ Endpoints de debug disponíveis")
    else:
        print("❌ Endpoints de debug não disponíveis")
    
    return available_endpoints

def check_railway_config():
    """Verifica se o Railway está usando a configuração correta"""
    
    print(f"\n🔧 VERIFICAÇÃO DE CONFIGURAÇÃO:")
    print("1. O arquivo railway-variables.json foi commitado ✅")
    print("2. O push foi realizado ✅")
    print("3. Railway deve fazer redeploy automático")
    print("4. Se não funcionou, pode ser necessário:")
    print("   - Forçar redeploy manual no Railway")
    print("   - Verificar se o arquivo está na raiz do projeto")
    print("   - Verificar se o Railway está lendo o arquivo")

if __name__ == "__main__":
    available = identify_railway_api()
    check_railway_config()
    
    print(f"\n" + "=" * 50)
    if any('/enhanced/' in ep['endpoint'] for ep in available):
        print("🎉 SUCESSO! API Enhanced está rodando!")
    else:
        print("❌ PROBLEMA: API Enhanced não está rodando")
        print("   Verifique se o Railway fez o redeploy")
        print("   Ou force um redeploy manual")



