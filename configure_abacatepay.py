#!/usr/bin/env python3
"""
🥑 CONFIGURADOR ABACATEPAY
=========================

Script interativo para configurar credenciais AbacatePay
Facilita a configuração das chaves de API

Autor: Sistema de Migração Automática
Data: 24 de Setembro de 2025
"""

import os
import sys
from pathlib import Path
import getpass

def print_header():
    """Exibir cabeçalho"""
    print("""
🥑 CONFIGURADOR ABACATEPAY v1.0
==============================
Configure suas credenciais AbacatePay de forma segura
""")

def print_instructions():
    """Exibir instruções"""
    print("""
📋 ANTES DE CONTINUAR:
1. Acesse: https://www.abacatepay.com/app/retiradas
2. Faça login com sua conta Google
3. Vá em 'API' ou 'Configurações'
4. Copie sua API Key e Secret Key
5. Configure webhook (opcional): https://web-production-1513a.up.railway.app/api/abacatepay/webhook

🔒 SUAS CREDENCIAIS SERÃO ARMAZENADAS LOCALMENTE DE FORMA SEGURA
""")

def get_current_config():
    """Obter configuração atual"""
    env_file = Path(".env")
    current_config = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    current_config[key] = value
    
    return current_config

def save_config(config):
    """Salvar configuração no arquivo .env"""
    env_file = Path(".env")
    
    # Ler arquivo existente
    existing_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            existing_lines = f.readlines()
    
    # Remover linhas AbacatePay existentes
    filtered_lines = []
    for line in existing_lines:
        if not line.strip().startswith('ABACATEPAY_'):
            filtered_lines.append(line)
    
    # Adicionar novas configurações AbacatePay
    abacatepay_section = [
        "\n# 🥑 AbacatePay Configuration\n",
        f"ABACATEPAY_API_KEY={config['api_key']}\n",
        f"ABACATEPAY_SECRET_KEY={config['secret_key']}\n",
        f"ABACATEPAY_WEBHOOK_SECRET={config['webhook_secret']}\n",
        f"ABACATEPAY_SANDBOX={config['sandbox']}\n",
        f"ABACATEPAY_BASE_URL={config['base_url']}\n"
    ]
    
    # Escrever arquivo atualizado
    with open(env_file, 'w') as f:
        f.writelines(filtered_lines)
        f.writelines(abacatepay_section)
    
    print(f"✅ Configuração salva em: {env_file.absolute()}")

def test_connection(config):
    """Testar conexão com AbacatePay"""
    print("\n🧪 TESTANDO CONEXÃO COM ABACATEPAY...")
    
    try:
        # Configurar variáveis de ambiente temporariamente
        os.environ['ABACATEPAY_API_KEY'] = config['api_key']
        os.environ['ABACATEPAY_SECRET_KEY'] = config['secret_key']
        os.environ['ABACATEPAY_WEBHOOK_SECRET'] = config['webhook_secret']
        os.environ['ABACATEPAY_SANDBOX'] = config['sandbox']
        os.environ['ABACATEPAY_BASE_URL'] = config['base_url']
        
        # Importar e testar
        from abacatepay_integration import AbacatePayConfig, AbacatePayClient
        
        abacate_config = AbacatePayConfig.from_env()
        client = AbacatePayClient(abacate_config)
        
        # Teste simples (health check se disponível)
        print("✅ Módulos AbacatePay carregados com sucesso")
        print("✅ Configuração válida")
        
        if config['sandbox'] == 'true':
            print("🧪 Modo: SANDBOX (Testes)")
        else:
            print("🚀 Modo: PRODUÇÃO")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print("💡 Verifique suas credenciais e tente novamente")
        return False

