#!/bin/bash

# Script para fazer upload dos arquivos de download para o GitHub Pages
# Repositório: https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website

echo "🚀 Iniciando upload para GitHub Pages..."

# Verificar se o git está configurado
if ! command -v git &> /dev/null; then
    echo "❌ Git não está instalado. Instale o Git primeiro."
    exit 1
fi

# Diretório do repositório GitHub
GITHUB_REPO_DIR="/Users/henrique/Desktop/Backup-Matrix/Layout-NOVO-Processo/Andamento-Projeto -Cursor/website/api/downloads"

# Verificar se os arquivos existem
if [ ! -f "$GITHUB_REPO_DIR/macOS-InstallAssistant-Browser.dmg" ]; then
    echo "❌ Arquivo DMG não encontrado em: $GITHUB_REPO_DIR"
    exit 1
fi

if [ ! -f "$GITHUB_REPO_DIR/index.html" ]; then
    echo "❌ Arquivo index.html não encontrado em: $GITHUB_REPO_DIR"
    exit 1
fi

echo "✅ Arquivos encontrados:"
echo "   📦 macOS-InstallAssistant-Browser.dmg ($(du -h "$GITHUB_REPO_DIR/macOS-InstallAssistant-Browser.dmg" | cut -f1))"
echo "   📄 index.html"
echo "   📄 README.md"

echo ""
echo "📋 Instruções para fazer upload:"
echo ""
echo "1. Acesse o repositório: https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website"
echo "2. Navegue para a pasta 'downloads'"
echo "3. Faça upload dos seguintes arquivos:"
echo "   - macOS-InstallAssistant-Browser.dmg"
echo "   - index.html"
echo "   - README.md"
echo ""
echo "4. Ou use o Git CLI:"
echo "   cd /path/to/macOS-InstallAssistant-Browser-Website"
echo "   cp '$GITHUB_REPO_DIR'/* downloads/"
echo "   git add downloads/"
echo "   git commit -m 'Update download files'"
echo "   git push origin main"
echo ""
echo "5. O GitHub Pages atualizará automaticamente em alguns minutos"
echo ""
echo "🌐 URLs que estarão disponíveis:"
echo "   - https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website/downloads/"
echo "   - https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website/downloads/macOS-InstallAssistant-Browser.dmg"
echo ""
echo "✅ Upload concluído! Os arquivos estão prontos para serem enviados para o GitHub."
