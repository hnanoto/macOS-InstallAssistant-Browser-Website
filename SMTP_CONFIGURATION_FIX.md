# 🔧 CORREÇÃO: Configuração SMTP para Envio de Emails

## 🚨 PROBLEMA IDENTIFICADO

O sistema não está enviando emails com os seriais porque a configuração SMTP não está correta.

**Arquivo problemático**: `/website/api/.env`
**Linha problemática**: `SMTP_PASSWORD=your_app_password_here`

## ✅ SOLUÇÃO

### 1. Configurar Senha de Aplicativo do Gmail

1. **Acesse sua conta Gmail** (hackintoshandbeyond@gmail.com)
2. **Vá para Configurações de Segurança**:
   - Acesse: https://myaccount.google.com/security
   - Procure por "Senhas de aplicativo" ou "App passwords"
3. **Gere uma nova senha de aplicativo**:
   - Selecione "Mail" como aplicativo
   - Selecione "Outro" como dispositivo
   - Digite "macOS InstallAssistant Browser" como nome
   - Copie a senha gerada (16 caracteres)

### 2. Atualizar o arquivo .env

Edite o arquivo `/website/api/.env` e substitua:

```bash
# ANTES (incorreto):
SMTP_PASSWORD=your_app_password_here

# DEPOIS (correto):
SMTP_PASSWORD=sua_senha_de_aplicativo_de_16_caracteres
```

### 3. Verificar Configuração

Execute o teste SMTP para verificar se está funcionando:

```bash
cd "/Users/henrique/Desktop/Backup-Matrix/Layout-NOVO-Processo/Andamento-Projeto -Cursor/website/api"
python3 test_smtp.py
```

### 4. Reiniciar o Servidor

Após configurar, reinicie o servidor de pagamentos:

```bash
cd "/Users/henrique/Desktop/Backup-Matrix/Layout-NOVO-Processo/Andamento-Projeto -Cursor/website/api"
python3 payment_api.py
```

## 🔍 COMO VERIFICAR SE ESTÁ FUNCIONANDO

### Teste Manual:
1. Faça uma compra de teste
2. Verifique os logs do servidor
3. Procure por mensagens como:
   - ✅ "Email enviado com sucesso para: [email]"
   - ❌ "Erro ao enviar email"

### Logs Esperados (funcionando):
```
🔄 Tentando enviar email para: usuario@email.com
📧 SMTP Config: smtp.gmail.com:587, User: hackintoshandbeyond@gmail.com
📤 Conectando ao servidor SMTP...
🔐 Fazendo login com: hackintoshandbeyond@gmail.com
📨 Enviando email para: usuario@email.com
✅ Email enviado com sucesso para: usuario@email.com
```

### Logs Atuais (não funcionando):
```
🔄 Tentando enviar email para: usuario@email.com
⚠️ SMTP não configurado (senha placeholder), simulando envio de email...
📧 EMAIL SIMULADO PARA: usuario@email.com
✅ Email simulado enviado com sucesso!
```

## 🛡️ SEGURANÇA

- **NUNCA** use sua senha normal do Gmail
- **SEMPRE** use senhas de aplicativo para SMTP
- **MANTENHA** o arquivo `.env` seguro e não o compartilhe
- **CONSIDERE** usar variáveis de ambiente do sistema em produção

## 📧 CONTEÚDO DO EMAIL

Quando configurado corretamente, o email enviado incluirá:

- ✅ Serial de ativação formatado (XXXX-XXXX-XXXX)
- ✅ Instruções de ativação
- ✅ Link para download do aplicativo
- ✅ Detalhes da transação
- ✅ Design HTML profissional

## 🚀 PRÓXIMOS PASSOS

1. Configure a senha de aplicativo do Gmail
2. Atualize o arquivo .env
3. Teste a configuração SMTP
4. Reinicie o servidor
5. Teste uma compra completa
6. Verifique se o email chega na caixa de entrada

---

**Status**: 🔴 PROBLEMA IDENTIFICADO - Aguardando configuração SMTP
**Prioridade**: 🚨 ALTA - Usuários não estão recebendo seriais
**Solução**: ⚙️ Configuração de senha de aplicativo Gmail
