# 📧 Guia de Configuração SMTP - Gmail

## ✅ Status da Implementação

- ✅ **Código SMTP implementado** - Fallback funcional após Resend
- ✅ **Configuração .env preparada** - Variáveis corretas
- ✅ **Teste direto criado** - `test_smtp_direct.py`
- ⚠️ **Senha de aplicativo** - Precisa ser configurada

## 🔧 Como Configurar a Senha de Aplicativo do Gmail

### Passo 1: Ativar Autenticação de 2 Fatores
1. Acesse [myaccount.google.com](https://myaccount.google.com)
2. Vá em **Segurança**
3. Ative a **Verificação em duas etapas**

### Passo 2: Gerar Senha de Aplicativo
1. Ainda em **Segurança**, procure por **Senhas de app**
2. Clique em **Senhas de app**
3. Selecione **Aplicativo**: Outro (nome personalizado)
4. Digite: `macOS InstallAssistant API`
5. Clique em **Gerar**
6. **COPIE** a senha de 16 caracteres (sem espaços)

### Passo 3: Atualizar o .env
```bash
# Substitua 'your_app_password_here' pela senha gerada
SMTP_PASSWORD=abcdabcdabcdabcd
```

### Passo 4: Testar a Configuração
```bash
python3 test_smtp_direct.py
```

## 🔍 Diagnóstico de Problemas

### Erro: "Username and Password not accepted"
- ✅ Verifique se a autenticação de 2 fatores está ativada
- ✅ Gere uma nova senha de aplicativo
- ✅ Certifique-se de que não há espaços na senha
- ✅ Use a senha de aplicativo, não a senha normal do Gmail

### Erro: "Less secure app access"
- ✅ Use senha de aplicativo (mais seguro)
- ❌ Não ative "Acesso de app menos seguro"

## 📋 Fluxo de E-mail Implementado

1. **Resend** (Primeiro) - Para domínio verificado
2. **SMTP Gmail** (Fallback) - Para qualquer e-mail
3. **Sistema Gratuito** (Final) - Salva em notifications.json

## 🧪 Testes Disponíveis

### Teste Direto SMTP
```bash
python3 test_smtp_direct.py
```

### Teste via API
```bash
curl -X POST https://payment-api-test.loca.lt/api/send-serial-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@gmail.com",
    "name": "Cliente Teste",
    "serial": "TEST-SERIAL-123",
    "product_name": "macOS InstallAssistant Browser",
    "payment_id": "test_payment_123",
    "transactionId": "txn_test_123"
  }'
```

### Verificar Configuração
```bash
curl -X GET https://payment-api-test.loca.lt/api/debug/smtp
```

## 🔐 Segurança

- ✅ Arquivo `.env` não é commitado no Git
- ✅ Senha de aplicativo é mais segura que senha normal
- ✅ Conexão TLS/SSL ativada
- ✅ Validação de credenciais antes do envio

## 📝 Próximos Passos

1. **Configure a senha de aplicativo** seguindo os passos acima
2. **Teste o SMTP** com `python3 test_smtp_direct.py`
3. **Teste a API** com o curl acima
4. **Verifique os logs** do servidor para confirmar o envio

---

**⚠️ IMPORTANTE**: Mantenha a senha de aplicativo segura e não a compartilhe!