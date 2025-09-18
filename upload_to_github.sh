#!/bin/bash

<<<<<<< HEAD
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
=======
# Script para upload dos arquivos do website para o GitHub
# Uso: ./upload_to_github.sh

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de output
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Verificar se estamos no diretório correto
if [ ! -f "index.html" ]; then
    print_error "Arquivo index.html não encontrado. Execute este script no diretório do website."
    exit 1
fi

print_header "Upload do Website para GitHub"

# Verificar se git está instalado
if ! command -v git &> /dev/null; then
    print_error "Git não está instalado. Instale o Git primeiro."
    exit 1
fi

# Verificar se estamos em um repositório git
if [ ! -d ".git" ]; then
    print_info "Inicializando repositório Git..."
    git init
    git remote add origin https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website.git
fi

# Verificar status do repositório
print_info "Verificando status do repositório..."
git status

# Adicionar todos os arquivos
print_info "Adicionando arquivos ao Git..."
git add .

# Fazer commit
print_info "Fazendo commit das mudanças..."
git commit -m "Atualizar website com informações completas

- Adicionar página principal com recursos e preços
- Incluir seção de download e instalação
- Adicionar FAQ e suporte
- Configurar GitHub Pages
- Atualizar documentação"

# Verificar se há mudanças para fazer push
if git diff --quiet HEAD origin/main 2>/dev/null; then
    print_warning "Nenhuma mudança para fazer push."
else
    print_info "Fazendo push para o GitHub..."
    git push -u origin main
    print_success "Push realizado com sucesso!"
fi

# Verificar se o GitHub Pages está configurado
print_info "Verificando configuração do GitHub Pages..."
print_info "Acesse: https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/settings/pages"
print_info "Certifique-se de que o GitHub Pages está configurado para usar a branch 'main'"

# Mostrar URLs importantes
print_header "URLs Importantes"
echo -e "${GREEN}Website:${NC} https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website"
echo -e "${GREEN}Repositório:${NC} https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website"
echo -e "${GREEN}Releases:${NC} https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases"
echo -e "${GREEN}Configurações:${NC} https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/settings"

# Instruções finais
print_header "Próximos Passos"
echo "1. Acesse as configurações do GitHub Pages"
echo "2. Configure para usar a branch 'main'"
echo "3. Aguarde alguns minutos para o site ser publicado"
echo "4. Teste o website em: https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website"
echo "5. Crie um release com o DMG do aplicativo"

print_success "Upload concluído com sucesso!"
print_info "O website será publicado em alguns minutos no GitHub Pages."
>>>>>>> 2187eb9cc4c89f41f9114f02772ec040405987db