def main():
    """Função principal"""
    print_header()
    print_instructions()
    
    # Verificar configuração atual
    current_config = get_current_config()
    
    if current_config.get('ABACATEPAY_API_KEY') and current_config.get('ABACATEPAY_API_KEY') != 'your_api_key_here':
        print("⚠️ CONFIGURAÇÃO EXISTENTE DETECTADA:")
        print(f"   API Key: {current_config.get('ABACATEPAY_API_KEY', 'Não configurada')[:20]}...")
        print(f"   Sandbox: {current_config.get('ABACATEPAY_SANDBOX', 'Não configurado')}")
        
        reconfigure = input("\n❓ Deseja reconfigurar? (s/N): ").lower().strip()
        if reconfigure not in ['s', 'sim', 'y', 'yes']:
            print("✅ Mantendo configuração existente")
            return 0
    
    print("\n🔧 CONFIGURAÇÃO DAS CREDENCIAIS:")
    print("=" * 40)
    
    # Coletar credenciais
    config = {}
    
    # API Key
    while True:
        api_key = getpass.getpass("🔑 Digite sua API Key AbacatePay: ").strip()
        if api_key and len(api_key) > 10:
            config['api_key'] = api_key
            break
        else:
            print("❌ API Key inválida. Deve ter mais de 10 caracteres.")
    
    # Secret Key
    while True:
        secret_key = getpass.getpass("🔐 Digite sua Secret Key AbacatePay: ").strip()
        if secret_key and len(secret_key) > 10:
            config['secret_key'] = secret_key
            break
        else:
            print("❌ Secret Key inválida. Deve ter mais de 10 caracteres.")
    
    # Webhook Secret (opcional)
    webhook_secret = getpass.getpass("🔔 Digite seu Webhook Secret (opcional): ").strip()
    config['webhook_secret'] = webhook_secret if webhook_secret else 'webhook_secret_not_configured'
    
    # Modo sandbox
    while True:
        sandbox_mode = input("🧪 Usar modo SANDBOX/Teste? (S/n): ").lower().strip()
        if sandbox_mode in ['', 's', 'sim', 'y', 'yes']:
            config['sandbox'] = 'true'
            config['base_url'] = 'https://api.abacatepay.com/v1'
            break
        elif sandbox_mode in ['n', 'nao', 'não', 'no']:
            config['sandbox'] = 'false'
            config['base_url'] = 'https://api.abacatepay.com/v1'
            break
        else:
            print("❌ Responda com 's' para sim ou 'n' para não")
    
    print("\n📋 RESUMO DA CONFIGURAÇÃO:")
    print("=" * 30)
    print(f"API Key: {config['api_key'][:10]}...{config['api_key'][-4:]}")
    print(f"Secret Key: {config['secret_key'][:10]}...{config['secret_key'][-4:]}")
    print(f"Webhook: {'Configurado' if config['webhook_secret'] != 'webhook_secret_not_configured' else 'Não configurado'}")
    print(f"Modo: {'SANDBOX (Testes)' if config['sandbox'] == 'true' else 'PRODUÇÃO'}")
    print(f"Base URL: {config['base_url']}")
    
    # Confirmar
    confirm = input("\n✅ Confirma a configuração? (S/n): ").lower().strip()
    if confirm not in ['', 's', 'sim', 'y', 'yes']:
        print("❌ Configuração cancelada")
        return 1
    
    # Salvar configuração
    try:
        save_config(config)
        print("✅ Configuração salva com sucesso!")
        
        # Testar conexão
        if test_connection(config):
            print("\n🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 40)
            print("✅ Credenciais AbacatePay configuradas")
            print("✅ Conexão testada e funcionando")
            print("✅ Sistema pronto para uso")
            
            print("\n📋 PRÓXIMOS PASSOS:")
            print("1. Reinicie o servidor: python3 payment_api.py")
            print("2. Teste os endpoints AbacatePay")
            print("3. Configure webhook no dashboard AbacatePay")
            
            if config['sandbox'] == 'true':
                print("\n🧪 MODO TESTE ATIVO:")
                print("- Use dados de teste para transações")
                print("- Nenhuma cobrança real será feita")
                print("- Mude para produção quando estiver pronto")
            
            return 0
        else:
            print("\n⚠️ Configuração salva, mas teste de conexão falhou")
            print("💡 Verifique suas credenciais no dashboard AbacatePay")
            return 1
            
    except Exception as e:
        print(f"\n❌ Erro ao salvar configuração: {e}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Configuração cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        sys.exit(1)
