#!/usr/bin/env python3
"""
Script para corrigir automaticamente a configuração do Railway
Configura todas as variáveis de ambiente necessárias
"""

import requests
import json
import os
from datetime import datetime

def create_railway_config_file():
    """Cria arquivo de configuração para o Railway"""
    print("📝 Criando arquivo de configuração do Railway...")
    
    config = {
        "variables": {
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587", 
            "SMTP_USERNAME": "hackintoshandbeyond@gmail.com",
            "SMTP_PASSWORD": "pvqd jzvt sjyz azwn",
            "FROM_EMAIL": "hackintoshandbeyond@gmail.com",
            "EMAIL_FROM": "hackintoshandbeyond@gmail.com",
            "EMAIL_TO_DEFAULT": "hackintoshandbeyond@gmail.com",
            "REPLY_TO_DEFAULT": "hackintoshandbeyond@gmail.com",
            "RESEND_API_KEY": "re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1",
            "RAILWAY_ENVIRONMENT": "production",
            "APP_BASE_URL": "https://web-production-1513a.up.railway.app",
            "STORAGE_URL_BASE": "https://web-production-1513a.up.railway.app/uploads",
            "DEBUG": "false",
            "PYTHON_VERSION": "3.11.7"
        },
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python payment_api.py",
            "healthcheckPath": "/api/health",
            "healthcheckTimeout": 100,
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    # Salvar configuração
    with open('railway_config_complete.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuração salva em: railway_config_complete.json")
    
    return config

def create_railway_env_file():
    """Cria arquivo .env para o Railway"""
    print("📝 Criando arquivo .env para Railway...")
    
    env_content = """# Railway Environment Variables
# Copy these to your Railway project variables

# Email Configuration (REQUIRED)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=hackintoshandbeyond@gmail.com
SMTP_PASSWORD=pvqd jzvt sjyz azwn
FROM_EMAIL=hackintoshandbeyond@gmail.com
EMAIL_FROM=hackintoshandbeyond@gmail.com
EMAIL_TO_DEFAULT=hackintoshandbeyond@gmail.com
REPLY_TO_DEFAULT=hackintoshandbeyond@gmail.com

# Email Providers (BACKUP)
RESEND_API_KEY=re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1

# Railway Configuration
RAILWAY_ENVIRONMENT=production
APP_BASE_URL=https://web-production-1513a.up.railway.app
STORAGE_URL_BASE=https://web-production-1513a.up.railway.app/uploads
DEBUG=false

# Python Configuration
PYTHON_VERSION=3.11.7
"""
    
    with open('railway.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Arquivo .env salvo em: railway.env")

def create_railway_cli_commands():
    """Cria comandos CLI para configurar o Railway"""
    print("📝 Criando comandos CLI do Railway...")
    
    commands = """#!/bin/bash
# Comandos para configurar o Railway via CLI
# Execute estes comandos no terminal após instalar o Railway CLI

echo "🚀 Configurando variáveis do Railway..."

# Instalar Railway CLI (se não estiver instalado)
# npm install -g @railway/cli

# Login no Railway
railway login

# Conectar ao projeto (substitua pelo ID do seu projeto)
# railway link

# Configurar variáveis de ambiente
railway variables set SMTP_SERVER=smtp.gmail.com
railway variables set SMTP_PORT=587
railway variables set SMTP_USERNAME=hackintoshandbeyond@gmail.com
railway variables set SMTP_PASSWORD="pvqd jzvt sjyz azwn"
railway variables set FROM_EMAIL=hackintoshandbeyond@gmail.com
railway variables set EMAIL_FROM=hackintoshandbeyond@gmail.com
railway variables set EMAIL_TO_DEFAULT=hackintoshandbeyond@gmail.com
railway variables set REPLY_TO_DEFAULT=hackintoshandbeyond@gmail.com
railway variables set RESEND_API_KEY=re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1
railway variables set RAILWAY_ENVIRONMENT=production
railway variables set APP_BASE_URL=https://web-production-1513a.up.railway.app
railway variables set STORAGE_URL_BASE=https://web-production-1513a.up.railway.app/uploads
railway variables set DEBUG=false
railway variables set PYTHON_VERSION=3.11.7

echo "✅ Variáveis configuradas!"
echo "🔄 Fazendo redeploy..."

# Redeploy
railway up

echo "🎉 Configuração completa!"
"""
    
    with open('configure_railway.sh', 'w') as f:
        f.write(commands)
    
    # Tornar executável
    os.chmod('configure_railway.sh', 0o755)
    
    print("✅ Script CLI salvo em: configure_railway.sh")

def create_manual_instructions():
    """Cria instruções manuais detalhadas"""
    print("📝 Criando instruções manuais...")
    
    instructions = """# 🔧 INSTRUÇÕES PARA CORRIGIR O RAILWAY

## 🚨 PROBLEMA IDENTIFICADO
O sistema de emails não está funcionando no Railway porque as variáveis de ambiente não estão configuradas.

## ✅ SOLUÇÃO PASSO A PASSO

### 1. ACESSE O PAINEL DO RAILWAY
- Vá para: https://railway.app
- Faça login com sua conta GitHub
- Selecione seu projeto: web-production-1513a

### 2. CONFIGURE AS VARIÁVEIS DE AMBIENTE
Clique em "Variables" no painel lateral e adicione TODAS estas variáveis:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=hackintoshandbeyond@gmail.com
SMTP_PASSWORD=pvqd jzvt sjyz azwn
FROM_EMAIL=hackintoshandbeyond@gmail.com
EMAIL_FROM=hackintoshandbeyond@gmail.com
EMAIL_TO_DEFAULT=hackintoshandbeyond@gmail.com
REPLY_TO_DEFAULT=hackintoshandbeyond@gmail.com
RESEND_API_KEY=re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1
RAILWAY_ENVIRONMENT=production
APP_BASE_URL=https://web-production-1513a.up.railway.app
STORAGE_URL_BASE=https://web-production-1513a.up.railway.app/uploads
DEBUG=false
PYTHON_VERSION=3.11.7
```

### 3. REDEPLOY O PROJETO
- Após adicionar todas as variáveis, clique em "Deploy"
- Aguarde o deploy terminar (2-5 minutos)
- Verifique se não há erros nos logs

### 4. TESTE O SISTEMA
Execute este comando para testar:
```bash
python3 test_railway_production.py
```

### 5. MONITORE OS LOGS
- Vá em "Deployments" > "View Logs"
- Procure por mensagens como:
  - "✅ Email enviado com sucesso"
  - "📧 Conectando ao servidor SMTP"
  - "✅ Configuração SMTP validada"

## 🎯 RESULTADO ESPERADO
Após a configuração, você deve ver:
- ✅ Health Check
- ✅ Configuração SMTP  
- ✅ Resend API
- ✅ Envio de Email
- ✅ Upload de Comprovante
- ✅ Painel Admin
- ✅ Pagamentos Pendentes

## 🚨 SE AINDA HOUVER PROBLEMAS

### Problema: SMTP não conecta
**Solução:** Verifique se a senha do Gmail está correta

### Problema: Resend falha
**Solução:** Verifique se a API key do Resend está válida

### Problema: Upload falha
**Solução:** Verifique se a pasta uploads existe e tem permissões

## 📞 SUPORTE
Se ainda houver problemas:
1. Verifique os logs do Railway
2. Execute o teste de produção
3. Confirme se todas as variáveis estão configuradas
"""
    
    with open('RAILWAY_FIX_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    print("✅ Instruções salvas em: RAILWAY_FIX_INSTRUCTIONS.md")

def test_current_config():
    """Testa a configuração atual do Railway"""
    print("🧪 Testando configuração atual do Railway...")
    
    try:
        response = requests.get("https://web-production-1513a.up.railway.app/api/debug/smtp", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📧 Status SMTP: {data}")
            
            if data.get('configured'):
                print("✅ SMTP já está configurado!")
                return True
            else:
                print("❌ SMTP não está configurado")
                return False
        else:
            print(f"❌ Erro na verificação: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")
        return False

def main():
    """Função principal"""
    print("🔧 CORREÇÃO AUTOMÁTICA DO RAILWAY")
    print("=" * 50)
    
    # Testar configuração atual
    current_ok = test_current_config()
    
    if current_ok:
        print("\n🎉 O Railway já está configurado corretamente!")
        print("   Execute o teste completo para verificar:")
        print("   python3 test_railway_production.py")
        return
    
    print("\n📝 Gerando arquivos de correção...")
    
    # Criar arquivos de configuração
    create_railway_config_file()
    create_railway_env_file()
    create_railway_cli_commands()
    create_manual_instructions()
    
    print("\n" + "=" * 50)
    print("📋 ARQUIVOS CRIADOS:")
    print("=" * 50)
    print("✅ railway_config_complete.json - Configuração completa")
    print("✅ railway.env - Variáveis de ambiente")
    print("✅ configure_railway.sh - Script CLI")
    print("✅ RAILWAY_FIX_INSTRUCTIONS.md - Instruções manuais")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Acesse https://railway.app")
    print("2. Vá para Variables no seu projeto")
    print("3. Adicione todas as variáveis do arquivo railway.env")
    print("4. Clique em Deploy para redeploy")
    print("5. Execute: python3 test_railway_production.py")
    
    print("\n📖 Para instruções detalhadas, leia:")
    print("   RAILWAY_FIX_INSTRUCTIONS.md")

if __name__ == "__main__":
    main()