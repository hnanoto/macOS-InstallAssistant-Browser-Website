# 🔧 INSTRUÇÕES PARA CORRIGIR O RAILWAY

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
