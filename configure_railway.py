#!/usr/bin/env python3
"""
Script para configurar automaticamente as variáveis de ambiente no Railway
"""

import os
import requests
import json

def configure_railway_smtp():
    """Configure SMTP variables on Railway"""
    
    # Railway API configuration
    RAILWAY_TOKEN = os.getenv('RAILWAY_TOKEN')
    PROJECT_ID = os.getenv('RAILWAY_PROJECT_ID')
    
    if not RAILWAY_TOKEN or not PROJECT_ID:
        print("❌ RAILWAY_TOKEN e RAILWAY_PROJECT_ID não configurados")
        print("Configure estas variáveis de ambiente primeiro:")
        print("export RAILWAY_TOKEN=seu_token_aqui")
        print("export RAILWAY_PROJECT_ID=seu_project_id_aqui")
        return False
    
    # SMTP Configuration with your App Password
    smtp_config = {
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'hackintoshandbeyond@gmail.com',
        'SMTP_PASSWORD': 'sua_chave_app_aqui',  # Replace with actual App Password
        'FROM_EMAIL': 'hackintoshandbeyond@gmail.com',
        'RAILWAY_ENVIRONMENT': 'production'
    }
    
    headers = {
        'Authorization': f'Bearer {RAILWAY_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    print("🔧 Configurando variáveis SMTP no Railway...")
    
    for key, value in smtp_config.items():
        try:
            url = f'https://backboard.railway.app/graphql/v1'
            query = {
                'query': '''
                mutation SetVariable($projectId: String!, $name: String!, $value: String!) {
                    projectUpdateVariable(projectId: $projectId, name: $name, value: $value) {
                        id
                    }
                }
                ''',
                'variables': {
                    'projectId': PROJECT_ID,
                    'name': key,
                    'value': value
                }
            }
            
            response = requests.post(url, headers=headers, json=query)
            
            if response.status_code == 200:
                print(f"✅ {key} configurado com sucesso")
            else:
                print(f"❌ Erro ao configurar {key}: {response.text}")
                
        except Exception as e:
            print(f"❌ Erro ao configurar {key}: {e}")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Acesse o painel do Railway")
    print("2. Vá em Variables")
    print("3. Atualize SMTP_PASSWORD com sua senha de aplicativo Gmail")
    print("4. Teste o envio de emails")
    
    return True

if __name__ == '__main__':
    configure_railway_smtp()
