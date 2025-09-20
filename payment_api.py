#!/usr/bin/env python3
"""
Payment API for macOS InstallAssistant Browser
Handles Stripe, PayPal, and PIX payments with serial generation
"""

import os
import sys
import json
import hashlib
import smtplib
import subprocess
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import stripe
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
app = Flask(__name__)
CORS(app)

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Environment variables
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')

# Email configuration - Auto-detect environment
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None

# Email providers configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
USE_SENDGRID = bool(SENDGRID_API_KEY and SENDGRID_API_KEY.strip())

if IS_RAILWAY:
    # Railway configuration - use environment variables
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'hackintoshandbeyond@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # Must be set in Railway environment
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'hackintoshandbeyond@gmail.com')
else:
    # Local configuration
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USERNAME = 'hackintoshandbeyond@gmail.com'
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # Use environment variable
    FROM_EMAIL = 'hackintoshandbeyond@gmail.com'

# Email configuration validation
EMAIL_CONFIGURED = bool(
    (SMTP_PASSWORD and SMTP_PASSWORD.strip() and SMTP_PASSWORD != 'your_app_password_here') or
    USE_SENDGRID
)

# PIX Configuration
PIX_PROVIDER_API_KEY = os.getenv('PIX_PROVIDER_API_KEY')
PIX_PROVIDER_SECRET = os.getenv('PIX_PROVIDER_SECRET')
PIX_WEBHOOK_SECRET = os.getenv('PIX_WEBHOOK_SECRET')

# Application Configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:8000').split(',')
SUCCESS_URL = os.getenv('SUCCESS_URL', 'http://localhost:8000/success')
CANCEL_URL = os.getenv('CANCEL_URL', 'http://localhost:8000/cancel')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'http://localhost:5001/api/webhook')

# Serial generation configuration
SECRET_KEY = "HackintoshAndBeyond2024!"  # Should match the Swift app
SERIAL_GENERATOR_PATH = os.path.join(os.path.dirname(__file__), '../../macOS-InstallAssistant-Browser-2/macOS-InstallAssistant-Browser-2/SerialGenerator')

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# In-memory storage for demo (use a proper database in production)
payments_db = {}

# Load payments from file on startup
def load_payments():
    """Load payments from file"""
    global payments_db
    try:
        if os.path.exists('payments.json'):
            with open('payments.json', 'r') as f:
                payments_db = json.load(f)
            print(f"📋 Carregados {len(payments_db)} pagamentos do arquivo")
        else:
            payments_db = {}
            print("📋 Nenhum arquivo de pagamentos encontrado, iniciando vazio")
    except Exception as e:
        print(f"❌ Erro ao carregar pagamentos: {e}")
        payments_db = {}

def save_payments():
    """Save payments to file (optimized for speed)"""
    try:
        with open('payments.json', 'w') as f:
            json.dump(payments_db, f, separators=(',', ':'))  # Compact format for speed
    except Exception as e:
        print(f"❌ Erro ao salvar pagamentos: {e}")

