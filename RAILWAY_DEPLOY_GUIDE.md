# 🚀 Guia de Deploy no Railway

## 📋 **Pré-requisitos**
- Conta no GitHub
- Conta no Railway (gratuita)
- Gmail com App Password configurado

## 🎯 **Passo 1: Preparar o Repositório**

### 1.1 Criar repositório no GitHub
```bash
# No terminal, na pasta do projeto
cd "/Users/henrique/Desktop/Backup-Matrix/Layout-NOVO-Processo/Andamento-Projeto -Cursor/website/api"

# Inicializar git (se não existir)
git init

# Adicionar arquivos
git add .

# Commit inicial
git commit -m "Initial commit - Payment API ready for Railway"

# Conectar ao GitHub (criar repositório primeiro no GitHub)
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git

# Push inicial
git push -u origin main
```

## 🚀 **Passo 2: Deploy no Railway**

### 2.1 Acessar Railway
1. Vá para [railway.app](https://railway.app)
2. Clique em "Login" e faça login com GitHub
3. Clique em "New Project"

### 2.2 Conectar Repositório
1. Selecione "Deploy from GitHub repo"
2. Escolha seu repositório
3. Railway detectará automaticamente que é Python

### 2.3 Configurar Variáveis de Ambiente
No dashboard do Railway, vá em "Variables" e adicione:

```env
# Email Configuration (OBRIGATÓRIO)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=hackintoshandbeyond@gmail.com
SMTP_PASSWORD=seu_app_password_aqui
FROM_EMAIL=hackintoshandbeyond@gmail.com

# Flask Configuration
PORT=5001
DEBUG=False

# URLs (substitua YOUR_APP_NAME pelo nome do seu app)
ALLOWED_ORIGINS=https://YOUR_APP_NAME.railway.app,http://localhost:8000
SUCCESS_URL=https://YOUR_APP_NAME.railway.app/success
CANCEL_URL=https://YOUR_APP_NAME.railway.app/cancel
WEBHOOK_URL=https://YOUR_APP_NAME.railway.app/api/webhook
```

### 2.4 Deploy Automático
- Railway fará o deploy automaticamente
- Aguarde alguns minutos
- Você receberá uma URL como: `https://seu-app.railway.app`

## 🔧 **Passo 3: Testar o Deploy**

### 3.1 Teste de Saúde
```bash
curl https://seu-app.railway.app/api/health
```

### 3.2 Teste de Processo de Compra
```bash
curl -X POST https://seu-app.railway.app/api/swift/process-purchase \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@exemplo.com","method":"pix","name":"Teste"}'
```

## 📱 **Passo 4: Atualizar App Swift**

### 4.1 Modificar NetworkManager.swift
```swift
// Substituir localhost pela URL do Railway
private let baseURL = "https://seu-app.railway.app"
```

### 4.2 Recompilar e Criar DMG
```bash
# Executar o script de build
./create_dmg.command
```

### 4.3 Atualizar Release no GitHub
1. Vá para o repositório do website
2. Crie um novo release
3. Faça upload do novo DMG

## 🎉 **Resultado Final**

✅ **API pública funcionando**
✅ **App Swift conectando na API pública**
✅ **PIX funcionando para todos os usuários**
✅ **PayPal funcionando para todos os usuários**
✅ **Emails sendo enviados corretamente**

## 🔍 **Troubleshooting**

### Problema: Deploy falha
- Verifique se todas as variáveis de ambiente estão configuradas
- Verifique os logs no Railway dashboard

### Problema: Email não funciona
- Verifique se o App Password do Gmail está correto
- Teste o SMTP localmente primeiro

### Problema: App Swift não conecta
- Verifique se a URL está correta no NetworkManager.swift
- Teste a API manualmente com curl

## 📞 **Suporte**

Se tiver problemas:
1. Verifique os logs no Railway dashboard
2. Teste cada endpoint individualmente
3. Verifique as variáveis de ambiente

---

**🎯 Próximos passos após o deploy:**
1. ✅ Testar PIX com usuário real
2. ✅ Testar PayPal com usuário real  
3. ✅ Verificar emails sendo enviados
4. ✅ Atualizar release no GitHub
