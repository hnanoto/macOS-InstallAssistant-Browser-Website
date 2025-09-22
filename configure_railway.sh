#!/bin/bash
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