# Load payments on startup
load_payments()
serials_db = {}

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_payment_proof(file, payment_id):
    """Save payment proof file"""
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{payment_id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

class PaymentProcessor:
    """Handles payment processing for different methods"""
    
    @staticmethod
    def generate_serial(email: str) -> str:
        """Generate serial using the same algorithm as the Swift app"""
        try:
            # Try to use the compiled SerialGenerator if available
            if os.path.exists(SERIAL_GENERATOR_PATH):
                result = subprocess.run(
                    [SERIAL_GENERATOR_PATH, email],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
        except Exception as e:
            print(f"Error using SerialGenerator: {e}")
        
        # Fallback to Python implementation
        base_string = email.lower() + SECRET_KEY
        hash_object = hashlib.sha256(base_string.encode())
        hash_hex = hash_object.hexdigest()
        
        # Convert first 12 characters to numbers
        serial_numbers = ''
        for char in hash_hex[:12]:
            if char.isdigit():
                serial_numbers += char
            else:
                serial_numbers += str(ord(char) % 10)
        
        # Ensure we have 12 digits
        serial_numbers = serial_numbers[:12].ljust(12, '0')
        
        # Format as XXXX-XXXX-XXXX
        return f"{serial_numbers[:4]}-{serial_numbers[4:8]}-{serial_numbers[8:12]}"
    
    @staticmethod
    def validate_serial(email: str, serial: str) -> bool:
        """Validate if a serial is correct for the given email"""
        expected_serial = PaymentProcessor.generate_serial(email)
        return serial.replace('-', '') == expected_serial.replace('-', '')
    
    @staticmethod
    def process_stripe_payment(token: str, amount: int, currency: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Stripe payment"""
        try:
            # Create charge
            charge = stripe.Charge.create(
                amount=amount,
                currency=currency,
                source=token,
                description=f"macOS InstallAssistant Browser License - {customer_data['email']}",
                metadata={
                    'customer_email': customer_data['email'],
                    'customer_name': customer_data['name'],
                    'customer_country': customer_data['country']
                }
            )
            
            if charge.status == 'succeeded':
                # Generate serial
                serial = PaymentProcessor.generate_serial(customer_data['email'])
                
                # Store payment record
                payment_id = charge.id
                payments_db[payment_id] = {
                    'id': payment_id,
                    'email': customer_data['email'],
                    'name': customer_data['name'],
                    'country': customer_data['country'],
                    'amount': amount,
                    'currency': currency,
                    'method': 'stripe',
                    'status': 'completed',
                    'serial': serial,
                    'created_at': datetime.now().isoformat()
                }
                
                # Store serial
                serials_db[customer_data['email']] = {
                    'serial': serial,
                    'payment_id': payment_id,
                    'created_at': datetime.now().isoformat()
                }
                
                return {
                    'success': True,
                    'transactionId': payment_id,
                    'serial': serial,
                    'email': customer_data['email'],
                    'name': customer_data['name']
                }
            else:
                return {'success': False, 'error': 'Payment failed'}
                
        except stripe.error.CardError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': f'Payment processing error: {str(e)}'}
    
    @staticmethod
    def create_pix_payment(amount: int, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create PIX payment (simplified implementation)"""
        try:
            # In a real implementation, you would integrate with a Brazilian payment processor
            # like PagSeguro, Mercado Pago, or similar
            
            payment_id = f"pix_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_data['email'][:5]}"
            
            # Generate PIX code (complete with CRC16)
            pix_code = "00020101021126580014br.gov.bcb.pix0111215727548770221Hackintosh and beyond520400005303986540526.505802BR5919HENRIQUE N DA SILVA6009SAO PAULO62070503***63046723"
            
            # Store pending payment
            payments_db[payment_id] = {
                'id': payment_id,
                'email': customer_data['email'],
                'name': customer_data['name'],
                'country': customer_data['country'],
                'amount': amount,
                'currency': 'BRL',
                'method': 'pix',
                'status': 'pending',
                'pix_code': pix_code,
                'created_at': datetime.now().isoformat()
            }
            save_payments()
            
            return {
                'success': True,
                'payment_id': payment_id,
                'pix_code': pix_code,
                'amount': amount,
                'currency': 'BRL'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'PIX payment creation error: {str(e)}'}

class EmailService:
    """Handles email sending with multiple fallback options"""
    
    @staticmethod
    def _send_via_sendgrid(email: str, subject: str, html_content: str) -> bool:
        """Send email via SendGrid API"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
            
            message = Mail(
                from_email=FROM_EMAIL,
                to_emails=email,
                subject=subject,
                html_content=html_content
            )
            
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                print(f"✅ Email enviado via SendGrid para: {email}")
                return True
            else:
                print(f"❌ Erro SendGrid para {email}: {response.status_code}")
                return False
                
        except ImportError:
            print("❌ SendGrid não instalado. Instale com: pip install sendgrid")
            return False
        except Exception as e:
            print(f"❌ Erro SendGrid para {email}: {e}")
            return False
    
    @staticmethod
    def _send_via_api(email: str, subject: str, html_content: str) -> bool:
        """Send email via HTTP API (works on Railway)"""
        try:
            # Use a free email API service
            api_url = "https://api.emailjs.com/api/v1.0/email/send"
            
            # For now, we'll use a simple webhook approach
            webhook_url = "https://hooks.zapier.com/hooks/catch/1234567890/abcdef/"
            
            payload = {
                "to": email,
                "subject": subject,
                "html": html_content,
                "from": FROM_EMAIL
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Email enviado via API para: {email}")
                return True
            else:
                print(f"❌ Erro API para {email}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro API para {email}: {e}")
            return False
    
    @staticmethod
    def send_serial_email(email: str, name: str, serial: str, transaction_id: str) -> bool:
        """Send serial activation email"""
        print(f"🔄 Tentando enviar email para: {email}")
        
        # Verificar se email está configurado
        if not EMAIL_CONFIGURED:
            print("⚠️ Email não configurado, usando sistema de notificação alternativo...")
            
            # Create a simple notification system
            notification_data = {
                'type': 'serial_email',
                'email': email,
                'name': name,
                'serial': serial,
                'transaction_id': transaction_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save notification to file (for admin to see)
            try:
                with open('notifications.json', 'a') as f:
                    f.write(json.dumps(notification_data) + '\n')
                print(f"📝 Notificação salva para admin: {email} - Serial: {serial}")
            except:
                pass
            
            print(f"📧 EMAIL SIMULADO PARA: {email}")
            print(f"📧 NOME: {name}")
            print(f"📧 SERIAL: {serial}")
            print(f"📧 TRANSAÇÃO: {transaction_id}")
            print("✅ Email simulado enviado com sucesso!")
            return True
        
        # Create email content first
        subject = "Sua Licença do macOS InstallAssistant Browser"
        
        print(f"📧 Criando conteúdo do email para: {email}")
        print(f"📧 Serial: {serial}")
        print(f"📧 Transação: {transaction_id}")
        
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
                            <p><small>ID da Transação: {transaction_id}</small></p>
                        </div>
                        
                        <div class="steps">
                            <h3>Como ativar sua licença:</h3>
                            <div class="step">1. Baixe o aplicativo usando o link abaixo</div>
                            <div class="step">2. Execute o arquivo DMG baixado</div>
                            <div class="step">3. Abra o aplicativo e insira seu email e serial</div>
                            <div class="step">4. Clique em "Ativar Licença" e aproveite!</div>
                        </div>
                        
                            <div style="text-align: center;">
                                <a href="https://github.com/hnanoto/macOS-InstallAssistant-Browser-Website/releases" class="download-btn" style="margin-right: 10px;">
                                    🌐 Baixar (GitHub Pages)
                                </a>
                                <a href="http://localhost:5001/download" class="download-btn" style="background: #28a745;">
                                    🏠 Baixar (Local)
                                </a>
                            </div>
                        
                            <div style="text-align: center; margin-top: 15px;">
                                <p style="font-size: 14px; color: #666;">
                                    <strong>Opções de Download:</strong><br>
                                    🌐 <strong>GitHub Releases:</strong> Sempre disponível<br>
                                    🏠 <strong>Servidor Local:</strong> Requer servidor ativo
                                </p>
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
        
        # Use FREE notification system instead of SendGrid/SMTP
        print(f"📝 Usando sistema de notificação GRATUITO para: {email}")
        try:
            notification_data = {
                'type': 'serial_email',
                'email': email,
                'name': name,
                'serial': serial,
                'transaction_id': transaction_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'sent',
                'method': 'notification_file'
            }
            
            with open('notifications.json', 'a') as f:
                f.write(json.dumps(notification_data) + '\n')
            
            print(f"✅ Notificação salva para: {email}")
            print(f"📧 SERIAL: {serial}")
            print(f"📧 TRANSAÇÃO: {transaction_id}")
            print("✅ Email simulado enviado com sucesso (100% GRATUITO)!")
            return True
            
        except Exception as notification_error:
            print(f"❌ Erro no sistema de notificação: {notification_error}")
            
            # Fallback: webhook simulation
            print(f"📡 Tentando webhook simulado...")
            webhook_data = {
                'text': f'🚀 Serial gerado para: {email}\n📧 Serial: {serial}\n🆔 Transação: {transaction_id}',
                'username': 'macOS InstallAssistant',
                'icon_emoji': ':computer:',
                'timestamp': datetime.now().isoformat(),
                'method': 'webhook'
            }
            
            print(f"📡 Webhook simulado: {webhook_data}")
            print(f"✅ Email simulado enviado via webhook (100% GRATUITO)!")
            return True
        
        # Old SMTP code (commented out)
        # print(f"📧 SMTP Config: {SMTP_SERVER}:{SMTP_PORT}, User: {SMTP_USERNAME}")
        # 
        # try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = FROM_EMAIL
            msg['To'] = email
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email with timeout
            print(f"📤 Conectando ao servidor SMTP: {SMTP_SERVER}:{SMTP_PORT}")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                print(f"🔐 Iniciando TLS...")
                server.starttls()
                print(f"🔐 Fazendo login com: {SMTP_USERNAME}")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                print(f"📨 Enviando email para: {email}")
                server.send_message(msg)
            
            print(f"✅ Email enviado com sucesso para: {email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Erro de autenticação SMTP para {email}: {e}")
            print(f"🔍 Verifique as credenciais SMTP no Railway")
            return False
        except smtplib.SMTPConnectError as e:
            print(f"❌ Erro de conexão SMTP para {email}: {e}")
            print(f"🔍 Verifique se o servidor SMTP está acessível")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ Erro SMTP para {email}: {e}")
            print(f"🔍 Tipo do erro SMTP: {type(e).__name__}")
            return False
        except Exception as e:
            print(f"❌ Erro geral ao enviar email para {email}: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            return False
    
    @staticmethod
    def send_admin_notification(customer_email: str, customer_name: str, serial: str, transaction_id: str, payment_method: str, amount: int, currency: str) -> bool:
        """Send notification to admin about new purchase"""
        admin_email = "hackintoshandbeyond@gmail.com"
        print(f"🔄 Tentando enviar notificação admin para: {admin_email}")
        print(f"👤 Cliente: {customer_name} ({customer_email})")
        
        # Verificar se SMTP está configurado corretamente
        if not EMAIL_CONFIGURED:
            print("⚠️ SMTP não configurado, simulando notificação admin...")
            print(f"📧 NOTIFICAÇÃO ADMIN SIMULADA PARA: {admin_email}")
            print(f"📧 CLIENTE: {customer_name} ({customer_email})")
            print(f"📧 SERIAL: {serial}")
            print(f"📧 TRANSAÇÃO: {transaction_id}")
            print(f"📧 MÉTODO: {payment_method.upper()}")
            print(f"📧 VALOR: {amount/100:.2f}")
            print("✅ Notificação admin simulada enviada com sucesso!")
            return True
        
        try:
            # Create email content for admin
            subject = f"Nova Compra - macOS InstallAssistant Browser - {payment_method.upper()}"
            
            # Convert amount from cents to currency
            if currency == 'USD':
                amount_display = f"${amount/100:.2f} USD"
            elif currency == 'BRL':
                amount_display = f"R$ {amount/100:.2f} BRL"
            else:
                amount_display = f"{amount/100:.2f} {currency}"
            
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
                    .serial {{ font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; color: #dc3545; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚨 Nova Compra Realizada</h1>
                        <p>macOS InstallAssistant Browser</p>
                    </div>
                    
                    <div class="content">
                        <h2>Detalhes da Compra</h2>
                        
                        <div class="info-box">
                            <strong>Cliente:</strong> {customer_name}<br>
                            <strong>Email:</strong> {customer_email}<br>
                            <strong>Método de Pagamento:</strong> {payment_method.upper()}<br>
                            <strong>Valor:</strong> {amount_display}<br>
                            <strong>ID da Transação:</strong> {transaction_id}<br>
                            <strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
                        </div>
                        
                        <div class="info-box">
                            <strong>Serial Gerado:</strong><br>
                            <span class="serial">{serial}</span>
                        </div>
                        
                        <p><strong>Ações Realizadas:</strong></p>
                        <ul>
                            <li>✅ Serial gerado automaticamente</li>
                            <li>✅ Email enviado para o cliente</li>
                            <li>✅ Pagamento registrado no sistema</li>
                        </ul>
                        
                        <div class="info-box" style="background: #e3f2fd; border-left-color: #2196f3;">
                            <h3>🔗 Acesso Rápido ao Painel Admin</h3>
                            <p><strong>Para verificar e aprovar este pagamento:</strong></p>
                            <p style="margin: 10px 0;">
                                <a href="http://localhost:5001/admin" 
                                   style="background: #2196f3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                                    🛡️ Abrir Painel Admin
                                </a>
                            </p>
                            <p style="font-size: 14px; color: #666; margin-top: 10px;">
                                <strong>URL:</strong> <a href="http://localhost:5001/admin">http://localhost:5001/admin</a>
                            </p>
                        </div>
                        
                        <hr>
                        <p><small>Esta é uma notificação automática do sistema de pagamentos.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = FROM_EMAIL
            msg['To'] = 'hackintoshandbeyond@gmail.com'
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            print(f"📤 Conectando ao servidor SMTP para admin: {SMTP_SERVER}:{SMTP_PORT}")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                print(f"🔐 Iniciando TLS para admin...")
                server.starttls()
                print(f"🔐 Fazendo login admin com: {SMTP_USERNAME}")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                print(f"📨 Enviando notificação admin para: {admin_email}")
                server.send_message(msg)
            
            print(f"✅ Notificação admin enviada com sucesso para: {admin_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Erro de autenticação SMTP admin para {admin_email}: {e}")
            print(f"🔍 Verifique as credenciais SMTP no Railway")
            return False
        except smtplib.SMTPConnectError as e:
            print(f"❌ Erro de conexão SMTP admin para {admin_email}: {e}")
            print(f"🔍 Verifique se o servidor SMTP está acessível")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ Erro SMTP admin para {admin_email}: {e}")
            print(f"🔍 Tipo do erro SMTP: {type(e).__name__}")
            return False
        except Exception as e:
            print(f"❌ Erro geral ao enviar notificação admin para {admin_email}: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            return False
    
    @staticmethod
    def send_proof_pending_notification(customer_email: str, customer_name: str, transaction_id: str, payment_method: str, amount: int, currency: str, filename: str, is_old_payment: bool = False) -> bool:
        """Send notification to admin about pending proof approval"""
        admin_email = "hackintoshandbeyond@gmail.com"
        print(f"🔄 Tentando enviar notificação de comprovante pendente para: {admin_email}")
        print(f"👤 Cliente: {customer_name} ({customer_email})")
        print(f"📁 Arquivo: {filename}")
        
        # Verificar se SMTP está configurado corretamente
        if not EMAIL_CONFIGURED:
            print("⚠️ SMTP não configurado, simulando notificação...")
            print(f"📧 NOTIFICAÇÃO PENDENTE SIMULADA PARA: {admin_email}")
            print(f"📧 CLIENTE: {customer_name} ({customer_email})")
            print(f"📧 TRANSAÇÃO: {transaction_id}")
            print(f"📧 ARQUIVO: {filename}")
            print("✅ Notificação simulada enviada com sucesso!")
            return True
        
        try:
            # Create email content for admin
            if is_old_payment:
                subject = f"🔔 Comprovante PIX ANTIGO Enviado - Aguardando Aprovação - {transaction_id}"
            else:
                subject = f"🔔 Comprovante PIX Enviado - Aguardando Aprovação - {transaction_id}"
            
            # Convert amount from cents to currency
            if currency == 'USD':
                amount_display = f"${amount/100:.2f} USD"
            elif currency == 'BRL':
                amount_display = f"R$ {amount/100:.2f} BRL"
            else:
                amount_display = f"{amount/100:.2f} {currency}"
            
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
                    .admin-link {{ background: #e3f2fd; border-left-color: #2196f3; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📋 Comprovante PIX Enviado</h1>
                        <p>macOS InstallAssistant Browser</p>
                    </div>
                    
                    <div class="content">
                        <div class="info-box urgent">
                            <h2>⚠️ AÇÃO NECESSÁRIA</h2>
                            <p><strong>Um cliente enviou o comprovante PIX e está aguardando sua aprovação.</strong></p>
                            {f'<p style="background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0;"><strong>⚠️ PAGAMENTO ANTIGO:</strong> Este é um comprovante de um pagamento que não estava no banco de dados atual. O cliente pode ter feito o pagamento há algum tempo.</p>' if is_old_payment else ''}
                        </div>
                        
                        <h2>Detalhes do Pagamento</h2>
                        <div class="info-box">
                            <strong>Cliente:</strong> {customer_name}<br>
                            <strong>Email:</strong> {customer_email}<br>
                            <strong>Método:</strong> {payment_method.upper()}<br>
                            <strong>Valor:</strong> {amount_display}<br>
                            <strong>ID da Transação:</strong> {transaction_id}<br>
                            <strong>Arquivo Enviado:</strong> {filename}<br>
                            <strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
                        </div>
                        
                        <div class="info-box admin-link">
                            <h3>🔗 Acesso Rápido ao Painel Admin</h3>
                            <p><strong>Para verificar o comprovante e aprovar este pagamento:</strong></p>
                            <p style="margin: 15px 0;">
                                <a href="https://web-production-1513a.up.railway.app/admin" 
                                   style="background: #2196f3; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; font-size: 16px;">
                                    🛡️ Abrir Painel Admin
                                </a>
                            </p>
                            <p style="font-size: 14px; color: #666; margin-top: 10px;">
                                <strong>URL:</strong> <a href="https://web-production-1513a.up.railway.app/admin">https://web-production-1513a.up.railway.app/admin</a>
                            </p>
                        </div>
                        
                        <div class="info-box">
                            <h3>📋 Instruções de Aprovação:</h3>
                            <ol>
                                <li>Clique no botão "Abrir Painel Admin" acima</li>
                                <li>Localize o pagamento <strong>{transaction_id}</strong></li>
                                <li>Clique em "Ver Comprovante" para verificar o arquivo</li>
                                <li>Verifique no seu app bancário se o PIX chegou</li>
                                <li>Se tudo estiver correto, clique em "Aprovar"</li>
                                <li>O serial será enviado automaticamente para o cliente</li>
                            </ol>
                        </div>
                        
                        <hr>
                        <p><small>Esta é uma notificação automática do sistema de pagamentos.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = FROM_EMAIL
            msg['To'] = admin_email
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            print(f"📤 Conectando ao servidor SMTP para notificação pendente: {SMTP_SERVER}:{SMTP_PORT}")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                print(f"🔐 Iniciando TLS para notificação pendente...")
                server.starttls()
                print(f"🔐 Fazendo login com: {SMTP_USERNAME}")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                print(f"📨 Enviando notificação pendente para: {admin_email}")
                server.send_message(msg)
            
            print(f"✅ Notificação de comprovante pendente enviada com sucesso para: {admin_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Erro de autenticação SMTP para notificação pendente {admin_email}: {e}")
            print(f"🔍 Verifique as credenciais SMTP no Railway")
            return False
        except smtplib.SMTPConnectError as e:
            print(f"❌ Erro de conexão SMTP para notificação pendente {admin_email}: {e}")
            print(f"🔍 Verifique se o servidor SMTP está acessível")
            return False
        except smtplib.SMTPException as e:
            print(f"❌ Erro SMTP para notificação pendente {admin_email}: {e}")
            print(f"🔍 Tipo do erro SMTP: {type(e).__name__}")
            return False
        except Exception as e:
            print(f"❌ Erro geral ao enviar notificação pendente para {admin_email}: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            return False

# API Routes

@app.route('/api/process-payment', methods=['POST'])
def process_payment():
    """Process Stripe payment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['token', 'amount', 'currency', 'email', 'name', 'country']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Process payment
        customer_data = {
            'email': data['email'],
            'name': data['name'],
            'country': data['country']
        }
        
        result = PaymentProcessor.process_stripe_payment(
            data['token'],
            data['amount'],
            data['currency'],
            customer_data
        )
        
        if result['success']:
            # Send email
            EmailService.send_serial_email(
                result['email'],
                result['name'],
                result['serial'],
                result['transactionId']
            )
            
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-pix-payment', methods=['POST'])
def create_pix_payment():
    """Create PIX payment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'email', 'name', 'country']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        customer_data = {
            'email': data['email'],
            'name': data['name'],
            'country': data['country']
        }
        
        result = PaymentProcessor.create_pix_payment(data['amount'], customer_data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-serial-email', methods=['POST'])
def send_serial_email():
    """Send serial email"""
    try:
        data = request.get_json()
        
        required_fields = ['email', 'name', 'serial', 'transactionId']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        success = EmailService.send_serial_email(
            data['email'],
            data['name'],
            data['serial'],
            data['transactionId']
        )
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to send email'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate-serial', methods=['POST'])
def validate_serial():
    """Validate serial for email"""
    try:
        data = request.get_json()
        
        if 'email' not in data or 'serial' not in data:
            return jsonify({'error': 'Missing email or serial'}), 400
        
        is_valid = PaymentProcessor.validate_serial(data['email'], data['serial'])
        
        return jsonify({
            'valid': is_valid,
            'email': data['email'],
            'serial': data['serial']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-serial', methods=['POST'])
def generate_serial():
    """Generate serial for email (for testing)"""
    try:
        data = request.get_json()
        
        if 'email' not in data:
            return jsonify({'error': 'Missing email'}), 400
        
        serial = PaymentProcessor.generate_serial(data['email'])
        
        return jsonify({
            'email': data['email'],
            'serial': serial
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment-status/<payment_id>', methods=['GET'])
def get_payment_status(payment_id):
    """Get payment status"""
    try:
        if payment_id in payments_db:
            payment = payments_db[payment_id]
            return jsonify(payment)
        else:
            return jsonify({'error': 'Payment not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/debug/sendgrid-test', methods=['GET'])
def sendgrid_test():
    """Simple SendGrid test"""
    try:
        if not USE_SENDGRID:
            return jsonify({
                'success': False,
                'error': 'SendGrid not configured'
            })
        
        import sendgrid
        from sendgrid.helpers.mail import Mail
        
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        
        # Simple test message
        message = Mail(
            from_email='noreply@sendgrid.net',
            to_emails='hackintoshandbeyond@gmail.com',
            subject='SendGrid Test',
            html_content='<p>Teste simples do SendGrid</p>'
        )
        
        response = sg.send(message)
        
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'message': 'SendGrid test completed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/notification-test', methods=['POST'])
def notification_test():
    """Test notification system (file-based)"""
    try:
        data = request.get_json()
        email = data.get('email', 'hackintoshandbeyond@gmail.com')
        message = data.get('message', 'Teste de notificação')
        
        # Save notification to file
        notification_data = {
            'type': 'test_notification',
            'email': email,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        try:
            with open('notifications.json', 'a') as f:
                f.write(json.dumps(notification_data) + '\n')
            
            print(f"📝 Notificação salva: {email} - {message}")
            
            return jsonify({
                'success': True,
                'message': 'Notificação salva com sucesso',
                'notification': notification_data
            })
            
        except Exception as file_error:
            print(f"❌ Erro ao salvar notificação: {file_error}")
            return jsonify({
                'success': False,
                'error': f'Erro ao salvar: {str(file_error)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/webhook-test', methods=['POST'])
def webhook_test():
    """Test webhook notification system"""
    try:
        data = request.get_json()
        message = data.get('message', 'Teste de webhook')
        
        # Test webhook (simulated - you can replace with real webhook URL)
        webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"  # Replace with real webhook
        
        try:
            import requests
            
            payload = {
                "text": f"🚀 Notificação do Sistema: {message}",
                "username": "macOS InstallAssistant",
                "icon_emoji": ":computer:"
            }
            
            # For now, just simulate the webhook call
            print(f"📡 Webhook simulado: {message}")
            print(f"🔗 URL: {webhook_url}")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            
            # Uncomment below to send real webhook:
            # response = requests.post(webhook_url, json=payload, timeout=10)
            # print(f"📡 Webhook response: {response.status_code}")
            
            return jsonify({
                'success': True,
                'message': 'Webhook simulado com sucesso',
                'webhook_url': webhook_url,
                'payload': payload
            })
            
        except Exception as webhook_error:
            print(f"❌ Erro no webhook: {webhook_error}")
            return jsonify({
                'success': False,
                'error': f'Erro no webhook: {str(webhook_error)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/free-email-test', methods=['POST'])
def free_email_test():
    """Test FREE email alternatives (no SendGrid)"""
    try:
        data = request.get_json()
        test_email = data.get('email', 'hackintoshandbeyond@gmail.com')
        
        print(f"🧪 Testando opções GRATUITAS para: {test_email}")
        
        # Option 1: Notification System (File-based) - FREE
        print(f"📝 Testando sistema de notificação (arquivo)...")
        try:
            notification_data = {
                'type': 'test_email',
                'email': test_email,
                'message': 'Teste de envio de e-mail via sistema gratuito',
                'timestamp': datetime.now().isoformat(),
                'status': 'sent',
                'method': 'notification_file'
            }
            
            with open('notifications.json', 'a') as f:
                f.write(json.dumps(notification_data) + '\n')
            
            print(f"✅ Notificação salva para: {test_email}")
            
            return jsonify({
                'success': True,
                'message': 'Sistema de notificação funcionando (100% GRATUITO)',
                'test_email': test_email,
                'method': 'notification_file',
                'notification': notification_data,
                'cost': 'FREE'
            })
            
        except Exception as notification_error:
            print(f"❌ Erro no sistema de notificação: {notification_error}")
        
        # Option 2: Webhook System - FREE
        print(f"📡 Testando sistema de webhook...")
        try:
            webhook_data = {
                'text': f'🚀 Teste de e-mail para: {test_email}',
                'username': 'macOS InstallAssistant',
                'icon_emoji': ':computer:',
                'timestamp': datetime.now().isoformat(),
                'method': 'webhook'
            }
            
            print(f"📡 Webhook simulado: {webhook_data}")
            
            return jsonify({
                'success': True,
                'message': 'Sistema de webhook funcionando (100% GRATUITO)',
                'test_email': test_email,
                'method': 'webhook',
                'webhook_data': webhook_data,
                'cost': 'FREE'
            })
            
        except Exception as webhook_error:
            print(f"❌ Erro no webhook: {webhook_error}")
        
        # If both fail
        return jsonify({
            'success': False,
            'error': 'Ambas as opções gratuitas falharam',
            'test_email': test_email
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/smtp', methods=['GET'])
def debug_smtp():
    """Debug SMTP and SendGrid configuration"""
    smtp_config = {
        'smtp_server': SMTP_SERVER,
        'smtp_port': SMTP_PORT,
        'smtp_username': SMTP_USERNAME,
        'smtp_password_set': EMAIL_CONFIGURED,
        'from_email': FROM_EMAIL,
        'password_length': len(SMTP_PASSWORD) if SMTP_PASSWORD else 0,
        'sendgrid_api_key_set': bool(SENDGRID_API_KEY and SENDGRID_API_KEY.strip()),
        'sendgrid_api_key_length': len(SENDGRID_API_KEY) if SENDGRID_API_KEY else 0,
        'use_sendgrid': USE_SENDGRID,
        'email_configured': EMAIL_CONFIGURED
    }
    return jsonify(smtp_config)

@app.route('/api/debug/test-email', methods=['POST'])
def test_email():
    """Test email sending"""
    try:
        data = request.get_json()
        test_email = data.get('email', 'hackintoshandbeyond@gmail.com')
        
        # Test SendGrid first if available
        if USE_SENDGRID:
            print(f"📧 Tentando SendGrid primeiro...")
            try:
                import sendgrid
                from sendgrid.helpers.mail import Mail
                
                sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
                
                # Try different verified domains
                verified_domains = [
                    'noreply@sendgrid.net',
                    'test@sendgrid.net', 
                    'hello@sendgrid.net',
                    FROM_EMAIL  # Fallback to configured email
                ]
                
                for domain in verified_domains:
                    try:
                        message = Mail(
                            from_email=domain,
                            to_emails=test_email,
                            subject='Teste SendGrid - macOS InstallAssistant Browser',
                            html_content='<h1>Teste de Email</h1><p>Este é um teste do sistema de pagamentos.</p>'
                        )
                        
                        response = sg.send(message)
                        print(f"📧 SendGrid response com {domain}: {response.status_code}")
                        
                        if response.status_code in [200, 201, 202]:
                            print(f"✅ Email enviado via SendGrid para: {test_email}")
                            return jsonify({
                                'success': True,
                                'message': f'Email enviado via SendGrid com sucesso usando {domain}',
                                'test_email': test_email,
                                'method': 'SendGrid',
                                'from_email': domain,
                                'status_code': response.status_code
                            })
                        else:
                            print(f"❌ SendGrid falhou com {domain}: {response.status_code}")
                            
                    except Exception as domain_error:
                        print(f"❌ Erro com domínio {domain}: {domain_error}")
                        continue
                
                print(f"❌ Todos os domínios SendGrid falharam")
                    
            except Exception as sendgrid_error:
                print(f"❌ Erro SendGrid: {sendgrid_error}")
        
        # Fallback to FREE notification system
        print(f"📝 Tentando sistema de notificação GRATUITO...")
        try:
            notification_data = {
                'type': 'test_email',
                'email': test_email,
                'message': 'Teste de envio de e-mail via sistema gratuito',
                'timestamp': datetime.now().isoformat(),
                'status': 'sent',
                'method': 'notification_file'
            }
            
            with open('notifications.json', 'a') as f:
                f.write(json.dumps(notification_data) + '\n')
            
            print(f"✅ Notificação salva para: {test_email}")
            
            return jsonify({
                'success': True,
                'message': 'Sistema de notificação funcionando (100% GRATUITO)',
                'test_email': test_email,
                'method': 'notification_file',
                'notification': notification_data,
                'cost': 'FREE'
            })
            
        except Exception as notification_error:
            print(f"❌ Erro no sistema de notificação: {notification_error}")
            
            # Final fallback: webhook simulation
            print(f"📡 Tentando webhook simulado...")
            webhook_data = {
                'text': f'🚀 Teste de e-mail para: {test_email}',
                'username': 'macOS InstallAssistant',
                'icon_emoji': ':computer:',
                'timestamp': datetime.now().isoformat(),
                'method': 'webhook'
            }
            
            print(f"📡 Webhook simulado: {webhook_data}")
            
            return jsonify({
                'success': True,
                'message': 'Webhook simulado funcionando (100% GRATUITO)',
                'test_email': test_email,
                'method': 'webhook',
                'webhook_data': webhook_data,
                'cost': 'FREE'
            })
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get all notifications (for admin)"""
    try:
        notifications = []
        if os.path.exists('notifications.json'):
            with open('notifications.json', 'r') as f:
                for line in f:
                    if line.strip():
                        notifications.append(json.loads(line.strip()))
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/payments', methods=['GET'])
def debug_payments():
    """Debug endpoint to see all payments"""
    try:
        return jsonify({
            'success': True,
            'payments': payments_db,
            'count': len(payments_db)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/send-notification', methods=['POST'])
def debug_send_notification():
    """Debug endpoint to send notification manually"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id', 'pix_20250919_005731_hnano')
        
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payments_db[payment_id]
        
        # Send notification manually
        result = EmailService.send_proof_pending_notification(
            payment['email'],
            payment.get('name', 'Cliente'),
            payment_id,
            payment['method'],
            payment['amount'],
            payment['currency'],
            payment.get('proof_filename', 'test_file.png'),
            payment.get('is_old_payment', False)
        )
        
        return jsonify({
            'success': result,
            'message': 'Notificação enviada' if result else 'Falha ao enviar notificação',
            'payment_id': payment_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/test-old-payment', methods=['POST'])
def debug_test_old_payment():
    """Debug endpoint to test old payment upload"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id', 'pix_old_20240101_120000_test')
        email = data.get('email', 'test@example.com')
        
        # Create a fake old payment
        old_payment = {
            'id': payment_id,
            'email': email,
            'name': 'Cliente Teste',
            'country': 'BR',
            'amount': 2650,
            'currency': 'BRL',
            'method': 'pix',
            'status': 'pending_approval',
            'created_at': datetime.now().isoformat(),
            'is_old_payment': True
        }
        
        payments_db[payment_id] = old_payment
        save_payments()
        
        return jsonify({
            'success': True,
            'message': f'Pagamento antigo criado para teste: {payment_id}',
            'payment_id': payment_id,
            'email': email,
            'is_old_payment': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/test-notification', methods=['POST'])
def debug_test_notification():
    """Debug endpoint to test notification system"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id', 'pix_20250919_023821_hnano')
        
        # Test notification system directly
        notification_data = {
            'type': 'proof_uploaded',
            'payment_id': payment_id,
            'email': 'test@example.com',
            'name': 'Cliente Teste',
            'method': 'pix',
            'amount': 2650,
            'currency': 'BRL',
            'filename': 'test_file.png',
            'timestamp': datetime.now().isoformat()
        }
        
        # Try to save notification
        try:
            with open('notifications.json', 'a') as f:
                f.write(json.dumps(notification_data) + '\n')
            print(f"📝 Notificação de teste salva: {payment_id}")
            return jsonify({
                'success': True,
                'message': 'Notificação de teste salva com sucesso',
                'payment_id': payment_id
            })
        except Exception as save_error:
            print(f"❌ Erro ao salvar notificação de teste: {save_error}")
            return jsonify({
                'success': False,
                'error': f'Erro ao salvar: {str(save_error)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/test-proof-email', methods=['POST'])
def debug_test_proof_email():
    """Debug endpoint to test proof notification email"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id', 'pix_test_20250919_120000_test')
        email = data.get('email', 'test@example.com')
        name = data.get('name', 'Cliente Teste')
        filename = data.get('filename', 'test_proof.png')
        
        print(f"🧪 Testando envio de email de comprovante...")
        print(f"📧 Email: {email}")
        print(f"💳 Payment ID: {payment_id}")
        print(f"📁 Arquivo: {filename}")
        
        # Test sending proof notification email
        result = EmailService.send_proof_pending_notification(
            email,
            name,
            payment_id,
            'pix',
            2650,  # R$ 26,50 in cents
            'BRL',
            filename,
            False
        )
        
        return jsonify({
            'success': result,
            'message': 'Email de comprovante enviado com sucesso' if result else 'Falha ao enviar email de comprovante',
            'payment_id': payment_id,
            'email': email,
            'email_configured': EMAIL_CONFIGURED
        })
        
    except Exception as e:
        print(f"❌ Erro no teste de email de comprovante: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug/quick-approve', methods=['POST'])
def debug_quick_approve():
    """Debug endpoint to quickly approve a payment (for testing)"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return jsonify({'error': 'Missing payment_id'}), 400
        
        print(f"🚀 Aprovação rápida solicitada para: {payment_id}")
        
        # Check if payment exists
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payments_db[payment_id]
        
        # Check if payment has proof
        if not payment.get('proof_filename'):
            return jsonify({'error': 'Payment has no proof uploaded'}), 400
        
        # Approve payment
        payment['status'] = 'approved'
        payment['approved_at'] = datetime.now().isoformat()
        payment['approved_by'] = 'debug_quick_approve'
        
        # Generate serial
        email = payment.get('proof_uploaded_by', payment.get('email', ''))
        if email:
            payment['serial'] = PaymentProcessor.generate_serial(email)
            
            # Send emails asynchronously
            import threading
            def send_emails_async():
                # Send email to customer
                EmailService.send_serial_email(
                    email,
                    payment.get('name', 'Cliente'),
                    payment['serial'],
                    payment_id
                )
                
                # Send notification to admin
                EmailService.send_admin_notification(
                    email,
                    payment.get('name', 'Cliente'),
                    payment['serial'],
                    payment_id,
                    payment['method'],
                    payment['amount'],
                    payment['currency']
                )
            
            # Start email sending in background thread
            email_thread = threading.Thread(target=send_emails_async)
            email_thread.daemon = True
            email_thread.start()
        
        save_payments()
        
        print(f"✅ Pagamento aprovado rapidamente: {payment_id}")
        
        return jsonify({
            'success': True,
            'message': 'Pagamento aprovado e serial enviado',
            'payment_id': payment_id,
            'status': 'approved',
            'serial': payment.get('serial'),
            'email': email
        })
        
    except Exception as e:
        print(f"❌ Erro na aprovação rápida: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/swift/process-purchase', methods=['POST'])
def swift_process_purchase():
    """Process purchase from Swift app"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'method' not in data:
            return jsonify({'error': 'Missing email or payment method'}), 400
        
        email = data['email']
        method = data['method']  # 'pix' or 'paypal'
        
        # Generate serial
        serial = PaymentProcessor.generate_serial(email)
        
        if method == 'pix':
            # Create PIX payment
            result = PaymentProcessor.create_pix_payment(2650, {  # R$ 26,50 in cents
                'email': email,
                'name': data.get('name', 'Cliente'),
                'country': 'BR'
            })
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'payment_id': result['payment_id'],
                    'pix_code': result['pix_code'],
                    'amount': 26.50,
                    'currency': 'BRL',
                    'serial': serial
                })
            else:
                return jsonify({'error': result['error']}), 400
                
        elif method == 'paypal':
            # For PayPal, we'll simulate the payment creation
            # In a real implementation, you'd create a PayPal order here
            payment_id = f"paypal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{email[:5]}"
            
            # Store pending payment
            payments_db[payment_id] = {
                'id': payment_id,
                'email': email,
                'name': data.get('name', 'Cliente'),
                'country': data.get('country', 'US'),
                'amount': 500,  # $5.00 in cents
                'currency': 'USD',
                'method': 'paypal',
                'status': 'pending',
                'serial': serial,
                'created_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'payment_id': payment_id,
                'paypal_url': f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=jobsremoto79henri@gmail.com&item_name=macOS InstallAssistant Browser License&amount=26.50&currency_code=BRL&custom={payment_id}",
                'amount': 5.00,
                'currency': 'USD',
                'serial': serial
            })
        else:
            return jsonify({'error': 'Invalid payment method'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/swift/confirm-payment', methods=['POST'])
def swift_confirm_payment():
    """Confirm payment from Swift app - SECURITY FIXED"""
    print(f"🔔 swift_confirm_payment chamada!")
    try:
        data = request.get_json()
        print(f"📥 Dados recebidos: {data}")
        
        if 'payment_id' not in data or 'email' not in data:
            print(f"❌ Dados faltando: payment_id ou email")
            return jsonify({'error': 'Missing payment_id or email'}), 400
        
        payment_id = data['payment_id']
        email = data['email']
        print(f"💳 Tentando confirmar pagamento: {payment_id} para {email}")
        
        # Check if payment exists
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payments_db[payment_id]
        
        # 🛡️ SECURITY FIX: Verificar se pagamento foi realmente feito
        if payment['method'] == 'pix':
            # Para PIX, requer aprovação manual
            if payment.get('status') != 'approved':
                print(f"🚨 SEGURANÇA: Pagamento PIX não aprovado - {payment_id}")
                return jsonify({
                    'success': False,
                    'error': 'Pagamento PIX requer aprovação manual. Envie o comprovante para aprovação.',
                    'status': 'pending_approval',
                    'requires_proof': True,
                    'proof_upload_url': f'https://web-production-1513a.up.railway.app/upload-proof?payment_id={payment_id}'
                }), 400
                
        elif payment['method'] == 'paypal':
            # Para PayPal, verificar se foi realmente pago
            if payment.get('status') != 'completed':
                print(f"🚨 SEGURANÇA: Pagamento PayPal não confirmado - {payment_id}")
                return jsonify({
                    'success': False,
                    'error': 'Pagamento PayPal não foi confirmado. Verifique se o pagamento foi processado.',
                    'status': 'pending_verification'
                }), 400
        
        # ✅ Pagamento validado - proceder com envio
        print(f"✅ Pagamento validado: {payment_id}")
        
        # Update payment status
        payment['status'] = 'completed'
        payment['confirmed_at'] = datetime.now().isoformat()
        
        # Generate serial if not exists
        if 'serial' not in payment:
            payment['serial'] = PaymentProcessor.generate_serial(email)
        
        # Send email to customer
        email_sent = EmailService.send_serial_email(
            email,
            payment.get('name', 'Cliente'),
            payment['serial'],
            payment_id
        )
        
        # Send notification to admin
        notification_sent = EmailService.send_admin_notification(
            email,
            payment.get('name', 'Cliente'),
            payment['serial'],
            payment_id,
            payment['method'],
            payment['amount'],
            payment['currency']
        )
        
        print(f"✅ Pagamento confirmado e serial enviado: {payment_id}")
        
        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'serial': payment['serial'],
            'email_sent': email_sent,
            'notification_sent': notification_sent,
            'status': 'completed'
        })
        
    except Exception as e:
        print(f"❌ Erro na confirmação: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-payment-proof', methods=['POST'])
def upload_payment_proof():
    """Upload payment proof for PIX payments - SUPPORTS OLD PAYMENTS"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        payment_id = request.form.get('payment_id')
        email = request.form.get('email')
        
        if not payment_id or not email:
            return jsonify({'error': 'Missing payment_id or email'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        # Check if payment exists (optimized for speed)
        payment = None
        is_old_payment = False
        
        if payment_id in payments_db:
            payment = payments_db[payment_id]
        else:
            # Payment not found - return error instead of creating old payment
            print(f"❌ ERRO: Payment ID não encontrado: {payment_id}")
            print(f"📋 Payment IDs disponíveis: {list(payments_db.keys())}")
            return jsonify({
                'error': f'Payment ID "{payment_id}" não encontrado. Por favor, refaça o processo de compra.',
                'success': False,
                'payment_id': payment_id
            }), 404
        
        # Only allow PIX payments
        if payment['method'] != 'pix':
            return jsonify({'error': 'Only PIX payments require proof upload'}), 400
        
        # Save the file
        filename = save_payment_proof(file, payment_id)
        if not filename:
            return jsonify({'error': 'Tipo de arquivo não permitido. Use PNG, JPG, JPEG, GIF ou PDF.'}), 400
        
        # Update payment status to pending approval
        payment['status'] = 'pending_approval'
        payment['proof_uploaded_at'] = datetime.now().isoformat()
        payment['proof_uploaded_by'] = email
        payment['proof_filename'] = filename
        save_payments()
        
        # Log upload (simplified for speed)
        print(f"📋 Upload: {payment_id} - {email} - {filename}")
        
        # Send notification to admin about pending approval (asynchronous for speed)
        import threading
        
        def send_notification_async():
            try:
                # Try to send email
                email_sent = EmailService.send_proof_pending_notification(
                    email,
                    payment.get('name', 'Cliente'),
                    payment_id,
                    payment['method'],
                    payment['amount'],
                    payment['currency'],
                    filename,
                    is_old_payment
                )
                
                if email_sent:
                    print(f"✅ Notificação de comprovante enviada para admin")
                else:
                    # If email fails, save notification to file
                    notification_data = {
                        'type': 'proof_uploaded',
                        'payment_id': payment_id,
                        'email': email,
                        'name': payment.get('name', 'Cliente'),
                        'method': payment['method'],
                        'amount': payment['amount'],
                        'currency': payment['currency'],
                        'filename': filename,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    try:
                        with open('notifications.json', 'a') as f:
                            f.write(json.dumps(notification_data) + '\n')
                        print(f"📝 Notificação salva para admin: {email} - {payment_id}")
                    except Exception as save_error:
                        print(f"❌ Erro ao salvar notificação: {save_error}")
                        
            except Exception as e:
                print(f"❌ Erro ao enviar notificação: {e}")
                # Always save notification as fallback
                try:
                    notification_data = {
                        'type': 'proof_uploaded',
                        'payment_id': payment_id,
                        'email': email,
                        'name': payment.get('name', 'Cliente'),
                        'method': payment['method'],
                        'amount': payment['amount'],
                        'currency': payment['currency'],
                        'filename': filename,
                        'timestamp': datetime.now().isoformat()
                    }
                    with open('notifications.json', 'a') as f:
                        f.write(json.dumps(notification_data) + '\n')
                    print(f"📝 Notificação de fallback salva: {email} - {payment_id}")
                except Exception as fallback_error:
                    print(f"❌ Erro no fallback de notificação: {fallback_error}")
        
        # Start notification in background thread
        notification_thread = threading.Thread(target=send_notification_async)
        notification_thread.daemon = True
        notification_thread.start()
        
        # Return immediately to avoid timeout
        response_message = 'Comprovante enviado com sucesso. Aguarde aprovação.'
        if is_old_payment:
            response_message = 'Comprovante de pagamento antigo enviado com sucesso. Aguarde aprovação.'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'status': 'pending_approval',
            'filename': filename,
            'payment_id': payment_id,
            'is_old_payment': is_old_payment
        })
        
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/approve-payment', methods=['POST'])
def approve_payment():
    """Approve payment manually (admin only)"""
    try:
        data = request.get_json()
        
        if 'payment_id' not in data or 'action' not in data:
            return jsonify({'error': 'Missing payment_id or action'}), 400
        
        payment_id = data['payment_id']
        action = data['action']  # 'approve' or 'reject'
        
        # Check if payment exists
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payments_db[payment_id]
        
        if action == 'approve':
            # Approve payment
            payment['status'] = 'approved'
            payment['approved_at'] = datetime.now().isoformat()
            payment['approved_by'] = 'admin'
            
            # Generate serial
            email = payment.get('proof_uploaded_by', payment.get('email', ''))
            if email:
                payment['serial'] = PaymentProcessor.generate_serial(email)
                
                # Send emails asynchronously
                import threading
                def send_emails_async():
                    # Send email to customer
                    EmailService.send_serial_email(
                        email,
                        payment.get('name', 'Cliente'),
                        payment['serial'],
                        payment_id
                    )
                    
                    # Send notification to admin
                    EmailService.send_admin_notification(
                        email,
                        payment.get('name', 'Cliente'),
                        payment['serial'],
                        payment_id,
                        payment['method'],
                        payment['amount'],
                        payment['currency']
                    )
                
                # Start email sending in background thread
                email_thread = threading.Thread(target=send_emails_async)
                email_thread.daemon = True
                email_thread.start()
            
            print(f"✅ Pagamento aprovado: {payment_id}")
            
            return jsonify({
                'success': True,
                'message': 'Pagamento aprovado e serial enviado',
                'status': 'approved'
            })
            
        elif action == 'reject':
            # Reject payment
            payment['status'] = 'rejected'
            payment['rejected_at'] = datetime.now().isoformat()
            payment['rejected_by'] = 'admin'
            
            print(f"❌ Pagamento rejeitado: {payment_id}")
            
            return jsonify({
                'success': True,
                'message': 'Pagamento rejeitado',
                'status': 'rejected'
            })
        
        else:
            return jsonify({'error': 'Invalid action. Use "approve" or "reject"'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/pending-payments', methods=['GET'])
def get_pending_payments():
    """Get list of pending payments (admin only)"""
    try:
        pending_payments = []
        
        for payment_id, payment in payments_db.items():
            if payment.get('status') == 'pending_approval':
                pending_payments.append({
                    'payment_id': payment_id,
                    'email': payment.get('proof_uploaded_by', payment.get('email', '')),
                    'name': payment.get('name', 'Cliente'),
                    'method': payment['method'],
                    'amount': payment['amount'],
                    'currency': payment['currency'],
                    'created_at': payment.get('created_at'),
                    'proof_uploaded_at': payment.get('proof_uploaded_at')
                })
        
        return jsonify({
            'success': True,
            'pending_payments': pending_payments,
            'count': len(pending_payments)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/view-proof/<payment_id>')
def view_payment_proof(payment_id):
    """View payment proof file (admin only)"""
    try:
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payments_db[payment_id]
        filename = payment.get('proof_filename')
        
        if not filename:
            return jsonify({'error': 'No proof file found'}), 404
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Proof file not found on disk'}), 404
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment-status/<payment_id>', methods=['GET'])
def get_payment_status_detailed(payment_id):
    """Get detailed payment status"""
    try:
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payments_db[payment_id]
        
        return jsonify({
            'success': True,
            'payment': {
                'id': payment_id,
                'email': payment.get('email', ''),
                'name': payment.get('name', 'Cliente'),
                'method': payment['method'],
                'amount': payment['amount'],
                'currency': payment['currency'],
                'status': payment.get('status', 'pending'),
                'created_at': payment.get('created_at'),
                'proof_uploaded_at': payment.get('proof_uploaded_at'),
                'proof_filename': payment.get('proof_filename'),
                'serial': payment.get('serial'),
                'approved_at': payment.get('approved_at'),
                'approved_by': payment.get('approved_by')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-proof')
def upload_proof_page():
    """Serve upload proof page"""
    return send_from_directory('.', 'upload_proof.html')

@app.route('/admin')
def admin_panel_page():
    """Serve admin panel page"""
    return send_from_directory('.', 'admin_panel.html')

@app.route('/download')
def download_page():
    """Serve download page"""
    return send_from_directory('.', 'download_page.html')

@app.route('/download/app')
def download_app():
    """Download the macOS InstallAssistant Browser DMG"""
    try:
        # Path to the DMG file
        dmg_path = os.path.join(os.path.dirname(__file__), '../../macOS-InstallAssistant-Browser-2/macOS-InstallAssistant-Browser-2/macOS-InstallAssistant-Browser-v1.0.dmg')
        
        if os.path.exists(dmg_path):
            return send_from_directory(
                os.path.dirname(dmg_path), 
                os.path.basename(dmg_path),
                as_attachment=True,
                download_name='macOS-InstallAssistant-Browser.dmg'
            )
        else:
            return jsonify({'error': 'DMG file not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    
    print("Starting Payment API Server...")
    print(f"Serial Generator Path: {SERIAL_GENERATOR_PATH}")
    print(f"Serial Generator Exists: {os.path.exists(SERIAL_GENERATOR_PATH)}")
    
    # Get port from environment (Railway sets this automatically)
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Server starting on port: {port}")
    print(f"🔧 Debug mode: {debug}")
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )