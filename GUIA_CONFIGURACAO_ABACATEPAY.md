# 🥑 GUIA DE CONFIGURAÇÃO ABACATEPAY

## 🎯 Como Obter suas Credenciais AbacatePay

### Passo 1: Acessar o Dashboard
1. Acesse: **https://www.abacatepay.com/app/retiradas**
2. Faça login com sua conta Google
3. Complete o cadastro se necessário

### Passo 2: Obter API Key
1. No dashboard, procure por **"API"** ou **"Configurações"**
2. Clique em **"Criar Nova Chave"** ou **"Generate API Key"**
3. Copie sua **API Key** (começará com algo como `ak_live_...` ou `ak_test_...`)
4. Copie sua **Secret Key** (começará com algo como `sk_live_...` ou `sk_test_...`)

### Passo 3: Configurar Webhook (Opcional)
1. Configure a URL do webhook: `https://web-production-1513a.up.railway.app/api/abacatepay/webhook`
2. Copie o **Webhook Secret** se fornecido

## ⚙️ Configurar no Sistema

### Método 1: Via Arquivo .env (Recomendado)
```bash
# Abra o arquivo .env na pasta da API
cd /Users/henrique/Desktop/Backup-Matrix/Layout-NOVO-Processo/Andamento-Projeto\ -Cursor/website/api/

# Edite o arquivo .env e substitua:
ABACATEPAY_API_KEY=sua_api_key_real_aqui
ABACATEPAY_SECRET_KEY=sua_secret_key_real_aqui
ABACATEPAY_WEBHOOK_SECRET=sua_webhook_secret_aqui

# Para produção:
ABACATEPAY_SANDBOX=false

# Para testes:
ABACATEPAY_SANDBOX=true
```

### Método 2: Via Variáveis de Ambiente
```bash
export ABACATEPAY_API_KEY="sua_api_key_aqui"
export ABACATEPAY_SECRET_KEY="sua_secret_key_aqui"
export ABACATEPAY_WEBHOOK_SECRET="sua_webhook_secret_aqui"
```

## 🧪 Testar a Configuração

### 1. Verificar Health Check
```bash
curl http://localhost:5001/api/abacatepay/health
```

### 2. Criar Pagamento de Teste
```bash
curl -X POST http://localhost:5001/api/abacatepay/create-pix-payment \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@exemplo.com",
    "name": "Teste AbacatePay",
    "amount": 26.50
  }'
```

## 🔒 Segurança

### ⚠️ IMPORTANTE:
- **NUNCA** compartilhe suas chaves de API publicamente
- **NUNCA** faça commit das chaves no Git
- Use **sandbox/test** para desenvolvimento
- Use **production/live** apenas em produção

### 🛡️ Boas Práticas:
- Mantenha as chaves em arquivo `.env` (já está no .gitignore)
- Use variáveis de ambiente no Railway/produção
- Monitore o uso das chaves no dashboard AbacatePay
- Regenere as chaves se necessário

## 🚀 Deploy em Produção

### Railway/Produção:
1. No painel do Railway, vá em **Variables**
2. Adicione as variáveis:
   - `ABACATEPAY_API_KEY`
   - `ABACATEPAY_SECRET_KEY`
   - `ABACATEPAY_WEBHOOK_SECRET`
   - `ABACATEPAY_SANDBOX=false`

## 📊 Monitoramento

### Dashboard AbacatePay:
- Monitore transações em tempo real
- Verifique webhooks recebidos
- Acompanhe estatísticas de pagamento

### Logs do Sistema:
```bash
# Ver logs do servidor
tail -f server.log

# Ver logs específicos AbacatePay
grep "AbacatePay" server.log
```

## 🆘 Problemas Comuns

### ❌ "API Key inválida"
- Verifique se copiou a chave completa
- Confirme se está usando a chave correta (test/live)
- Regenere a chave se necessário

### ❌ "Webhook não funciona"
- Verifique se a URL está correta
- Confirme se o webhook secret está configurado
- Teste a conectividade da URL

### ❌ "Pagamento não processa"
- Verifique se está no modo correto (sandbox/production)
- Confirme se a conta está ativa
- Verifique logs de erro

## 📞 Suporte

- **Documentação AbacatePay:** https://abacatepay.readme.io/
- **Suporte Técnico:** Através do dashboard AbacatePay
- **Logs do Sistema:** Verifique sempre os logs para diagnosticar problemas

---

## ✅ Checklist de Configuração

- [ ] Conta AbacatePay criada
- [ ] API Key obtida
- [ ] Secret Key obtida
- [ ] Webhook configurado (opcional)
- [ ] Credenciais configuradas no .env
- [ ] Health check funcionando
- [ ] Pagamento teste criado
- [ ] Deploy em produção configurado

**🎉 Quando todos os itens estiverem marcados, sua integração AbacatePay estará completa!**
