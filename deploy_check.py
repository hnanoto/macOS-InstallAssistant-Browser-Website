#!/usr/bin/env python3
"""
Script para verificar e preparar deploy do painel de aprovação
"""

import os
import json
import subprocess
from datetime import datetime

def check_deploy_status():
    """Verifica o status do deploy"""
    print("🔍 Verificando status do deploy...")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    current_dir = os.getcwd()
    print(f"📁 Diretório atual: {current_dir}")
    
    # Verificar arquivos importantes
    important_files = [
        'payment_api.py',
        'requirements.txt',
        'admin_portal.html'
    ]
    
    print("\n📋 Verificando arquivos importantes:")
    for file in important_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} - AUSENTE!")
    
    # Verificar configurações do Render
    print("\n⚙️ Verificando configurações do Render:")
    render_yaml_path = "../../render.yaml"
    if os.path.exists(render_yaml_path):
        print("✅ render.yaml encontrado")
        with open(render_yaml_path, 'r') as f:
            content = f.read()
            if 'payment-api-b6th.onrender.com' in content:
                print("✅ URLs do Render configuradas")
            else:
                print("⚠️ URLs do Render podem estar desatualizadas")
    else:
        print("❌ render.yaml não encontrado")
    
    # Verificar dependências
    print("\n📦 Verificando dependências:")
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            deps = f.read().strip().split('\n')
            print(f"✅ {len(deps)} dependências encontradas")
            for dep in deps:
                if dep.strip():
                    print(f"   - {dep}")
    
    print("\n🚀 Próximos passos para deploy:")
    print("1. Fazer commit das alterações no Git")
    print("2. Push para o repositório")
    print("3. O Render fará deploy automático")
    print("4. Verificar logs do Render para confirmar deploy")
    
    return True

def create_deploy_instructions():
    """Cria instruções de deploy"""
    instructions = """
# 🚀 Instruções de Deploy - Painel de Aprovação

## Problemas Identificados e Corrigidos:

### ✅ Correções Implementadas:
1. **URLs Hardcoded**: Substituídas por variáveis de ambiente
2. **CORS**: Configuração mais robusta adicionada
3. **Logs de Debug**: Sistema de monitoramento implementado
4. **Health Check**: Endpoints de monitoramento criados
5. **Configurações Render**: render.yaml atualizado

### 🔧 Arquivos Modificados:
- `payment_api.py` - URLs dinâmicas e logs de debug
- `render.yaml` - URLs corretas do servidor
- `test_sync.py` - Script de teste criado
- `monitor_sync.py` - Monitor de sincronização

### 📋 Próximos Passos:

1. **Commit das Alterações:**
   ```bash
   git add .
   git commit -m "Fix: Sincronização do painel de aprovação com Render"
   git push origin main
   ```

2. **Verificar Deploy no Render:**
   - Acessar dashboard do Render
   - Verificar logs de deploy
   - Aguardar conclusão do build

3. **Testar Sincronização:**
   ```bash
   python3 monitor_sync.py
   ```

4. **Verificar Endpoints:**
   - `/health` - Status do servidor
   - `/api/sync-status` - Status de sincronização
   - `/admin/portal` - Painel administrativo

### 🎯 Resultado Esperado:
- Taxa de sucesso: 100%
- Painel admin sincronizado
- URLs dinâmicas funcionando
- Logs de debug ativos

### 📞 Em caso de problemas:
1. Verificar logs do Render
2. Executar `monitor_sync.py` para diagnóstico
3. Verificar variáveis de ambiente no Render
"""
    
    with open('DEPLOY_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("📝 Instruções de deploy criadas em: DEPLOY_INSTRUCTIONS.md")

def main():
    """Função principal"""
    print("🔧 Verificador de Deploy - Painel de Aprovação")
    print("=" * 60)
    
    check_deploy_status()
    create_deploy_instructions()
    
    print("\n✅ Verificação concluída!")
    print("📋 Consulte DEPLOY_INSTRUCTIONS.md para próximos passos")

if __name__ == "__main__":
    main()
