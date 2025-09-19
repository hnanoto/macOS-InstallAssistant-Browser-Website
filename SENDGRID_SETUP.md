# 🚀 CONFIGURAÇÃO RÁPIDA: SendGrid para Railway

## ⚡ SOLUÇÃO RÁPIDA (5 minutos)

O Gmail está sendo bloqueado pelo Railway. Vamos usar SendGrid que funciona perfeitamente!

### 1. Criar conta SendGrid (GRATUITO)
1. Acesse: https://sendgrid.com/
2. Clique em "Start for Free"
3. Crie conta com seu email
4. Confirme o email

### 2. Gerar API Key
1. No painel SendGrid, vá em **Settings** → **API Keys**
2. Clique em **Create API Key**
3. Nome: "macOS InstallAssistant Browser"
4. Permissions: **Full Access**
5. **COPIE a API Key** (começa com SG.)

### 3. Configurar no Railway
1. Acesse seu projeto no Railway
2. Vá em **Variables**
3. Adicione estas variáveis:

```
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SUA_API_KEY_AQUI
FROM_EMAIL=hackintoshandbeyond@gmail.com
```

### 4. Testar
Após configurar, teste:
```bash
curl -X POST https://web-production-1513a.up.railway.app/api/debug/test-email \
  -H "Content-Type: application/json" \
  -d '{"email":"hackintoshandbeyond@gmail.com"}'
```

## ✅ VANTAGENS DO SENDGRID
- ✅ Funciona perfeitamente no Railway
- ✅ 100 emails/dia GRATUITOS
- ✅ Mais rápido que Gmail
- ✅ Melhor deliverability
- ✅ Sem bloqueios de firewall

## 🔧 CONFIGURAÇÃO ATUAL
O código já está configurado para SendGrid por padrão!
