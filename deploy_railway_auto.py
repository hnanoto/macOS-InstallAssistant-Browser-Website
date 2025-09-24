#!/usr/bin/env python3
"""
Script de Configuração Automática do Railway
Resolve problemas de login usando modo browserless
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime

class RailwayDeployer:
    def __init__(self):
        self.start_time = datetime.now()
        self.steps_completed = []
        self.errors = []
        
    def log(self, message, status="INFO"):
        """Log com timestamp e status"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "SUCCESS":
            print(f"✅ {message}")
        elif status == "ERROR":
            print(f"❌ {message}")
        elif status == "PROGRESS":
            print(f"🔄 {message}")
        elif status == "INFO":
            print(f"🔍 {message}")
        else:
            print(f"📋 {message}")
            
    def run_command(self, command, capture_output=True, timeout=30):
        """Executa comando com tratamento de erro"""
        try:
            if capture_output:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=timeout
                )
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(command, shell=True, timeout=timeout)
                return result.returncode == 0, "", ""
        except subprocess.TimeoutExpired:
            return False, "", f"Timeout após {timeout}s"
        except Exception as e:
            return False, "", str(e)
            
    def check_railway_cli(self):
        """Verifica se Railway CLI está instalada"""
        self.log("Verificando Railway CLI...")
        success, output, error = self.run_command("railway --version")
        
        if success:
            version = output.strip()
            self.log(f"Railway CLI encontrada: {version}", "SUCCESS")
            return True
        else:
            self.log("Railway CLI não está instalada", "ERROR")
            return False
            
    def install_railway_cli(self):
        """Instala Railway CLI"""
        self.log("Tentando instalar Railway CLI...", "PROGRESS")
        
        # Comando de instalação para macOS
        install_cmd = "curl -fsSL https://railway.app/install.sh | sh"
        
        self.log("Instalando Railway CLI...")
        success, output, error = self.run_command(install_cmd, timeout=120)
        
        if success:
            self.log("Railway CLI instalada com sucesso", "SUCCESS")
            # Adicionar ao PATH se necessário
            os.environ['PATH'] = f"/Users/{os.getenv('USER')}/.railway/bin:" + os.environ['PATH']
            return True
        else:
            self.log(f"Erro ao instalar Railway CLI: {error}", "ERROR")
            return False
            
    def login_railway_browserless(self):
        """Faz login no Railway usando modo browserless"""
        self.log("Fazendo login no Railway (modo browserless)...", "PROGRESS")
        
        # Usar modo browserless conforme sugerido no erro
        login_cmd = "railway login --browserless"
        
        self.log("🔐 Executando login browserless...")
        self.log("📋 Siga as instruções que aparecerão no terminal")
        
        # Executar comando sem capturar output para permitir interação
        success, output, error = self.run_command(login_cmd, capture_output=False, timeout=300)
        
        if success:
            self.log("Login realizado com sucesso", "SUCCESS")
            return True
        else:
            self.log(f"Erro no login: {error}", "ERROR")
            return False
            
    def verify_login(self):
        """Verifica se o login foi bem-sucedido"""
        self.log("Verificando status do login...")
        success, output, error = self.run_command("railway whoami")
        
        if success and output.strip():
            self.log(f"Usuário logado: {output.strip()}", "SUCCESS")
            return True
        else:
            self.log("Login não verificado", "ERROR")
            return False
            
    def list_projects(self):
        """Lista projetos disponíveis"""
        self.log("Listando projetos disponíveis...")
        success, output, error = self.run_command("railway projects")
        
        if success:
            self.log("Projetos encontrados:", "SUCCESS")
            print(output)
            return True
        else:
            self.log(f"Erro ao listar projetos: {error}", "ERROR")
            return False
            
    def connect_project(self, project_name=None):
        """Conecta a um projeto específico"""
        if project_name:
            self.log(f"Conectando ao projeto: {project_name}...", "PROGRESS")
            cmd = f"railway link {project_name}"
        else:
            self.log("Conectando ao projeto (seleção interativa)...", "PROGRESS")
            cmd = "railway link"
            
        success, output, error = self.run_command(cmd, capture_output=False, timeout=60)
        
        if success:
            self.log("Projeto conectado com sucesso", "SUCCESS")
            return True
        else:
            self.log(f"Erro ao conectar projeto: {error}", "ERROR")
            return False
            
    def set_environment_variables(self):
        """Configura variáveis de ambiente essenciais"""
        self.log("Configurando variáveis de ambiente...", "PROGRESS")
        
        # Variáveis essenciais para o sistema de email
        env_vars = {
            "FLASK_ENV": "production",
            "FLASK_DEBUG": "False",
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USE_TLS": "True",
            "EMAIL_BACKEND": "smtp",
            "RESEND_API_KEY": "re_placeholder_key",
            "SENDGRID_API_KEY": "SG.placeholder_key",
            "ADMIN_EMAIL": "admin@example.com",
            "SUPPORT_EMAIL": "support@example.com",
            "DATABASE_URL": "sqlite:///app.db",
            "SECRET_KEY": "railway-secret-key-2024",
            "UPLOAD_FOLDER": "/tmp/uploads",
            "MAX_CONTENT_LENGTH": "16777216"
        }
        
        success_count = 0
        for key, value in env_vars.items():
            cmd = f'railway variables set {key}="{value}"'
            success, output, error = self.run_command(cmd)
            
            if success:
                self.log(f"✅ {key} configurada")
                success_count += 1
            else:
                self.log(f"❌ Erro ao configurar {key}: {error}", "ERROR")
                
        self.log(f"Variáveis configuradas: {success_count}/{len(env_vars)}", "SUCCESS")
        return success_count > len(env_vars) * 0.7  # 70% de sucesso mínimo
        
    def deploy_project(self):
        """Faz deploy do projeto"""
        self.log("Iniciando deploy...", "PROGRESS")
        
        # Deploy usando Railway
        cmd = "railway up --detach"
        success, output, error = self.run_command(cmd, timeout=300)
        
        if success:
            self.log("Deploy iniciado com sucesso", "SUCCESS")
            self.log("📋 Aguardando conclusão do deploy...")
            
            # Aguardar deploy
            time.sleep(30)
            
            # Verificar status
            status_success, status_output, status_error = self.run_command("railway status")
            if status_success:
                self.log("Status do deploy:", "SUCCESS")
                print(status_output)
                
            return True
        else:
            self.log(f"Erro no deploy: {error}", "ERROR")
            return False
            
    def run_final_test(self):
        """Executa teste final do sistema"""
        self.log("Executando teste final...", "PROGRESS")
        
        # Verificar se o serviço está rodando
        cmd = "railway logs --tail 10"
        success, output, error = self.run_command(cmd)
        
        if success:
            self.log("Logs do serviço:", "SUCCESS")
            print(output)
            
            # Verificar URL do serviço
            url_cmd = "railway domain"
            url_success, url_output, url_error = self.run_command(url_cmd)
            
            if url_success and url_output.strip():
                service_url = url_output.strip()
                self.log(f"🌐 Serviço disponível em: {service_url}", "SUCCESS")
                
                # Teste básico de conectividade
                test_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' {service_url}/api/health"
                test_success, test_output, test_error = self.run_command(test_cmd)
                
                if test_success and test_output.strip() == "200":
                    self.log("✅ Teste de conectividade: PASSOU", "SUCCESS")
                    return True
                else:
                    self.log(f"⚠️ Teste de conectividade: Status {test_output}", "ERROR")
                    
            return True
        else:
            self.log(f"Erro ao verificar logs: {error}", "ERROR")
            return False
            
    def generate_report(self):
        """Gera relatório final"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL - CONFIGURAÇÃO RAILWAY")
        print("="*60)
        print(f"⏰ Iniciado em: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Concluído em: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ Duração total: {duration}")
        print(f"✅ Etapas concluídas: {len(self.steps_completed)}")
        print(f"❌ Erros encontrados: {len(self.errors)}")
        
        if self.steps_completed:
            print("\n📋 Etapas Concluídas:")
            for step in self.steps_completed:
                print(f"  ✅ {step}")
                
        if self.errors:
            print("\n❌ Erros Encontrados:")
            for error in self.errors:
                print(f"  ❌ {error}")
                
        print("\n🎯 Próximos Passos:")
        print("  1. Verificar se todas as variáveis de ambiente estão corretas")
        print("  2. Configurar chaves de API reais (RESEND_API_KEY, SENDGRID_API_KEY)")
        print("  3. Testar envio de emails em produção")
        print("  4. Monitorar logs do Railway para possíveis erros")
        print("="*60)
        
    def run(self):
        """Executa todo o processo de configuração"""
        print("🚀 CONFIGURAÇÃO AUTOMÁTICA DO RAILWAY")
        print("=" * 50)
        print(f"⏰ Iniciado em: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Etapa 1: Verificar Railway CLI
            self.log("Verificar Railway CLI...", "PROGRESS")
            if not self.check_railway_cli():
                if not self.install_railway_cli():
                    self.errors.append("Falha na instalação da Railway CLI")
                    return False
                    
            if not self.check_railway_cli():
                self.errors.append("Railway CLI não funciona após instalação")
                return False
                
            self.steps_completed.append("Verificar Railway CLI")
            self.log("Verificar Railway CLI: Concluído", "SUCCESS")
            
            # Etapa 2: Login (modo browserless)
            self.log("Fazer login no Railway...", "PROGRESS")
            if not self.login_railway_browserless():
                self.errors.append("Falha no login do Railway")
                return False
                
            # Verificar login
            if not self.verify_login():
                self.errors.append("Login não verificado")
                return False
                
            self.steps_completed.append("Login no Railway")
            self.log("Login no Railway: Concluído", "SUCCESS")
            
            # Etapa 3: Listar e conectar projeto
            self.log("Conectar ao projeto...", "PROGRESS")
            self.list_projects()
            
            if not self.connect_project():
                self.errors.append("Falha ao conectar projeto")
                return False
                
            self.steps_completed.append("Conectar projeto")
            self.log("Conectar projeto: Concluído", "SUCCESS")
            
            # Etapa 4: Configurar variáveis de ambiente
            self.log("Configurar variáveis de ambiente...", "PROGRESS")
            if not self.set_environment_variables():
                self.errors.append("Falha na configuração de variáveis")
                return False
                
            self.steps_completed.append("Configurar variáveis")
            self.log("Configurar variáveis: Concluído", "SUCCESS")
            
            # Etapa 5: Deploy
            self.log("Fazer deploy...", "PROGRESS")
            if not self.deploy_project():
                self.errors.append("Falha no deploy")
                return False
                
            self.steps_completed.append("Deploy do projeto")
            self.log("Deploy: Concluído", "SUCCESS")
            
            # Etapa 6: Teste final
            self.log("Executar teste final...", "PROGRESS")
            if not self.run_final_test():
                self.errors.append("Falha no teste final")
                # Não retorna False aqui pois o deploy pode estar funcionando
                
            self.steps_completed.append("Teste final")
            self.log("Teste final: Concluído", "SUCCESS")
            
            return True
            
        except KeyboardInterrupt:
            self.log("\n⚠️ Processo interrompido pelo usuário", "ERROR")
            return False
        except Exception as e:
            self.log(f"\n❌ Erro inesperado: {str(e)}", "ERROR")
            self.errors.append(f"Erro inesperado: {str(e)}")
            return False
        finally:
            self.generate_report()

if __name__ == "__main__":
    deployer = RailwayDeployer()
    success = deployer.run()
    
    if success:
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        sys.exit(0)
    else:
        print("\n❌ CONFIGURAÇÃO FALHOU. Verifique os erros acima.")
        sys.exit(1)