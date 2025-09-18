# 🔒 SLSA Security - macOS InstallAssistant Browser

Este documento explica como o SLSA (Supply-chain Levels for Software Artifacts) protege os releases do macOS InstallAssistant Browser.

## 🛡️ O que é SLSA?

SLSA é um framework de segurança que garante a autenticidade e integridade dos artefatos de software. Ele cria "certificados digitais" que provam que um arquivo foi realmente criado pelo repositório oficial.

## 🎯 Benefícios para o macOS InstallAssistant Browser

### ✅ **Segurança para Usuários**
- **Proteção contra malware**: Usuários podem verificar se o DMG é autêntico
- **Prevenção de ataques**: Evita downloads de versões falsas do aplicativo
- **Confiança**: Aumenta a credibilidade do produto

### ✅ **Segurança para Desenvolvedor**
- **Proteção da marca**: Evita que terceiros distribuam versões modificadas
- **Rastreabilidade**: Cada release é rastreado e verificado
- **Compliance**: Atende padrões de segurança da indústria

## 🔍 Como Funciona

### 1. **Geração de Proveniência**
- Quando você cria um release, o GitHub Actions gera um certificado
- O certificado contém informações sobre como o software foi construído
- Inclui hash do arquivo, timestamp, e assinatura digital

### 2. **Verificação Automática**
- O certificado é anexado automaticamente ao release
- Usuários podem verificar a autenticidade do arquivo
- GitHub mostra um badge de "Verified" no release

### 3. **Transparência Total**
- Todo o processo é público e auditável
- Logs de build são preservados
- Histórico completo de mudanças

## 📋 Arquivos de Configuração

### `.github/workflows/slsa-generator.yml`
- Workflow principal do SLSA
- Gera certificados de proveniência
- Verifica integridade dos arquivos

### `.github/workflows/release.yml`
- Workflow para criação de releases
- Integra com o SLSA Generator
- Automatiza todo o processo

## 🚀 Como Usar

### **Criar um Release Seguro:**

1. **Acesse Actions**: https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/actions
2. **Execute "Create Release with SLSA"**
3. **Preencha os campos**:
   - Version: `v1.0.0`
   - Release notes: Descrição das mudanças
4. **Clique em "Run workflow"**

### **Resultado:**
- ✅ Release criado automaticamente
- ✅ Certificado SLSA gerado
- ✅ Badge "Verified" no GitHub
- ✅ Arquivo `slsa-provenance.json` anexado

## 🔍 Verificação de Segurança

### **Para Usuários:**
1. Baixe o DMG do release
2. Verifique o badge "Verified" no GitHub
3. Confirme que o arquivo `slsa-provenance.json` está presente
4. Use ferramentas de verificação SLSA (opcional)

### **Para Desenvolvedores:**
1. Monitore os logs do GitHub Actions
2. Verifique se os certificados são gerados corretamente
3. Confirme que os hashes dos arquivos estão corretos

## 📊 Níveis de Segurança SLSA

### **Nível 1 - Scripts de Build**
- ✅ Builds são executados por scripts
- ✅ Scripts são versionados no controle de origem

### **Nível 2 - Proveniência**
- ✅ Proveniência é gerada automaticamente
- ✅ Proveniência é assinada digitalmente

### **Nível 3 - Ambiente Não-Confiança**
- ✅ Builds são executados em ambiente isolado
- ✅ Ambiente é configurado de forma determinística

## 🛠️ Troubleshooting

### **Problema: Workflow falha**
- Verifique se o arquivo DMG existe
- Confirme que as permissões estão corretas
- Veja os logs do GitHub Actions

### **Problema: Certificado não é gerado**
- Verifique se o tag foi criado corretamente
- Confirme que o workflow foi executado
- Verifique as permissões do repositório

### **Problema: Badge não aparece**
- Aguarde alguns minutos para propagação
- Verifique se o release foi criado corretamente
- Confirme que o certificado está anexado

## 📚 Recursos Adicionais

- **SLSA Framework**: https://slsa.dev/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Verificação SLSA**: https://slsa.dev/verification

## 🎉 Resultado Final

Com o SLSA configurado, cada release do macOS InstallAssistant Browser terá:

- 🔒 **Certificado de autenticidade**
- ✅ **Badge "Verified" no GitHub**
- 🛡️ **Proteção contra falsificação**
- 📋 **Rastreabilidade completa**
- 🎯 **Maior confiança dos usuários**

---

**Última atualização**: 18 de Setembro de 2025  
**Versão SLSA**: v1.9.0
