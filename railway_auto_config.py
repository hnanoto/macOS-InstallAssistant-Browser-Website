#!/usr/bin/env python3
"""
Script para configurar automaticamente as variáveis de ambiente no Railway
"""

import requests
import json
import os

def configure_railway_variables():
    """Configure Railway environment variables automatically"""
    
    # Railway API configuration
    RAILWAY_TOKEN = os.getenv('RAILWAY_TOKEN')
    PROJECT_ID = os.getenv('RAILWAY_PROJECT_ID')
    
    if not RAILWAY_TOKEN or not PROJECT_ID:
        print("❌ RAILWAY_TOKEN e RAILWAY_PROJECT_ID não configurados")
        print("Configure estas variáveis de ambiente primeiro:")
        print("export RAILWAY_TOKEN=seu_token_aqui")
        print("export RAILWAY_PROJECT_ID=seu_project_id_aqui")
        return False
    
    # Variables to set
    variables = {
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': 'hackintoshandbeyond@gmail.com',
        'SMTP_PASSWORD': 'your_app_password_here',  # User needs to update this
        'FROM_EMAIL': 'hackintoshandbeyond@gmail.com',
        'RAILWAY_ENVIRONMENT': 'production'
    }
    
    headers = {
        'Authorization': f'Bearer {RAILWAY_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    for key, value in variables.items():
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
    configure_railway_variables()
