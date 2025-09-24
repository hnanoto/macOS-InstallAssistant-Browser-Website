# 🔐 Informações de Acesso - Payment API Tunnel

## 🌐 URL do Tunnel
**URL Principal:** https://payment-api-test.loca.lt

## 🔑 Credenciais de Acesso

### Senha do Tunnel
**Senha:** `131.100.202.230`
- Esta é a senha baseada no IP público da máquina
- Válida por 7 dias para este IP
- Necessária apenas no primeiro acesso via navegador

### Bypass para APIs
Para requisições programáticas (curl, APIs, webhooks):
```bash
# Adicione o header bypass-tunnel-reminder
curl -H "bypass-tunnel-reminder: true" https://payment-api-test.loca.lt/api/health
```

## ✅ Verificação de Status

### Health Check
```bash
curl -H "bypass-tunnel-reminder: true" https://payment-api-test.loca.lt/api/health
```

**Resposta Esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-20T20:52:22.489483",
  "version": "1.0.0"
}
```

### Teste de SMTP
```bash
curl -H "bypass-tunnel-reminder: true" https://payment-api-test.loca.lt/api/debug/smtp
```

### Envio de E-mail
```bash
curl -X POST https://payment-api-test.loca.lt/api/send-serial-email \
  -H "Content-Type: application/json" \
  -H "bypass-tunnel-reminder: true" \
  -d '{
    "email": "teste@gmail.com",
    "name": "Cliente Teste",
    "serial": "TEST-SERIAL-123",
    "product_name": "macOS InstallAssistant Browser",
    "payment_id": "test_payment_123",
    "transactionId": "txn_test_123"
  }'
```

## 🔧 Configuração de Segurança

### Headers Recomendados
- `bypass-tunnel-reminder: true` - Para APIs e webhooks
- `Content-Type: application/json` - Para requisições POST

### Renovação da Senha
A senha do tunnel é renovada automaticamente:
- **Frequência:** A cada 7 dias
- **Baseada em:** IP público da máquina
- **Comando para obter nova senha:** `curl https://loca.lt/mytunnelpassword`

## 📋 Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|----------|
| `/api/health` | GET | Status do servidor |
| `/api/debug/smtp` | GET | Configuração SMTP |
| `/api/send-serial-email` | POST | Envio de e-mail |
| `/api/process-payment` | POST | Processar pagamento |
| `/api/upload-payment-proof` | POST | Upload de comprovante |
| `/admin` | GET | Painel administrativo |

## 🚨 Notas de Segurança

- ✅ Tunnel protegido por senha baseada em IP
- ✅ Headers de bypass para automação
- ✅ HTTPS obrigatório
- ⚠️ Senha válida por 7 dias apenas
- ⚠️ Acesso limitado ao IP público atual

## 🔄 Renovação Automática

Para obter a senha atual a qualquer momento:
```bash
curl https://loca.lt/mytunnelpassword
```

---

**Última atualização:** 20/09/2025 20:52  
**IP Atual:** 131.100.202.230  
**Status:** ✅ Ativo e funcionando