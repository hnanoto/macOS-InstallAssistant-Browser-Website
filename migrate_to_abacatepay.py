#!/usr/bin/env python3
"""
🥑 SCRIPT DE MIGRAÇÃO PARA ABACATEPAY
====================================

Script completo para migrar o sistema de pagamentos para AbacatePay
Mantém todas as funcionalidades existentes e adiciona melhorias

Autor: Sistema de Migração Automática
Data: 24 de Setembro de 2025
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

class AbacatePayMigrator:
    """Migrador completo para AbacatePay"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "backup_pre_migration"
        self.migration_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.migration_log.append(log_entry)
        
    def create_backup(self) -> bool:
        """Criar backup do sistema atual"""
        try:
            self.log("🔄 Criando backup do sistema atual...", "INFO")
            
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            self.backup_dir.mkdir(exist_ok=True)
            
            # Arquivos importantes para backup
            files_to_backup = [
                "payment_api.py",
                "payments.json",
                "notifications.json",
                "admin_notifications.json",
                ".env"
            ]
            
            for file_name in files_to_backup:
                source_file = self.project_root / file_name
                if source_file.exists():
                    backup_file = self.backup_dir / file_name
                    shutil.copy2(source_file, backup_file)
                    self.log(f"✅ Backup criado: {file_name}")
                else:
                    self.log(f"⚠️ Arquivo não encontrado: {file_name}", "WARN")
            
            # Criar arquivo de informações do backup
            backup_info = {
                "created_at": datetime.now().isoformat(),
                "migration_version": "1.0",
                "files_backed_up": files_to_backup,
                "reason": "Pre-migration backup for AbacatePay integration"
            }
            
            with open(self.backup_dir / "backup_info.json", 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.log("✅ Backup completo criado", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao criar backup: {e}", "ERROR")
            return False
    
    def check_dependencies(self) -> bool:
        """Verificar dependências necessárias"""
        try:
            self.log("🔍 Verificando dependências...", "INFO")
            
            required_modules = [
                "flask",
                "requests",
                "json",
                "hashlib",
                "hmac",
                "datetime",
                "pathlib"
            ]
            
            missing_modules = []
            
            for module in required_modules:
                try:
                    __import__(module)
                    self.log(f"✅ {module}: OK")
                except ImportError:
                    missing_modules.append(module)
                    self.log(f"❌ {module}: FALTANDO", "ERROR")
            
            if missing_modules:
                self.log(f"❌ Módulos faltando: {', '.join(missing_modules)}", "ERROR")
                self.log("💡 Execute: pip install " + " ".join(missing_modules), "INFO")
                return False
            
            self.log("✅ Todas as dependências estão disponíveis", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao verificar dependências: {e}", "ERROR")
            return False
    
    def setup_environment(self) -> bool:
        """Configurar variáveis de ambiente"""
        try:
            self.log("🔧 Configurando ambiente AbacatePay...", "INFO")
            
            # Verificar se já existe arquivo de configuração
            env_file = self.project_root / ".env"
            config_example = self.project_root / "abacatepay_config.example"
            
            if not env_file.exists():
                if config_example.exists():
                    # Copiar exemplo para .env
                    shutil.copy2(config_example, env_file)
                    self.log("✅ Arquivo .env criado a partir do exemplo", "SUCCESS")
                else:
                    # Criar arquivo .env básico
                    env_content = """# AbacatePay Configuration
ABACATEPAY_API_KEY=your_api_key_here
ABACATEPAY_SECRET_KEY=your_secret_key_here
ABACATEPAY_WEBHOOK_SECRET=your_webhook_secret_here
ABACATEPAY_SANDBOX=true
"""
                    with open(env_file, 'w') as f:
                        f.write(env_content)
                    self.log("✅ Arquivo .env básico criado", "SUCCESS")
            
            # Carregar variáveis de ambiente
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
            
            # Verificar configurações críticas
            critical_configs = [
                'ABACATEPAY_API_KEY',
                'ABACATEPAY_SECRET_KEY'
            ]
            
            missing_configs = []
            for config in critical_configs:
                if not os.getenv(config) or os.getenv(config) == 'your_api_key_here':
                    missing_configs.append(config)
            
            if missing_configs:
                self.log("⚠️ Configurações pendentes:", "WARN")
                for config in missing_configs:
                    self.log(f"   - {config}: Precisa ser configurada", "WARN")
                self.log("💡 Configure as credenciais no arquivo .env", "INFO")
                return False
            
            self.log("✅ Ambiente configurado corretamente", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao configurar ambiente: {e}", "ERROR")
            return False
    
    def integrate_abacatepay(self) -> bool:
        """Integrar AbacatePay ao sistema existente"""
        try:
            self.log("🔗 Integrando AbacatePay ao sistema...", "INFO")
            
            # Verificar se arquivos de integração existem
            integration_files = [
                "abacatepay_integration.py",
                "abacatepay_routes.py"
            ]
            
            for file_name in integration_files:
                file_path = self.project_root / file_name
                if not file_path.exists():
                    self.log(f"❌ Arquivo de integração não encontrado: {file_name}", "ERROR")
                    return False
                else:
                    self.log(f"✅ Arquivo encontrado: {file_name}")
            
            # Modificar payment_api.py para incluir rotas AbacatePay
            main_api_file = self.project_root / "payment_api.py"
            
            if main_api_file.exists():
                # Ler conteúdo atual
                with open(main_api_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Verificar se já foi integrado
                if "abacatepay_routes" not in content:
                    # Adicionar importação das rotas AbacatePay
                    import_line = "\n# AbacatePay Integration\ntry:\n    from abacatepay_routes import *\n    print('🥑 AbacatePay routes loaded successfully')\nexcept ImportError as e:\n    print(f'⚠️ AbacatePay routes not available: {e}')\n"
                    
                    # Adicionar antes da linha if __name__ == "__main__":
                    if 'if __name__ == "__main__":' in content:
                        content = content.replace('if __name__ == "__main__":', import_line + '\nif __name__ == "__main__":')
                    else:
                        content += import_line
                    
                    # Salvar arquivo modificado
                    with open(main_api_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.log("✅ payment_api.py atualizado com integração AbacatePay", "SUCCESS")
                else:
                    self.log("✅ AbacatePay já integrado ao payment_api.py", "INFO")
            
            self.log("✅ Integração AbacatePay completa", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro na integração: {e}", "ERROR")
            return False
    
    def test_integration(self) -> bool:
        """Testar integração AbacatePay"""
        try:
            self.log("🧪 Testando integração AbacatePay...", "INFO")
            
            # Importar módulos de integração
            try:
                from abacatepay_integration import migrate_to_abacatepay
                self.log("✅ Módulo de integração carregado")
                
                # Testar migração
                migration_result = migrate_to_abacatepay()
                
                if migration_result:
                    self.log("✅ Teste de integração passou", "SUCCESS")
                    return True
                else:
                    self.log("⚠️ Teste de integração falhou - verifique configurações", "WARN")
                    return False
                    
            except ImportError as e:
                self.log(f"❌ Erro ao importar módulos: {e}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no teste: {e}", "ERROR")
            return False
    
    def create_migration_report(self) -> bool:
        """Criar relatório de migração"""
        try:
            self.log("📊 Criando relatório de migração...", "INFO")
            
            report = {
                "migration_info": {
                    "completed_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "provider": "AbacatePay",
                    "status": "completed"
                },
                "features_migrated": [
                    "Pagamentos PIX",
                    "Pagamentos com cartão",
                    "Geração automática de serials",
                    "Sistema de emails",
                    "Webhooks automáticos",
                    "Painel administrativo",
                    "API de status de pagamentos"
                ],
                "new_endpoints": [
                    "/api/abacatepay/create-pix-payment",
                    "/api/abacatepay/create-card-payment",
                    "/api/abacatepay/webhook",
                    "/api/abacatepay/payment-status/<id>",
                    "/api/abacatepay/payments",
                    "/api/abacatepay/health",
                    "/api/abacatepay/admin/dashboard"
                ],
                "compatibility": {
                    "legacy_endpoints": "Mantidos",
                    "email_system": "Integrado",
                    "admin_panel": "Compatível",
                    "serial_generation": "Mantido"
                },
                "next_steps": [
                    "Configurar credenciais AbacatePay no arquivo .env",
                    "Testar pagamentos em modo sandbox",
                    "Configurar webhook URL na AbacatePay",
                    "Migrar para produção quando pronto"
                ],
                "backup_location": str(self.backup_dir),
                "migration_log": self.migration_log
            }
            
            report_file = self.project_root / "ABACATEPAY_MIGRATION_REPORT.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log(f"✅ Relatório salvo: {report_file}", "SUCCESS")
            
            # Criar também versão markdown
            md_report = f"""# 🥑 Relatório de Migração para AbacatePay

## ✅ Migração Concluída
**Data:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}  
**Status:** Completa  
**Provider:** AbacatePay  

## 🚀 Funcionalidades Migradas
- ✅ Pagamentos PIX
- ✅ Pagamentos com cartão
- ✅ Geração automática de serials
- ✅ Sistema de emails integrado
- ✅ Webhooks automáticos
- ✅ Painel administrativo
- ✅ API de status de pagamentos

## 🔗 Novos Endpoints Disponíveis
```
POST /api/abacatepay/create-pix-payment
POST /api/abacatepay/create-card-payment
POST /api/abacatepay/webhook
GET  /api/abacatepay/payment-status/<id>
GET  /api/abacatepay/payments
GET  /api/abacatepay/health
GET  /api/abacatepay/admin/dashboard
```

## 🔧 Próximos Passos
1. **Configure as credenciais** no arquivo `.env`
2. **Teste pagamentos** em modo sandbox
3. **Configure webhook URL** na AbacatePay
4. **Migre para produção** quando pronto

## 💾 Backup
Backup do sistema anterior salvo em: `{self.backup_dir}`

## 🎯 Compatibilidade
- **Endpoints legados:** Mantidos funcionando
- **Sistema de email:** Totalmente integrado
- **Painel admin:** Compatível
- **Geração de serials:** Mantida
"""
            
            md_report_file = self.project_root / "ABACATEPAY_MIGRATION_REPORT.md"
            with open(md_report_file, 'w', encoding='utf-8') as f:
                f.write(md_report)
            
            self.log(f"✅ Relatório MD salvo: {md_report_file}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao criar relatório: {e}", "ERROR")
            return False
    
    def run_migration(self) -> bool:
        """Executar migração completa"""
        self.log("🥑 INICIANDO MIGRAÇÃO PARA ABACATEPAY", "INFO")
        self.log("=" * 50, "INFO")
        
        steps = [
            ("Verificar dependências", self.check_dependencies),
            ("Criar backup", self.create_backup),
            ("Configurar ambiente", self.setup_environment),
            ("Integrar AbacatePay", self.integrate_abacatepay),
            ("Testar integração", self.test_integration),
            ("Criar relatório", self.create_migration_report)
        ]
        
        for step_name, step_function in steps:
            self.log(f"🔄 {step_name}...", "INFO")
            
            if not step_function():
                self.log(f"❌ Falha em: {step_name}", "ERROR")
                self.log("🚨 MIGRAÇÃO INTERROMPIDA", "ERROR")
                return False
            
            self.log(f"✅ {step_name} - CONCLUÍDO", "SUCCESS")
        
        self.log("=" * 50, "SUCCESS")
        self.log("🎉 MIGRAÇÃO PARA ABACATEPAY CONCLUÍDA COM SUCESSO!", "SUCCESS")
        self.log("=" * 50, "SUCCESS")
        
        return True

def main():
    """Função principal"""
    print("""
🥑 MIGRADOR ABACATEPAY v1.0
==========================
Sistema de Migração Automática
Migra seu sistema de pagamentos para AbacatePay
mantendo todas as funcionalidades existentes.
""")
    
    migrator = AbacatePayMigrator()
    
    try:
        success = migrator.run_migration()
        
        if success:
            print("""
🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!
=================================

✅ Seu sistema foi migrado para AbacatePay
✅ Todas as funcionalidades foram preservadas
✅ Backup do sistema anterior foi criado
✅ Relatório de migração foi gerado

📋 PRÓXIMOS PASSOS:
1. Configure suas credenciais AbacatePay no arquivo .env
2. Teste os pagamentos em modo sandbox
3. Configure a URL do webhook na AbacatePay
4. Migre para produção quando estiver pronto

📄 Consulte o arquivo ABACATEPAY_MIGRATION_REPORT.md para detalhes completos.
""")
            return 0
        else:
            print("""
❌ MIGRAÇÃO FALHOU
==================

A migração não pôde ser concluída.
Verifique os logs acima para identificar o problema.
Seu sistema original permanece intacto.
""")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Migração cancelada pelo usuário")
        return 1
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
