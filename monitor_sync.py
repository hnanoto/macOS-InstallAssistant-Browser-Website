#!/usr/bin/env python3
"""
Monitor de sincronização do painel de aprovação com servidor Render
"""

import requests
import json
import time
import os
from datetime import datetime

class RenderSyncMonitor:
    def __init__(self, base_url="https://payment-api-b6th.onrender.com"):
        self.base_url = base_url
        self.timeout = 30  # Aumentar timeout para Render
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RenderSyncMonitor/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
    
    def test_endpoint(self, endpoint, name):
        """Testa um endpoint específico"""
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"🔍 Testando {name}...")
            print(f"   URL: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                print(f"✅ {name}: OK (Status: {response.status_code})")
                return True, response.json() if 'application/json' in response.headers.get('content-type', '') else response.text
            else:
                print(f"❌ {name}: Falhou (Status: {response.status_code})")
                return False, None
                
        except requests.exceptions.Timeout:
            print(f"⏰ {name}: Timeout (>{self.timeout}s)")
            return False, None
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 {name}: Erro de conexão - {e}")
            return False, None
        except Exception as e:
            print(f"❌ {name}: Erro - {e}")
            return False, None
    
    def monitor_sync(self):
        """Monitora a sincronização completa"""
        print("🚀 Iniciando monitor de sincronização do painel de aprovação...")
        print(f"🌐 Servidor: {self.base_url}")
        print(f"⏱️ Timeout: {self.timeout}s")
        print("=" * 80)
        
        # Lista de endpoints para testar
        endpoints = [
            ("/health", "Health Check"),
            ("/api/sync-status", "Status de Sincronização"),
            ("/admin/portal", "Painel Admin"),
            ("/api/admin/payments", "API de Pagamentos"),
            ("/api/admin/notifications", "Notificações Admin"),
            ("/api/admin/pending-payments", "Pagamentos Pendentes")
        ]
        
        results = {}
        
        for endpoint, name in endpoints:
            success, data = self.test_endpoint(endpoint, name)
            results[endpoint] = {
                'success': success,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            print("-" * 60)
            time.sleep(1)  # Pausa entre testes
        
        # Resumo dos resultados
        print("📊 RESUMO DOS TESTES:")
        print("=" * 80)
        
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        
        print(f"✅ Sucessos: {successful}/{total}")
        print(f"❌ Falhas: {total - successful}/{total}")
        print(f"📈 Taxa de sucesso: {(successful/total)*100:.1f}%")
        
        # Status geral
        if successful == total:
            print("🎉 SINCRONIZAÇÃO: PERFEITA!")
        elif successful >= total * 0.8:
            print("⚠️ SINCRONIZAÇÃO: PARCIAL (alguns problemas)")
        else:
            print("🚨 SINCRONIZAÇÃO: CRÍTICA (muitos problemas)")
        
        print(f"⏰ Monitor concluído em: {datetime.now().isoformat()}")
        
        return results

def main():
    """Função principal"""
    monitor = RenderSyncMonitor()
    results = monitor.monitor_sync()
    
    # Salvar resultados em arquivo
    try:
        with open('sync_monitor_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("💾 Resultados salvos em: sync_monitor_results.json")
    except Exception as e:
        print(f"⚠️ Erro ao salvar resultados: {e}")

if __name__ == "__main__":
    main()
