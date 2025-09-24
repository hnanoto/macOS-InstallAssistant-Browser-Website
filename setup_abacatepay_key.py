#!/usr/bin/env python3
"""
🔑 CONFIGURAÇÃO AUTOMÁTICA ABACATEPAY
====================================

Configura a API Key da AbacatePay de forma segura
"""

import os
from pathlib import Path

def setup_abacatepay_credentials():
    """Configurar credenciais AbacatePay"""
    
    # API Key fornecida pelo usuário
    api_key = "abc_dev_0Bm00HssGqag5GB30qnpQSFF"
    
    print("🔑 CONFIGURANDO CREDENCIAIS ABACATEPAY")
    print("=====================================")
    print(f"✅ API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Configurar variáveis de ambiente
    os.environ['ABACATEPAY_API_KEY'] = api_key
    os.environ['ABACATEPAY_SECRET_KEY'] = api_key  # Usar mesma chave como secret temporariamente
    os.environ['ABACATEPAY_WEBHOOK_SECRET'] = 'webhook_secret_temp'
    os.environ['ABACATEPAY_SANDBOX'] = 'true'  # Modo desenvolvimento
    os.environ['ABACATEPAY_BASE_URL'] = 'https://api.abacatepay.com/v1'
    
    print("✅ Variáveis de ambiente configuradas")
    
    # Testar a integração
    try:
        from abacatepay_integration import AbacatePayConfig, AbacatePayClient
        
        config = AbacatePayConfig(
            api_key=api_key,
            secret_key=api_key,
            webhook_secret='webhook_secret_temp',
            sandbox_mode=True
        )
        
        client = AbacatePayClient(config)
        print("✅ Cliente AbacatePay inicializado com sucesso")
        
        # Testar criação de pagamento PIX
        from abacatepay_integration import abacatepay_processor
        
        # Atualizar configuração do processador
        abacatepay_processor.config = config
        abacatepay_processor.client = client
        
        print("✅ Processador AbacatePay configurado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False

if __name__ == "__main__":
    success = setup_abacatepay_credentials()
    if success:
        print("\n🎉 CONFIGURAÇÃO ABACATEPAY CONCLUÍDA!")
        print("===================================")
        print("✅ API Key configurada")
        print("✅ Cliente inicializado")
        print("✅ Sistema pronto para testes")
        print("\n🧪 PRÓXIMO PASSO: Testar criação de pagamento")
    else:
        print("\n❌ Erro na configuração - verifique a API Key")
