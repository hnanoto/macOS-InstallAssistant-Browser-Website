# 🚀 Instruções para Publicar o Website

Este documento contém todas as instruções necessárias para publicar o website do macOS InstallAssistant Browser no GitHub Pages.

## 📋 Pré-requisitos

- [ ] Conta no GitHub
- [ ] Repositório criado: [https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website](https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website)
- [ ] Git instalado no seu Mac
- [ ] Acesso ao terminal

## 🎯 Passo a Passo

### 1. Preparar os Arquivos

Todos os arquivos do website já foram criados na pasta `github_website/`:

- ✅ `index.html` - Página principal
- ✅ `css/style.css` - Estilos do website
- ✅ `js/script.js` - Funcionalidades JavaScript
- ✅ `README.md` - Documentação
- ✅ `_config.yml` - Configuração do GitHub Pages
- ✅ `.nojekyll` - Arquivo para GitHub Pages
- ✅ `RELEASE_INSTRUCTIONS.md` - Instruções para releases
- ✅ `upload_to_github.sh` - Script de upload

### 2. Upload para o GitHub

#### Opção A: Usando o Script Automático (Recomendado)

```bash
# Navegar para a pasta do website
cd "/Users/henrique/Desktop/Backup-Matrix/Layout-NOVO-Processo/Andamento-Projeto -Cursor/website/api/github_website"

# Executar o script de upload
./upload_to_github.sh
```

#### Opção B: Upload Manual

```bash
# Navegar para a pasta do website
cd "/Users/henrique/Desktop/Backup-Matrix/Layout-NOVO-Processo/Andamento-Projeto -Cursor/website/api/github_website"

# Inicializar repositório Git (se necessário)
git init

# Adicionar repositório remoto
git remote add origin https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website.git

# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Adicionar website completo do macOS InstallAssistant Browser"

# Fazer push
git push -u origin main
```

### 3. Configurar GitHub Pages

1. **Acesse o repositório**: [https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website](https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website)

2. **Vá para Settings**: Clique na aba "Settings" no repositório

3. **Configure GitHub Pages**:
   - Role para baixo até "Pages"
   - Em "Source", selecione "Deploy from a branch"
   - Em "Branch", selecione "main"
   - Clique em "Save"

4. **Aguarde a publicação**: O GitHub levará alguns minutos para publicar o site

### 4. Verificar o Website

Após a configuração, o website estará disponível em:
**https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website**

## 🎨 Conteúdo do Website

O website inclui:

### 📄 Página Principal
- **Hero Section**: Apresentação do produto
- **Recursos**: Lista de funcionalidades
- **Preços**: Informações de licenciamento
- **Download**: Links para download
- **Suporte**: Informações de contato
- **FAQ**: Perguntas frequentes

### 🔗 Links Importantes
- **GitHub Releases**: [https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases](https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases)
- **Download Direto**: Link para o DMG
- **Suporte**: hackintoshandbeyond@gmail.com

### 💰 Informações de Venda
- **Preço**: R$ 26,50
- **Formas de Pagamento**: PIX, PayPal, Cartão
- **Garantia**: 30 dias
- **Suporte**: 24 horas

## 🚀 Criando um Release

Para adicionar o DMG do aplicativo:

1. **Acesse Releases**: [https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases](https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases)

2. **Clique em "Create a new release"**

3. **Preencha os campos**:
   - Tag: `v1.0.0`
   - Title: `macOS InstallAssistant Browser v1.0.0`
   - Description: Use o template do arquivo `RELEASE_INSTRUCTIONS.md`

4. **Anexe o DMG**: Arraste o arquivo `macOS-InstallAssistant-Browser.dmg`

5. **Publique**: Clique em "Publish release"

## 🔄 Atualizações Futuras

Para atualizar o website:

1. **Edite os arquivos** na pasta `github_website/`
2. **Execute o script** `./upload_to_github.sh`
3. **Aguarde** a atualização automática

## 🆘 Suporte

Se tiver problemas:

- **Email**: hackintoshandbeyond@gmail.com
- **GitHub Issues**: [Criar Issue](https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/issues)

## ✅ Checklist Final

- [ ] Arquivos criados na pasta `github_website/`
- [ ] Script de upload executado
- [ ] GitHub Pages configurado
- [ ] Website acessível em: https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website
- [ ] Release criado com DMG
- [ ] Links de download funcionando
- [ ] Informações de contato corretas

## 🎉 Resultado Final

Após seguir todas as instruções, você terá:

- ✅ Website profissional e responsivo
- ✅ Informações completas sobre o produto
- ✅ Sistema de download funcionando
- ✅ Integração com GitHub Releases
- ✅ Suporte e FAQ
- ✅ Design moderno e atrativo

---

**Desenvolvido por**: Henrique  
**Data**: 18 de Setembro de 2025  
**Versão**: 1.0.0
