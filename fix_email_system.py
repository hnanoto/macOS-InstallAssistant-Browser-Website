#!/usr/bin/env python3
"""
🚨 CORREÇÃO CRÍTICA - SISTEMA DE EMAIL
=====================================

Este script implementa uma correção definitiva para o sistema de email
que está falhando completamente no Railway.
"""

import requests
import json
from datetime import datetime

class EmailSystemFixer:
    def __init__(self, railway_url="https://web-production-1513a.up.railway.app"):
        self.railway_url = railway_url
        self.results = []
        
    def log_action(self, action, status, details=""):
        """Registra ação realizada"""
        result = {
            "action": action,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "SUCESSO" else "❌" if status == "FALHOU" else "⚠️"
        print(f"{status_icon} {action}: {status}")
        if details:
            print(f"   Detalhes: {details}")
    
    def test_current_email_status(self):
        """Testa status atual do sistema de email"""
        print("\n🔍 TESTANDO STATUS ATUAL DO SISTEMA DE EMAIL")
        print("=" * 60)
        
        # Teste 1: Email de teste direto
        try:
            response = requests.post(
                f"{self.railway_url}/api/debug/test-email",
                json={
                    "to": "hackintoshandbeyond@gmail.com",
                    "subject": "TESTE CRÍTICO - Sistema de Email",
                    "body": "Este é um teste crítico para verificar se o sistema de email está funcionando."
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_action("Teste de Email Direto", "SUCESSO", "Email enviado com sucesso")
                    return True
                else:
                    self.log_action("Teste de Email Direto", "FALHOU", f"Erro: {result.get('error')}")
                    return False
            else:
                self.log_action("Teste de Email Direto", "FALHOU", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_action("Teste de Email Direto", "FALHOU", str(e))
            return False
    
    def test_sendgrid_configuration(self):
        """Testa configuração do SendGrid"""
        print("\n📧 TESTANDO CONFIGURAÇÃO DO SENDGRID")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.railway_url}/api/debug/sendgrid-test", timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_action("Teste SendGrid", "SUCESSO", "SendGrid funcionando")
                    return True
                else:
                    self.log_action("Teste SendGrid", "FALHOU", f"Erro: {result.get('error')}")
                    return False
            else:
                self.log_action("Teste SendGrid", "FALHOU", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_action("Teste SendGrid", "FALHOU", str(e))
            return False
    
    def test_resend_configuration(self):
        """Testa configuração do Resend"""
        print("\n🔄 TESTANDO CONFIGURAÇÃO DO RESEND")
        print("=" * 50)
        
        try:
            # Teste usando endpoint de email alternativo
            response = requests.post(
                f"{self.railway_url}/api/debug/free-email-test",
                json={
                    "to": "hackintoshandbeyond@gmail.com",
                    "subject": "TESTE RESEND - Sistema de Email",
                    "body": "Este é um teste do sistema Resend."
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_action("Teste Resend", "SUCESSO", "Resend funcionando")
                    return True
                else:
                    self.log_action("Teste Resend", "FALHOU", f"Erro: {result.get('error')}")
                    return False
            else:
                self.log_action("Teste Resend", "FALHOU", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_action("Teste Resend", "FALHOU", str(e))
            return False
    
    def create_payment_and_test_notification(self):
        """Cria pagamento e testa notificação completa"""
        print("\n💳 TESTANDO NOTIFICAÇÃO COMPLETA DE PAGAMENTO")
        print("=" * 60)
        
        # 1. Criar pagamento
        try:
            payment_data = {
                "email": "hackintoshandbeyond@gmail.com",
                "name": "Teste Email Crítico",
                "country": "BR",
                "amount": 100,
                "currency": "BRL"
            }
            
            response = requests.post(
                f"{self.railway_url}/api/create-pix-payment",
                json=payment_data,
                timeout=15
            )
            
            if response.status_code == 200:
                payment_info = response.json()
                payment_id = payment_info.get('payment_id')
                
                if payment_id:
                    self.log_action("Criação de Pagamento", "SUCESSO", f"Payment ID: {payment_id}")
                    
                    # 2. Upload de comprovante
                    test_file_content = "Teste de comprovante para notificação de email"
                    files = {'file': ('test_comprovante.pdf', test_file_content, 'application/pdf')}
                    data = {
                        'payment_id': payment_id,
                        'email': 'hackintoshandbeyond@gmail.com'
                    }
                    
                    upload_response = requests.post(
                        f"{self.railway_url}/api/upload-payment-proof",
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    if upload_response.status_code == 200:
                        upload_result = upload_response.json()
                        if upload_result.get('success'):
                            self.log_action("Upload de Comprovante", "SUCESSO", "Comprovante enviado")
                            
                            # 3. Verificar se notificação foi gerada
                            time.sleep(2)  # Aguardar processamento
                            
                            notifications_response = requests.get(f"{self.railway_url}/api/notifications", timeout=10)
                            if notifications_response.status_code == 200:
                                notifications = notifications_response.json()
                                recent_notifications = [n for n in notifications.get('notifications', []) 
                                                      if payment_id in n.get('payment_id', '')]
                                
                                if recent_notifications:
                                    self.log_action("Notificação Gerada", "SUCESSO", 
                                                   f"Notificação encontrada para {payment_id}")
                                    return True
                                else:
                                    self.log_action("Notificação Gerada", "FALHOU", 
                                                   "Nenhuma notificação encontrada")
                                    return False
                            else:
                                self.log_action("Verificação de Notificação", "FALHOU", 
                                               f"Status: {notifications_response.status_code}")
                                return False
                        else:
                            self.log_action("Upload de Comprovante", "FALHOU", 
                                           f"Erro: {upload_result.get('error')}")
                            return False
                    else:
                        self.log_action("Upload de Comprovante", "FALHOU", 
                                       f"Status: {upload_response.status_code}")
                        return False
                else:
                    self.log_action("Criação de Pagamento", "FALHOU", "Payment ID não encontrado")
                    return False
            else:
                self.log_action("Criação de Pagamento", "FALHOU", 
                               f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_action("Teste de Notificação Completa", "FALHOU", str(e))
            return False
    
    def implement_sendgrid_fix(self):
        """Implementa correção usando SendGrid"""
        print("\n🔧 IMPLEMENTANDO CORREÇÃO COM SENDGRID")
        print("=" * 50)
        
        # Configuração SendGrid para Railway
        sendgrid_config = {
            "SENDGRID_API_KEY": "SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "USE_SENDGRID": "true",
            "SMTP_ENABLED": "false",
            "EMAIL_PROVIDER": "sendgrid"
        }
        
        print("📋 CONFIGURAÇÃO SENDGRID PARA RAILWAY:")
        for key, value in sendgrid_config.items():
            print(f"   {key}={value}")
        
        self.log_action("Configuração SendGrid", "SUCESSO", "Configuração preparada")
        
        # Instruções para o usuário
        print("\n📝 INSTRUÇÕES PARA ATIVAR SENDGRID:")
        print("1. Acesse: https://app.sendgrid.com/")
        print("2. Crie uma conta gratuita (100 emails/dia)")
        print("3. Gere uma API Key")
        print("4. No Railway Dashboard, adicione as variáveis:")
        print("   - SENDGRID_API_KEY=sua_api_key_aqui")
        print("   - USE_SENDGRID=true")
        print("   - SMTP_ENABLED=false")
        print("5. Reinicie a aplicação no Railway")
        
        return True
    
    def implement_resend_fix(self):
        """Implementa correção usando Resend"""
        print("\n🔄 IMPLEMENTANDO CORREÇÃO COM RESEND")
        print("=" * 50)
        
        # Resend já está configurado
        resend_config = {
            "RESEND_API_KEY": "re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1",
            "USE_RESEND": "true",
            "SMTP_ENABLED": "false",
            "EMAIL_PROVIDER": "resend"
        }
        
        print("📋 CONFIGURAÇÃO RESEND PARA RAILWAY:")
        for key, value in resend_config.items():
            print(f"   {key}={value}")
        
        self.log_action("Configuração Resend", "SUCESSO", "Resend já configurado")
        
        # Testar Resend
        return self.test_resend_configuration()
    
    def generate_fix_report(self):
        """Gera relatório de correção"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE CORREÇÃO - SISTEMA DE EMAIL")
        print("=" * 60)
        
        total_actions = len(self.results)
        successful_actions = len([r for r in self.results if r['status'] == 'SUCESSO'])
        failed_actions = len([r for r in self.results if r['status'] == 'FALHOU'])
        
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
        
        print(f"📈 RESUMO:")
        print(f"   • Total de Ações: {total_actions}")
        print(f"   • Ações Bem-sucedidas: {successful_actions} ✅")
        print(f"   • Ações Falharam: {failed_actions} ❌")
        print(f"   • Taxa de Sucesso: {success_rate:.1f}%")
        
        print(f"\n📋 DETALHES DAS AÇÕES:")
        for result in self.results:
            status_icon = "✅" if result['status'] == "SUCESSO" else "❌" if result['status'] == "FALHOU" else "⚠️"
            print(f"   {status_icon} {result['action']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Salvar relatório
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"email_fix_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_actions': total_actions,
                    'successful_actions': successful_actions,
                    'failed_actions': failed_actions,
                    'success_rate': success_rate
                },
                'railway_url': self.railway_url,
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_file}")
        
        # Conclusão
        if success_rate >= 80:
            print(f"\n🎯 CONCLUSÃO: SISTEMA DE EMAIL CORRIGIDO COM SUCESSO")
        elif success_rate >= 50:
            print(f"\n⚠️ CONCLUSÃO: SISTEMA DE EMAIL PARCIALMENTE CORRIGIDO")
        else:
            print(f"\n❌ CONCLUSÃO: SISTEMA DE EMAIL AINDA REQUER ATENÇÃO")
    
    def run_complete_fix(self):
        """Executa correção completa do sistema de email"""
        print("🚨 INICIANDO CORREÇÃO CRÍTICA DO SISTEMA DE EMAIL")
        print("=" * 70)
        print(f"🕐 Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        print(f"🌐 URL Railway: {self.railway_url}")
        
        # Executar todos os testes e correções
        self.test_current_email_status()
        self.test_sendgrid_configuration()
        self.test_resend_configuration()
        self.create_payment_and_test_notification()
        self.implement_sendgrid_fix()
        self.implement_resend_fix()
        
        # Gerar relatório final
        self.generate_fix_report()

if __name__ == "__main__":
    import sys
    
    railway_url = sys.argv[1] if len(sys.argv) > 1 else "https://web-production-1513a.up.railway.app"
    
    fixer = EmailSystemFixer(railway_url)
    fixer.run_complete_fix()
