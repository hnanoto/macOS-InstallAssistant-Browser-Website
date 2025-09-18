#!/bin/bash

# 🚀 Script para Deploy no Railway
# Execute este script para preparar o projeto para o Railway

echo "🚀 Preparando projeto para deploy no Railway..."

# Verificar se estamos na pasta correta
if [ ! -f "payment_api.py" ]; then
    echo "❌ Erro: Execute este script na pasta que contém payment_api.py"
    exit 1
fi

# Verificar se git está inicializado
if [ ! -d ".git" ]; then
    echo "📦 Inicializando repositório Git..."
    git init
    echo "✅ Git inicializado"
fi

# Adicionar arquivos necessários
echo "📁 Adicionando arquivos ao Git..."
git add .

# Verificar se há mudanças para commit
if git diff --staged --quiet; then
    echo "ℹ️ Nenhuma mudança para commit"
else
    echo "💾 Fazendo commit das mudanças..."
    git commit -m "Deploy para Railway - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "✅ Commit realizado"
fi

# Verificar se remote origin existe
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "🔗 Configure o remote origin primeiro:"
    echo "   git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git"
    echo ""
    echo "📋 Próximos passos:"
    echo "1. Crie um repositório no GitHub"
    echo "2. Execute: git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git"
    echo "3. Execute: git push -u origin main"
    echo "4. Vá para railway.app e conecte o repositório"
    echo "5. Configure as variáveis de ambiente no Railway"
    exit 0
fi

# Push para o repositório
echo "⬆️ Enviando para o GitHub..."
git push origin main

echo ""
echo "🎉 Projeto preparado para Railway!"
echo ""
echo "📋 Próximos passos:"
echo "1. Vá para https://railway.app"
echo "2. Faça login com GitHub"
echo "3. Clique em 'New Project'"
echo "4. Selecione 'Deploy from GitHub repo'"
echo "5. Escolha seu repositório"
echo "6. Configure as variáveis de ambiente (veja railway.env.example)"
echo "7. Aguarde o deploy automático"
echo ""
echo "🔧 Variáveis obrigatórias no Railway:"
echo "   SMTP_USERNAME=hackintoshandbeyond@gmail.com"
echo "   SMTP_PASSWORD=seu_app_password_aqui"
echo "   FROM_EMAIL=hackintoshandbeyond@gmail.com"
echo ""
echo "📖 Para mais detalhes, veja: RAILWAY_DEPLOY_GUIDE.md"
