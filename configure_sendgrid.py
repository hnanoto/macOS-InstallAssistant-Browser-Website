#!/usr/bin/env python3
"""
🔧 CONFIGURAÇÃO AUTOMÁTICA DO SENDGRID
=====================================

Este script ajuda a configurar o SendGrid no Railway
e testa se está funcionando corretamente.
"""

import requests
import json
from datetime import datetime

class SendGridConfigurator:
    def __init__(self, railway_url="https://web-production-1513a.up.railway.app"):
        self.railway_url = railway_url
        
    def check_current_config(self):
        """Verifica configuração atual"""
        print("🔍 VERIFICANDO CONFIGURAÇÃO ATUAL DO SENDGRID")
        print("=" * 60)
        
        try:
            response = requests.get(f"{self.railway_url}/api/debug/sendgrid-test", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ SendGrid está configurado e funcionando!")
                    return True
                else:
                    print(f"❌ SendGrid não está configurado: {result.get('error')}")
                    return False
            else:
                print(f"❌ Erro ao verificar SendGrid: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao verificar SendGrid: {e}")
            return False
    
    def test_sendgrid_with_key(self, api_key):
        """Testa SendGrid com uma API Key específica"""
        print(f"\n🧪 TESTANDO SENDGRID COM API KEY")
        print("=" * 50)
        
        if not api_key or api_key.startswith('SG.') == False:
            print("❌ API Key inválida. Deve começar com 'SG.'")
            return False
        
        try:
            # Simular teste local (não podemos alterar variáveis do Railway via API)
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=api_key)
            
            message = Mail(
                from_email='noreply@sendgrid.net',
                to_emails='hackintoshandbeyond@gmail.com',
                subject='Teste SendGrid - Sistema de Pagamentos',
                html_content='<p>Este é um teste do sistema SendGrid para o sistema de pagamentos.</p>'
            )
            
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                print("✅ SendGrid funcionando! API Key válida.")
                return True
            else:
                print(f"❌ SendGrid falhou: Status {response.status_code}")
                return False
                
        except ImportError:
            print("❌ SendGrid não instalado. Execute: pip install sendgrid")
            return False
        except Exception as e:
            print(f"❌ Erro no teste SendGrid: {e}")
            return False
    
    def generate_railway_config(self, api_key):
        """Gera configuração para Railway"""
        print(f"\n📋 CONFIGURAÇÃO PARA RAILWAY")
        print("=" * 40)
        
        config = {
            "SENDGRID_API_KEY": api_key,
            "USE_SENDGRID": "true",
            "SMTP_ENABLED": "false",
            "EMAIL_PROVIDER": "sendgrid"
        }
        
        print("🔧 Variáveis para adicionar no Railway Dashboard:")
        print()
        for key, value in config.items():
            print(f"   {key}={value}")
        
        print()
        print("📝 INSTRUÇÕES:")
        print("1. Acesse: https://railway.app/dashboard")
        print("2. Projeto: web-production-1513a")
        print("3. Clique: 'Variables'")
        print("4. Adicione as variáveis acima")
        print("5. Clique: 'Deploy' para reiniciar")
        
        return config
    
    def test_after_configuration(self):
        """Testa sistema após configuração"""
        print(f"\n🧪 TESTANDO SISTEMA APÓS CONFIGURAÇÃO")
        print("=" * 50)
        
        # Aguardar um pouco para o deploy
        import time
        print("⏳ Aguardando 30 segundos para deploy...")
        time.sleep(30)
        
        # Teste 1: SendGrid
        if self.check_current_config():
            print("✅ SendGrid configurado com sucesso!")
            
            # Teste 2: Email de teste
            try:
                response = requests.post(
                    f"{self.railway_url}/api/debug/test-email",
                    json={
                        "to": "hackintoshandbeyond@gmail.com",
                        "subject": "TESTE - SendGrid Configurado",
                        "body": "Se você receber este email, o SendGrid está funcionando!"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print("✅ Email de teste enviado com sucesso!")
                        return True
                    else:
                        print(f"❌ Email de teste falhou: {result.get('error')}")
                        return False
                else:
                    print(f"❌ Erro no teste de email: Status {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Erro no teste de email: {e}")
                return False
        else:
            print("❌ SendGrid ainda não está configurado")
            return False
    
    def run_configuration(self, api_key=None):
        """Executa configuração completa"""
        print("🔧 CONFIGURAÇÃO AUTOMÁTICA DO SENDGRID")
        print("=" * 60)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        
        # Verificar configuração atual
        if self.check_current_config():
            print("\n✅ SendGrid já está configurado e funcionando!")
            return True
        
        # Se API Key fornecida, testar
        if api_key:
            if self.test_sendgrid_with_key(api_key):
                self.generate_railway_config(api_key)
                print("\n⏳ Após configurar no Railway, execute novamente para testar.")
                return True
            else:
                print("\n❌ API Key inválida. Verifique se está correta.")
                return False
        else:
            print("\n📝 Para configurar SendGrid:")
            print("1. Forneça sua API Key do SendGrid")
            print("2. Execute: python configure_sendgrid.py SUA_API_KEY")
            print("3. Configure as variáveis no Railway")
            print("4. Execute novamente para testar")
            return False

if __name__ == "__main__":
    import sys
    
    railway_url = "https://web-production-1513a.up.railway.app"
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    
    configurator = SendGridConfigurator(railway_url)
    configurator.run_configuration(api_key)
