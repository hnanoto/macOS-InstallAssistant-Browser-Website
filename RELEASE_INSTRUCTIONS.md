# Instruções para Releases

Este documento explica como fazer releases do macOS InstallAssistant Browser no GitHub.

## 📋 Processo de Release

### 1. Preparação
- [ ] Testar o aplicativo completamente
- [ ] Verificar se todas as funcionalidades estão funcionando
- [ ] Atualizar a versão no código
- [ ] Criar o DMG usando o script `create_dmg.command`
- [ ] Testar o DMG em diferentes versões do macOS

### 2. Criando o Release no GitHub

1. **Acesse o repositório**: [https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website](https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website)

2. **Clique em "Releases"** na barra lateral direita

3. **Clique em "Create a new release"**

4. **Preencha os campos**:
   - **Tag version**: `v1.0.0` (ou a versão apropriada)
   - **Release title**: `macOS InstallAssistant Browser v1.0.0`
   - **Description**: Use o template abaixo

### 3. Template de Descrição do Release

```markdown
## 🎉 macOS InstallAssistant Browser v1.0.0

### ✨ Novidades
- Lançamento inicial do macOS InstallAssistant Browser
- Interface intuitiva e moderna
- Download automático de versões do macOS
- Sistema de licenciamento seguro
- Verificação de integridade dos arquivos

### 🚀 Recursos
- ✅ Download automático de versões do macOS
- ✅ Interface intuitiva e moderna
- ✅ Verificação de integridade automática
- ✅ Sistema de licenciamento seguro
- ✅ Suporte técnico completo
- ✅ Atualizações gratuitas por 1 ano

### 📥 Download
- **Arquivo**: `macOS-InstallAssistant-Browser.dmg`
- **Tamanho**: ~3 MB
- **Compatibilidade**: macOS 13.5+

### 🛠️ Instalação
1. Baixe o arquivo DMG
2. Execute o arquivo DMG baixado
3. Arraste o aplicativo para a pasta Applications
4. Abra o aplicativo e insira sua licença
5. Comece a usar imediatamente!

### 💰 Preço
- **Licença Individual**: R$ 26,50 (pagamento único)
- **Formas de Pagamento**: PIX, PayPal, Cartão de Crédito

### 🆘 Suporte
- **Email**: hackintoshandbeyond@gmail.com
- **Documentação**: [Website](https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website)

### 📝 Notas de Versão
- Primeira versão estável
- Interface completamente redesenhada
- Sistema de licenciamento implementado
- Verificação de integridade adicionada

---
**Desenvolvido por**: Henrique  
**Website**: [https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website](https://hnanoto.github.io/macOS-InstallAssistant-Browser-Website)
```

### 4. Anexar Arquivos

1. **Clique em "Attach binaries"**
2. **Selecione o arquivo DMG** criado pelo script
3. **Renomeie para**: `macOS-InstallAssistant-Browser.dmg`

### 5. Publicar

1. **Marque como "Set as the latest release"**
2. **Clique em "Publish release"**

## 🔄 Atualizando o Website

Após criar o release, atualize o website:

1. **Atualize a versão** no `index.html`
2. **Atualize o link de download** se necessário
3. **Commit e push** as mudanças

## 📱 Testando o Release

Após publicar:

1. **Teste o download** do GitHub
2. **Verifique se o DMG funciona** em diferentes versões do macOS
3. **Teste o processo de licenciamento**
4. **Verifique se o suporte está funcionando**

## 🚨 Checklist Final

- [ ] DMG criado e testado
- [ ] Release criado no GitHub
- [ ] Arquivo DMG anexado
- [ ] Descrição completa adicionada
- [ ] Website atualizado
- [ ] Download testado
- [ ] Suporte funcionando
- [ ] Email de notificação enviado (se aplicável)

## 📞 Suporte

Se tiver problemas com o processo de release:

- **Email**: hackintoshandbeyond@gmail.com
- **GitHub Issues**: [Criar Issue](https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/issues)

---

**Última atualização**: 18 de Setembro de 2025
