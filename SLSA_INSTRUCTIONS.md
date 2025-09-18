# 🚀 Instruções para Usar SLSA

Este documento explica como usar o sistema SLSA configurado para criar releases seguros do macOS InstallAssistant Browser.

## 📋 Pré-requisitos

- [ ] Repositório configurado com SLSA
- [ ] DMG do aplicativo criado
- [ ] Acesso ao GitHub Actions
- [ ] Permissões de administrador no repositório

## 🎯 Como Criar um Release Seguro

### **Passo 1: Preparar o DMG**
1. **Crie o DMG** usando o script `create_dmg.command`
2. **Teste o DMG** em diferentes versões do macOS
3. **Verifique** se o aplicativo funciona corretamente
4. **Salve** o DMG em um local acessível

### **Passo 2: Executar o Workflow**
1. **Acesse**: https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/actions
2. **Clique** em "Create Release with SLSA"
3. **Clique** em "Run workflow"
4. **Preencha os campos**:
   - **Version**: `v1.0.0` (ou a versão apropriada)
   - **Release notes**: Descrição das mudanças
5. **Clique** em "Run workflow"

### **Passo 3: Anexar o DMG**
1. **Aguarde** o workflow criar o release
2. **Acesse** a página do release
3. **Clique** em "Edit release"
4. **Arraste** o arquivo DMG para a seção de assets
5. **Salve** as mudanças

### **Passo 4: Verificar SLSA**
1. **Aguarde** alguns minutos
2. **Verifique** se o badge "Verified" aparece
3. **Confirme** que o arquivo `slsa-provenance.json` está anexado
4. **Teste** o download do DMG

## 🔍 Verificação de Segurança

### **Badge "Verified"**
- ✅ Aparece automaticamente quando SLSA é processado
- ✅ Indica que o release é autêntico
- ✅ Confirma que o arquivo não foi modificado

### **Arquivo de Proveniência**
- ✅ `slsa-provenance.json` é anexado automaticamente
- ✅ Contém informações sobre o build
- ✅ Inclui hash do arquivo e assinatura digital

### **Logs do GitHub Actions**
- ✅ Mostram o processo de geração de certificados
- ✅ Confirmam que a verificação foi bem-sucedida
- ✅ Registram todos os passos de segurança

## 🛠️ Troubleshooting

### **Problema: Workflow não executa**
- Verifique se você tem permissões de administrador
- Confirme que o repositório está configurado corretamente
- Veja se há erros nos logs do GitHub Actions

### **Problema: Badge "Verified" não aparece**
- Aguarde alguns minutos para propagação
- Verifique se o arquivo DMG foi anexado
- Confirme que o workflow SLSA foi executado

### **Problema: Certificado não é gerado**
- Verifique se o arquivo DMG existe
- Confirme que as permissões estão corretas
- Veja os logs detalhados do workflow

## 📊 Monitoramento

### **GitHub Actions**
- Monitore os workflows em: https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/actions
- Verifique se todos os jobs passam
- Confirme que os certificados são gerados

### **Releases**
- Acesse: https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases
- Verifique se o badge "Verified" está presente
- Confirme que o arquivo de proveniência está anexado

## 🎉 Benefícios Alcançados

Com o SLSA configurado, você agora tem:

- 🔒 **Segurança máxima** para seus releases
- ✅ **Verificação automática** de integridade
- 🛡️ **Proteção contra falsificação**
- 📋 **Rastreabilidade completa**
- 🎯 **Maior confiança dos usuários**
- 🏆 **Padrão da indústria** de segurança

## 📚 Recursos Adicionais

- **SLSA Framework**: https://slsa.dev/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Verificação SLSA**: https://slsa.dev/verification
- **Documentação SLSA**: [SLSA_SECURITY.md](SLSA_SECURITY.md)

## 🆘 Suporte

Se tiver problemas com o SLSA:

- **Email**: hackintoshandbeyond@gmail.com
- **GitHub Issues**: [Criar Issue](https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/issues)
- **Documentação**: Consulte os arquivos de documentação

---

**Última atualização**: 18 de Setembro de 2025  
**Versão SLSA**: v1.9.0
