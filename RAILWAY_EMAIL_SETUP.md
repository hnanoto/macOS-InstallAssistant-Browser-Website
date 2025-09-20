# 🚀 Configuração de E-mail no Railway

## 📧 Problema Identificado

O ChatGPT5 identificou corretamente que o problema está no backend hospedado no Railway. Os comprovantes enviados pela página web não chegam no e-mail `hackintoshandbeyond@gmail.com` porque:

1. **Configuração SMTP incorreta** - A senha estava hardcoded no código
2. **Variáveis de ambiente não configuradas** no Railway
3. **Falta de logs detalhados** para debug

## ✅ Correções Implementadas

### 1. Configuração SMTP Corrigida
- ✅ Removida senha hardcoded do código
- ✅ Adicionada validação de configuração de e-mail
- ✅ Melhorado tratamento de erros SMTP
- ✅ Adicionados logs detalhados para debug

### 2. Variáveis de Ambiente Necessárias

Configure estas variáveis no Railway Dashboard:

```bash
# Email Configuration (OBRIGATÓRIO)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=hackintoshandbeyond@gmail.com
SMTP_PASSWORD=pvqd jzvt sjyz azwn
FROM_EMAIL=hackintoshandbeyond@gmail.com

# Railway Detection
RAILWAY_ENVIRONMENT=production
```

### 3. Como Configurar no Railway

1. **Acesse o Railway Dashboard**
2. **Vá para seu projeto**
3. **Clique em "Variables"**
4. **Adicione as variáveis acima**

## 🧪 Endpoints de Teste

### Testar Configuração SMTP
```bash
curl -X GET https://web-production-1513a.up.railway.app/api/debug/smtp
```

### Testar Envio de E-mail
```bash
curl -X POST https://web-production-1513a.up.railway.app/api/debug/test-email \
  -H "Content-Type: application/json" \
  -d '{"email": "hackintoshandbeyond@gmail.com"}'
```

### Testar E-mail de Comprovante
```bash
curl -X POST https://web-production-1513a.up.railway.app/api/debug/test-proof-email \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "pix_test_123",
    "email": "test@example.com",
    "name": "Cliente Teste",
    "filename": "comprovante.png"
  }'
```

## 🔍 Verificação de Logs

Após configurar as variáveis, verifique os logs do Railway:

1. **Acesse o Railway Dashboard**
2. **Vá para "Deployments"**
3. **Clique no deployment mais recente**
4. **Vá para "Logs"**
5. **Procure por mensagens como:**
   - `📤 Conectando ao servidor SMTP`
   - `✅ Email enviado com sucesso`
   - `❌ Erro de autenticação SMTP`

## 🚨 Troubleshooting

### Erro de Autenticação
```
❌ Erro de autenticação SMTP: (535, '5.7.8 Username and Password not accepted')
```
**Solução:** Verifique se a senha do Gmail App Password está correta

### Erro de Conexão
```
❌ Erro de conexão SMTP: [Errno 11001] getaddrinfo failed
```
**Solução:** Verifique se o servidor SMTP está correto

### E-mail não chega
1. Verifique a pasta de spam
2. Confirme se o Gmail App Password está ativo
3. Verifique se a autenticação de 2 fatores está habilitada

## 📋 Fluxo de E-mail Corrigido

### 1. Upload de Comprovante
- ✅ Usuário envia comprovante via página web
- ✅ Backend salva arquivo e atualiza status
- ✅ **E-mail é enviado automaticamente para admin**

### 2. Aprovação Manual
- ✅ Admin acessa painel e aprova pagamento
- ✅ **E-mail é enviado automaticamente para cliente**
- ✅ **Notificação é enviada para admin**

### 3. Confirmação de Pagamento
- ✅ App Swift confirma pagamento
- ✅ **E-mail é enviado automaticamente para cliente**

## 🎯 Próximos Passos

1. **Configure as variáveis de ambiente no Railway**
2. **Teste os endpoints de debug**
3. **Verifique os logs do Railway**
4. **Teste o fluxo completo de upload de comprovante**

## 📞 Suporte

Se ainda houver problemas:
1. Verifique os logs do Railway
2. Teste os endpoints de debug
3. Confirme se as variáveis estão configuradas corretamente
