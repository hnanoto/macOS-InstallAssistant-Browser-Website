#!/usr/bin/env python3
"""
Sistema de Notificações Automáticas Avançado
Gerencia notificações para clientes e administradores
"""

import json
import smtplib
import threading
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationSystem:
    """Sistema avançado de notificações automáticas"""
    
    def __init__(self):
        self.notification_queue = []
        self.failed_notifications = []
        self.retry_attempts = 3
        self.retry_delay = 30  # segundos
        
        # Configurações de email
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', 'hackintoshandbeyond@gmail.com')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'hackintoshandbeyond@gmail.com')
        
        # Iniciar processador de notificações em background
        self._start_notification_processor()
    
    def _start_notification_processor(self):
        """Inicia processador de notificações em background"""
        def process_notifications():
            while True:
                try:
                    if self.notification_queue:
                        notification = self.notification_queue.pop(0)
                        self._process_notification(notification)
                    
                    # Processar notificações falhadas
                    if self.failed_notifications:
                        self._retry_failed_notifications()
                    
                    time.sleep(5)  # Verificar a cada 5 segundos
                    
                except Exception as e:
                    logger.error(f"❌ Erro no processador de notificações: {e}")
                    time.sleep(10)
        
        # Iniciar thread em background
        processor_thread = threading.Thread(target=process_notifications, daemon=True)
        processor_thread.start()
        logger.info("🚀 Processador de notificações iniciado")
    
    def send_payment_confirmation(self, payment_data: Dict[str, Any]) -> bool:
        """
        Envia confirmação de pagamento para cliente e admin
        """
        try:
            # Notificação para cliente
            customer_notification = {
                'type': 'payment_confirmation',
                'recipient': 'customer',
                'email': payment_data.get('email', ''),
                'name': payment_data.get('name', 'Cliente'),
                'payment_id': payment_data.get('payment_id', ''),
                'amount': payment_data.get('amount', 0),
                'currency': payment_data.get('currency', ''),
                'serial': payment_data.get('serial', ''),
                'timestamp': datetime.now().isoformat(),
                'priority': 'high'
            }
            
            # Notificação para admin
            admin_notification = {
                'type': 'payment_confirmation',
                'recipient': 'admin',
                'payment_id': payment_data.get('payment_id', ''),
                'customer_email': payment_data.get('email', ''),
                'customer_name': payment_data.get('name', 'Cliente'),
                'amount': payment_data.get('amount', 0),
                'currency': payment_data.get('currency', ''),
                'serial': payment_data.get('serial', ''),
                'method': payment_data.get('method', ''),
                'timestamp': datetime.now().isoformat(),
                'priority': 'high'
            }
            
            # Adicionar à fila
            self.notification_queue.append(customer_notification)
            self.notification_queue.append(admin_notification)
            
            logger.info(f"📧 Notificações de confirmação adicionadas à fila: {payment_data.get('payment_id', '')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar confirmação de pagamento: {e}")
            return False
    
    def send_payment_pending(self, payment_data: Dict[str, Any]) -> bool:
        """
        Envia notificação de pagamento pendente
        """
        try:
            # Notificação para admin sobre pagamento pendente
            admin_notification = {
                'type': 'payment_pending',
                'recipient': 'admin',
                'payment_id': payment_data.get('payment_id', ''),
                'customer_email': payment_data.get('email', ''),
                'customer_name': payment_data.get('name', 'Cliente'),
                'amount': payment_data.get('amount', 0),
                'currency': payment_data.get('currency', ''),
                'method': payment_data.get('method', ''),
                'proof_filename': payment_data.get('proof_filename', ''),
                'timestamp': datetime.now().isoformat(),
                'priority': 'urgent'
            }
            
            # Notificação para cliente sobre status
            customer_notification = {
                'type': 'payment_pending',
                'recipient': 'customer',
                'email': payment_data.get('email', ''),
                'name': payment_data.get('name', 'Cliente'),
                'payment_id': payment_data.get('payment_id', ''),
                'amount': payment_data.get('amount', 0),
                'currency': payment_data.get('currency', ''),
                'timestamp': datetime.now().isoformat(),
                'priority': 'medium'
            }
            
            # Adicionar à fila
            self.notification_queue.append(admin_notification)
            self.notification_queue.append(customer_notification)
            
            logger.info(f"📧 Notificações de pagamento pendente adicionadas à fila: {payment_data.get('payment_id', '')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação de pagamento pendente: {e}")
            return False
    
    def send_payment_approved(self, payment_data: Dict[str, Any]) -> bool:
        """
        Envia notificação de pagamento aprovado
        """
        try:
            # Notificação para cliente
            customer_notification = {
                'type': 'payment_approved',
                'recipient': 'customer',
                'email': payment_data.get('email', ''),
                'name': payment_data.get('name', 'Cliente'),
                'payment_id': payment_data.get('payment_id', ''),
                'serial': payment_data.get('serial', ''),
                'amount': payment_data.get('amount', 0),
                'currency': payment_data.get('currency', ''),
                'timestamp': datetime.now().isoformat(),
                'priority': 'high'
            }
            
            # Adicionar à fila
            self.notification_queue.append(customer_notification)
            
            logger.info(f"📧 Notificação de pagamento aprovado adicionada à fila: {payment_data.get('payment_id', '')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação de pagamento aprovado: {e}")
            return False
    
    def send_payment_rejected(self, payment_data: Dict[str, Any], reason: str = '') -> bool:
        """
        Envia notificação de pagamento rejeitado
        """
        try:
            # Notificação para cliente
            customer_notification = {
                'type': 'payment_rejected',
                'recipient': 'customer',
                'email': payment_data.get('email', ''),
                'name': payment_data.get('name', 'Cliente'),
                'payment_id': payment_data.get('payment_id', ''),
                'amount': payment_data.get('amount', 0),
                'currency': payment_data.get('currency', ''),
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'priority': 'high'
            }
            
            # Adicionar à fila
            self.notification_queue.append(customer_notification)
            
            logger.info(f"📧 Notificação de pagamento rejeitado adicionada à fila: {payment_data.get('payment_id', '')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação de pagamento rejeitado: {e}")
            return False
    
    def send_system_alert(self, alert_type: str, message: str, severity: str = 'medium') -> bool:
        """
        Envia alerta do sistema para admin
        """
        try:
            admin_notification = {
                'type': 'system_alert',
                'recipient': 'admin',
                'alert_type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'priority': 'high' if severity == 'critical' else 'medium'
            }
            
            # Adicionar à fila
            self.notification_queue.append(admin_notification)
            
            logger.info(f"🚨 Alerta do sistema adicionado à fila: {alert_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta do sistema: {e}")
            return False
    
    def _process_notification(self, notification: Dict[str, Any]) -> bool:
        """
        Processa uma notificação individual
        """
        try:
            notification_type = notification.get('type', '')
            recipient = notification.get('recipient', '')
            
            if notification_type == 'payment_confirmation':
                return self._send_payment_confirmation_email(notification)
            elif notification_type == 'payment_pending':
                return self._send_payment_pending_email(notification)
            elif notification_type == 'payment_approved':
                return self._send_payment_approved_email(notification)
            elif notification_type == 'payment_rejected':
                return self._send_payment_rejected_email(notification)
            elif notification_type == 'system_alert':
                return self._send_system_alert_email(notification)
            else:
                logger.warning(f"⚠️ Tipo de notificação desconhecido: {notification_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar notificação: {e}")
            return False
    
    def _send_payment_confirmation_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de confirmação de pagamento
        """
        try:
            recipient = notification.get('recipient', '')
            
            if recipient == 'customer':
                return self._send_customer_confirmation_email(notification)
            elif recipient == 'admin':
                return self._send_admin_confirmation_email(notification)
            else:
                logger.error(f"❌ Destinatário inválido: {recipient}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de confirmação: {e}")
            return False
    
    def _send_customer_confirmation_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de confirmação para cliente
        """
        try:
            email = notification.get('email', '')
            name = notification.get('name', 'Cliente')
            serial = notification.get('serial', '')
            payment_id = notification.get('payment_id', '')
            amount = notification.get('amount', 0)
            currency = notification.get('currency', '')
            
            # Converter amount para formato legível
            if currency == 'BRL':
                amount_display = f"R$ {amount/100:.2f}"
            elif currency == 'USD':
                amount_display = f"${amount/100:.2f}"
            else:
                amount_display = f"{amount/100:.2f} {currency}"
            
            subject = "🎉 Compra Confirmada - macOS InstallAssistant Browser"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .serial-box {{ background: white; border: 2px solid #667eea; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
                    .serial {{ font-family: 'Courier New', monospace; font-size: 24px; font-weight: bold; color: #667eea; letter-spacing: 2px; }}
                    .download-btn {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                    .steps {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                    .step {{ margin: 10px 0; padding: 10px; border-left: 4px solid #667eea; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Compra Confirmada!</h1>
                        <p>Obrigado por adquirir o macOS InstallAssistant Browser</p>
                    </div>
                    <div class="content">
                        <p>Olá <strong>{name}</strong>,</p>
                        <p>Sua compra foi processada com sucesso! Aqui estão os detalhes da sua licença:</p>
                        
                        <div class="serial-box">
                            <h3>Seu Serial de Ativação:</h3>
                            <div class="serial">{serial}</div>
                            <p><small>ID da Transação: {payment_id}</small></p>
                            <p><small>Valor Pago: {amount_display}</small></p>
                        </div>
                        
                        <div class="steps">
                            <h3>Como ativar sua licença:</h3>
                            <div class="step">1. Baixe o aplicativo usando o link abaixo</div>
                            <div class="step">2. Execute o arquivo DMG baixado</div>
                            <div class="step">3. Abra o aplicativo e insira seu email e serial</div>
                            <div class="step">4. Clique em "Ativar Licença" e aproveite!</div>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases" class="download-btn">
                                🌐 Baixar Aplicativo
                            </a>
                        </div>
                        
                        <p><strong>Recursos inclusos na sua licença:</strong></p>
                        <ul>
                            <li>✅ Downloads ilimitados de macOS</li>
                            <li>✅ Gerador de seriais integrado</li>
                            <li>✅ Verificação de integridade automática</li>
                            <li>✅ Suporte técnico premium</li>
                            <li>✅ Atualizações gratuitas</li>
                        </ul>
                        
                        <p>Se você tiver alguma dúvida, responda este email ou visite nosso site.</p>
                        
                        <p>Obrigado por escolher o Hackintosh and Beyond!</p>
                        
                        <hr>
                        <p><small>Este email foi enviado para {email}. Se você não fez esta compra, entre em contato conosco imediatamente.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de confirmação para cliente: {e}")
            return False
    
    def _send_admin_confirmation_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de confirmação para admin
        """
        try:
            admin_email = "hackintoshandbeyond@gmail.com"
            customer_email = notification.get('customer_email', '')
            customer_name = notification.get('customer_name', 'Cliente')
            payment_id = notification.get('payment_id', '')
            serial = notification.get('serial', '')
            amount = notification.get('amount', 0)
            currency = notification.get('currency', '')
            method = notification.get('method', '')
            
            # Converter amount para formato legível
            if currency == 'BRL':
                amount_display = f"R$ {amount/100:.2f}"
            elif currency == 'USD':
                amount_display = f"${amount/100:.2f}"
            else:
                amount_display = f"{amount/100:.2f} {currency}"
            
            subject = f"💰 Nova Venda - {method.upper()} - {amount_display}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background: white; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; }}
                    .serial {{ font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; color: #28a745; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>💰 Nova Venda Realizada</h1>
                        <p>macOS InstallAssistant Browser</p>
                    </div>
                    
                    <div class="content">
                        <h2>Detalhes da Venda</h2>
                        
                        <div class="info-box">
                            <strong>Cliente:</strong> {customer_name}<br>
                            <strong>Email:</strong> {customer_email}<br>
                            <strong>Método de Pagamento:</strong> {method.upper()}<br>
                            <strong>Valor:</strong> {amount_display}<br>
                            <strong>ID da Transação:</strong> {payment_id}<br>
                            <strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
                        </div>
                        
                        <div class="info-box">
                            <strong>Serial Gerado:</strong><br>
                            <span class="serial">{serial}</span>
                        </div>
                        
                        <p><strong>Ações Realizadas:</strong></p>
                        <ul>
                            <li>✅ Pagamento verificado e confirmado</li>
                            <li>✅ Serial gerado automaticamente</li>
                            <li>✅ Email enviado para o cliente</li>
                            <li>✅ Venda registrada no sistema</li>
                        </ul>
                        
                        <hr>
                        <p><small>Esta é uma notificação automática do sistema de pagamentos.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(admin_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de confirmação para admin: {e}")
            return False
    
    def _send_payment_pending_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de pagamento pendente
        """
        try:
            recipient = notification.get('recipient', '')
            
            if recipient == 'admin':
                return self._send_admin_pending_email(notification)
            elif recipient == 'customer':
                return self._send_customer_pending_email(notification)
            else:
                logger.error(f"❌ Destinatário inválido: {recipient}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de pagamento pendente: {e}")
            return False
    
    def _send_admin_pending_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de pagamento pendente para admin
        """
        try:
            admin_email = "hackintoshandbeyond@gmail.com"
            customer_email = notification.get('customer_email', '')
            customer_name = notification.get('customer_name', 'Cliente')
            payment_id = notification.get('payment_id', '')
            amount = notification.get('amount', 0)
            currency = notification.get('currency', '')
            method = notification.get('method', '')
            proof_filename = notification.get('proof_filename', '')
            
            # Converter amount para formato legível
            if currency == 'BRL':
                amount_display = f"R$ {amount/100:.2f}"
            elif currency == 'USD':
                amount_display = f"${amount/100:.2f}"
            else:
                amount_display = f"{amount/100:.2f} {currency}"
            
            subject = f"⏳ Pagamento Pendente - {method.upper()} - {amount_display}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background: white; border-left: 4px solid #ff9800; padding: 15px; margin: 15px 0; }}
                    .urgent {{ background: #fff3cd; border-left-color: #ffc107; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⏳ Pagamento Pendente</h1>
                        <p>macOS InstallAssistant Browser</p>
                    </div>
                    
                    <div class="content">
                        <div class="info-box urgent">
                            <h2>⚠️ AÇÃO NECESSÁRIA</h2>
                            <p><strong>Um cliente enviou comprovante de pagamento e está aguardando sua aprovação.</strong></p>
                        </div>
                        
                        <h2>Detalhes do Pagamento</h2>
                        <div class="info-box">
                            <strong>Cliente:</strong> {customer_name}<br>
                            <strong>Email:</strong> {customer_email}<br>
                            <strong>Método:</strong> {method.upper()}<br>
                            <strong>Valor:</strong> {amount_display}<br>
                            <strong>ID da Transação:</strong> {payment_id}<br>
                            <strong>Comprovante:</strong> {proof_filename}<br>
                            <strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
                        </div>
                        
                        <div class="info-box">
                            <h3>📋 Instruções de Aprovação:</h3>
                            <ol>
                                <li>Acesse o painel admin</li>
                                <li>Localize o pagamento <strong>{payment_id}</strong></li>
                                <li>Verifique o comprovante enviado</li>
                                <li>Confirme se o pagamento foi recebido</li>
                                <li>Aprove ou rejeite o pagamento</li>
                            </ol>
                        </div>
                        
                        <hr>
                        <p><small>Esta é uma notificação automática do sistema de pagamentos.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(admin_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de pagamento pendente para admin: {e}")
            return False
    
    def _send_customer_pending_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de pagamento pendente para cliente
        """
        try:
            email = notification.get('email', '')
            name = notification.get('name', 'Cliente')
            payment_id = notification.get('payment_id', '')
            amount = notification.get('amount', 0)
            currency = notification.get('currency', '')
            
            # Converter amount para formato legível
            if currency == 'BRL':
                amount_display = f"R$ {amount/100:.2f}"
            elif currency == 'USD':
                amount_display = f"${amount/100:.2f}"
            else:
                amount_display = f"{amount/100:.2f} {currency}"
            
            subject = "⏳ Pagamento em Análise - macOS InstallAssistant Browser"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #ff9800; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background: white; border-left: 4px solid #ff9800; padding: 15px; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⏳ Pagamento em Análise</h1>
                        <p>macOS InstallAssistant Browser</p>
                    </div>
                    
                    <div class="content">
                        <p>Olá <strong>{name}</strong>,</p>
                        <p>Recebemos seu comprovante de pagamento e estamos analisando. Você receberá uma notificação assim que a análise for concluída.</p>
                        
                        <div class="info-box">
                            <strong>ID da Transação:</strong> {payment_id}<br>
                            <strong>Valor:</strong> {amount_display}<br>
                            <strong>Status:</strong> Em análise<br>
                            <strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
                        </div>
                        
                        <p><strong>O que acontece agora:</strong></p>
                        <ul>
                            <li>✅ Seu comprovante foi recebido</li>
                            <li>⏳ Nossa equipe está analisando</li>
                            <li>📧 Você receberá o serial por email</li>
                            <li>🚀 Poderá ativar sua licença</li>
                        </ul>
                        
                        <p>O tempo de análise é normalmente de algumas horas. Se você tiver alguma dúvida, responda este email.</p>
                        
                        <p>Obrigado pela sua paciência!</p>
                        
                        <hr>
                        <p><small>Este email foi enviado para {email}.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de pagamento pendente para cliente: {e}")
            return False
    
    def _send_payment_approved_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de pagamento aprovado
        """
        try:
            email = notification.get('email', '')
            name = notification.get('name', 'Cliente')
            serial = notification.get('serial', '')
            payment_id = notification.get('payment_id', '')
            amount = notification.get('amount', 0)
            currency = notification.get('currency', '')
            
            # Converter amount para formato legível
            if currency == 'BRL':
                amount_display = f"R$ {amount/100:.2f}"
            elif currency == 'USD':
                amount_display = f"${amount/100:.2f}"
            else:
                amount_display = f"{amount/100:.2f} {currency}"
            
            subject = "✅ Pagamento Aprovado - macOS InstallAssistant Browser"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .serial-box {{ background: white; border: 2px solid #28a745; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
                    .serial {{ font-family: 'Courier New', monospace; font-size: 24px; font-weight: bold; color: #28a745; letter-spacing: 2px; }}
                    .download-btn {{ display: inline-block; background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Pagamento Aprovado!</h1>
                        <p>Seu serial está pronto</p>
                    </div>
                    
                    <div class="content">
                        <p>Olá <strong>{name}</strong>,</p>
                        <p>Ótimas notícias! Seu pagamento foi aprovado e seu serial de ativação está pronto.</p>
                        
                        <div class="serial-box">
                            <h3>Seu Serial de Ativação:</h3>
                            <div class="serial">{serial}</div>
                            <p><small>ID da Transação: {payment_id}</small></p>
                            <p><small>Valor Pago: {amount_display}</small></p>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases" class="download-btn">
                                🌐 Baixar Aplicativo
                            </a>
                        </div>
                        
                        <p><strong>Próximos passos:</strong></p>
                        <ol>
                            <li>Baixe o aplicativo usando o link acima</li>
                            <li>Execute o arquivo DMG</li>
                            <li>Use o serial para ativar sua licença</li>
                            <li>Aproveite todas as funcionalidades premium!</li>
                        </ol>
                        
                        <p>Obrigado por escolher o Hackintosh and Beyond!</p>
                        
                        <hr>
                        <p><small>Este email foi enviado para {email}.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de pagamento aprovado: {e}")
            return False
    
    def _send_payment_rejected_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de pagamento rejeitado
        """
        try:
            email = notification.get('email', '')
            name = notification.get('name', 'Cliente')
            payment_id = notification.get('payment_id', '')
            amount = notification.get('amount', 0)
            currency = notification.get('currency', '')
            reason = notification.get('reason', 'Não especificado')
            
            # Converter amount para formato legível
            if currency == 'BRL':
                amount_display = f"R$ {amount/100:.2f}"
            elif currency == 'USD':
                amount_display = f"${amount/100:.2f}"
            else:
                amount_display = f"{amount/100:.2f} {currency}"
            
            subject = "❌ Pagamento Rejeitado - macOS InstallAssistant Browser"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background: white; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>❌ Pagamento Rejeitado</h1>
                        <p>macOS InstallAssistant Browser</p>
                    </div>
                    
                    <div class="content">
                        <p>Olá <strong>{name}</strong>,</p>
                        <p>Infelizmente, seu pagamento foi rejeitado após análise. Aqui estão os detalhes:</p>
                        
                        <div class="info-box">
                            <strong>ID da Transação:</strong> {payment_id}<br>
                            <strong>Valor:</strong> {amount_display}<br>
                            <strong>Status:</strong> Rejeitado<br>
                            <strong>Motivo:</strong> {reason}<br>
                            <strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
                        </div>
                        
                        <p><strong>O que você pode fazer:</strong></p>
                        <ul>
                            <li>Verifique se o comprovante está legível</li>
                            <li>Confirme se o valor está correto</li>
                            <li>Entre em contato conosco para esclarecimentos</li>
                            <li>Refaça o processo de pagamento se necessário</li>
                        </ul>
                        
                        <p>Se você acredita que houve um erro, responda este email com mais detalhes.</p>
                        
                        <p>Obrigado pela sua compreensão!</p>
                        
                        <hr>
                        <p><small>Este email foi enviado para {email}.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(email, subject, html_content)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de pagamento rejeitado: {e}")
            return False
    
    def _send_system_alert_email(self, notification: Dict[str, Any]) -> bool:
        """
        Envia email de alerta do sistema
        """
        try:
            admin_email = "hackintoshandbeyond@gmail.com"
            alert_type = notification.get('alert_type', '')
            message = notification.get('message', '')
            severity = notification.get('severity', 'medium')
            
            # Definir cor baseada na severidade
            if severity == 'critical':
                color = '#dc3545'
                icon = '🚨'
            elif severity == 'high':
                color = '#fd7e14'
                icon = '⚠️'
            else:
                color = '#ffc107'
                icon = 'ℹ️'
            
            subject = f"{icon} Alerta do Sistema - {alert_type}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: {color}; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background: white; border-left: 4px solid {color}; padding: 15px; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{icon} Alerta do Sistema</h1>
                        <p>{alert_type}</p>
                    </div>
                    
                    <div class="content">
                        <div class="info-box">
                            <strong>Tipo:</strong> {alert_type}<br>
                            <strong>Severidade:</strong> {severity.upper()}<br>
                            <strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
                        </div>
                        
                        <h3>Mensagem:</h3>
                        <p>{message}</p>
                        
                        <hr>
                        <p><small>Este é um alerta automático do sistema de pagamentos.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(admin_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email de alerta do sistema: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Envia email usando SMTP
        """
        try:
            if not self.smtp_password:
                logger.warning("⚠️ SMTP não configurado, salvando notificação em arquivo")
                return self._save_notification_to_file(to_email, subject, html_content)
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Adicionar conteúdo HTML
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email enviado com sucesso para: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email para {to_email}: {e}")
            return self._save_notification_to_file(to_email, subject, html_content)
    
    def _save_notification_to_file(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Salva notificação em arquivo quando email falha
        """
        try:
            notification_data = {
                'to_email': to_email,
                'subject': subject,
                'html_content': html_content,
                'timestamp': datetime.now().isoformat(),
                'status': 'saved_to_file'
            }
            
            with open('notifications.json', 'a') as f:
                f.write(json.dumps(notification_data) + '\n')
            
            logger.info(f"📝 Notificação salva em arquivo para: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar notificação em arquivo: {e}")
            return False
    
    def _retry_failed_notifications(self):
        """
        Tenta reenviar notificações que falharam
        """
        try:
            retry_notifications = []
            
            for notification in self.failed_notifications:
                attempts = notification.get('attempts', 0)
                
                if attempts < self.retry_attempts:
                    # Tentar novamente
                    if self._process_notification(notification):
                        logger.info(f"✅ Notificação reenviada com sucesso: {notification.get('type', '')}")
                    else:
                        # Incrementar tentativas
                        notification['attempts'] = attempts + 1
                        retry_notifications.append(notification)
                else:
                    # Máximo de tentativas atingido
                    logger.error(f"❌ Notificação falhou após {self.retry_attempts} tentativas: {notification.get('type', '')}")
            
            # Atualizar lista de notificações falhadas
            self.failed_notifications = retry_notifications
            
        except Exception as e:
            logger.error(f"❌ Erro ao tentar reenviar notificações: {e}")
    
    def get_notification_status(self) -> Dict[str, Any]:
        """
        Obtém status do sistema de notificações
        """
        try:
            return {
                'success': True,
                'queue_size': len(self.notification_queue),
                'failed_notifications': len(self.failed_notifications),
                'smtp_configured': bool(self.smtp_password),
                'processor_running': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter status das notificações: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Instância global
notification_system = NotificationSystem()
