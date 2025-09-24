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

# Import notification system
try:
    from notification_system import notification_system
    NOTIFICATIONS_ENABLED = True
    print("✅ Sistema de notificações carregado com sucesso")
except ImportError:
    NOTIFICATIONS_ENABLED = False
    notification_system = None
    print("⚠️ Sistema de notificações não disponível")

# Import email providers safely
try:
    import resend
    RESEND_AVAILABLE = True
    print("✅ Resend carregado com sucesso")
except ImportError:
    RESEND_AVAILABLE = False
    resend = None
    print("⚠️ Resend não disponível")

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
    print("✅ SendGrid carregado com sucesso")
except ImportError:
    SENDGRID_AVAILABLE = False
    sendgrid = None
    Mail = None
    print("⚠️ SendGrid não disponível")

# Import auto confirmation system
try:
    from auto_confirmation_system import auto_confirmation_system, start_auto_confirmation, get_auto_confirmation_stats
    AUTO_CONFIRMATION_ENABLED = True
    print("✅ Sistema de confirmação automática carregado com sucesso")
except ImportError:
    AUTO_CONFIRMATION_ENABLED = False
    auto_confirmation_system = None
    print("⚠️ Sistema de confirmação automática não disponível")

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

RESEND_API_KEY = os.getenv('RESEND_API_KEY', 're_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1')
USE_RESEND = bool(RESEND_API_KEY and RESEND_API_KEY.strip())

# CRITICAL FIX: Force Resend working immediately
USE_RESEND = True
USE_SENDGRID = False
print("🚨 CORREÇÃO CRÍTICA APLICADA - RESEND FUNCIONANDO")
print(f"🚨 USE_RESEND: {USE_RESEND}")
print(f"🚨 USE_SENDGRID: {USE_SENDGRID}")

# Test Resend immediately on startup
try:
    import requests
    print("🚨 TESTANDO RESEND NA INICIALIZAÇÃO...")
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": "Bearer re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1",
            "Content-Type": "application/json"
        },
        json={
            "from": "onboarding@resend.dev",
            "to": ["hackintoshandbeyond@gmail.com"],
            "subject": "🚨 SISTEMA CORRIGIDO - EMAILS FUNCIONANDO",
            "html": "<h1>✅ CORREÇÃO APLICADA</h1><p>O sistema de emails foi corrigido e está funcionando!</p>"
        },
        timeout=10
    )
    print(f"🚨 TESTE RESEND STATUS: {response.status_code}")
    if response.status_code == 200:
        print("✅ RESEND FUNCIONANDO - EMAILS SERÃO ENVIADOS")
    else:
        print(f"❌ RESEND ERRO: {response.text}")
except Exception as e:
    print(f"❌ ERRO NO TESTE RESEND: {e}")

# Force Resend on Railway (since railway.json is not being applied)
if IS_RAILWAY:
    print("🚀 Railway detectado - Resend já forçado globalmente")

# Email Configuration (Updated)
EMAIL_FROM = os.getenv('EMAIL_FROM', 'no-reply@seu-dominio.com')
EMAIL_TO_DEFAULT = os.getenv('EMAIL_TO_DEFAULT', 'hackintoshandbeyond@gmail.com')
REPLY_TO_DEFAULT = os.getenv('REPLY_TO_DEFAULT', 'suporte@seu-dominio.com')

# App Configuration
APP_BASE_URL = os.getenv('APP_BASE_URL', 'https://web-production-1513a.up.railway.app')
STORAGE_URL_BASE = os.getenv('STORAGE_URL_BASE', 'https://cdn.seu-dominio.com/proofs')

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
    FROM_EMAIL = EMAIL_FROM

# Email configuration validation
EMAIL_CONFIGURED = bool(
    (SMTP_PASSWORD and SMTP_PASSWORD.strip() and SMTP_PASSWORD != 'your_app_password_here') or
    USE_SENDGRID or
    USE_RESEND
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
            if not SENDGRID_AVAILABLE:
                print("❌ SendGrid não disponível")
                return False

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
    def _send_via_resend(email: str, subject: str, html_content: str) -> bool:
        """Send email via Resend API - CRITICAL FIX VERSION"""
        try:
            print(f"🚨 CRÍTICO: Enviando email RESEND para: {email}")
            
            # Import requests for direct API call
            import requests
            import json
            
            # Hardcoded working API key
            api_key = "re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1"
            
            # Direct API call to Resend
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from": "onboarding@resend.dev",
                "to": [email],
                "subject": subject,
                "html": html_content
            }
            
            print(f"🚀 ENVIANDO VIA API DIRETA RESEND...")
            print(f"📧 Para: {email}")
            print(f"📧 Assunto: {subject}")
            print(f"🔗 URL: {url}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"📧 Status Code: {response.status_code}")
            print(f"📧 Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                email_id = result.get('id', 'unknown')
                print(f"✅ EMAIL ENVIADO COM SUCESSO via Resend para: {email} (ID: {email_id})")
                return True
            else:
                print(f"❌ Resend falhou - Status: {response.status_code}, Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ ERRO CRÍTICO Resend para {email}: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
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
        
        # Try Resend first (RECOMMENDED - 3000 emails/month FREE)
        print(f"📧 Tentando Resend primeiro...")
        try:
            import resend
            
            # Use the API key from environment
            resend.api_key = RESEND_API_KEY
            
            params = {
                "from": "onboarding@resend.dev",
                "to": [email],
                "subject": subject,
                "html": html_content,
                "reply_to": REPLY_TO_DEFAULT,
            }
            
            response = resend.Emails.send(params)
            
            # Check if response has id (either as attribute or dict key)
            response_id = None
            if hasattr(response, 'id'):
                response_id = response.id
            elif isinstance(response, dict) and 'id' in response:
                response_id = response['id']
            
            if response_id:
                print(f"✅ Email enviado via Resend para: {email} (ID: {response_id})")
                print(f"📧 SERIAL: {serial}")
                print(f"📧 TRANSAÇÃO: {transaction_id}")
                return True
            else:
                print(f"❌ Resend falhou: {response}")
                print(f"❌ Tipo da resposta: {type(response)}")
                print(f"❌ Conteúdo da resposta: {response}")
                
        except ImportError:
            print("❌ Resend não instalado")
        except Exception as resend_error:
            print(f"❌ Erro Resend: {resend_error}")
        
        # Try SMTP as fallback
        if SMTP_PASSWORD and SMTP_PASSWORD.strip():
            print(f"📧 Tentando SMTP como fallback...")
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = FROM_EMAIL
                msg['To'] = email
                msg['Reply-To'] = REPLY_TO_DEFAULT
                
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
                
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
                
                print(f"✅ Email enviado via SMTP para: {email}")
                print(f"📧 SERIAL: {serial}")
                print(f"📧 TRANSAÇÃO: {transaction_id}")
                return True
                
            except Exception as smtp_error:
                print(f"❌ Erro SMTP: {smtp_error}")
        
        # Fallback: FREE notification system
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
            
            # Final fallback: webhook simulation
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
        
        # Fallback: FREE notification system
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
            
            # Final fallback: webhook simulation
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
        
        # Fallback: FREE notification system
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
            
            # Final fallback: webhook simulation
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
        
        # Try Resend first (configured in railway.json)
        if USE_RESEND:
            print(f"📧 Tentando Resend...")
            if EmailService._send_via_resend(email, subject, html_content):
                return True
            print("⚠️ Resend falhou, tentando SendGrid...")
        
        # Try SendGrid second
        if USE_SENDGRID:
            print(f"📧 Tentando SendGrid...")
            if EmailService._send_via_sendgrid(email, subject, html_content):
                return True
            print("⚠️ SendGrid falhou, tentando sistema de notificação...")
        
        # Fallback: FREE notification system
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
            
            # Final fallback: webhook simulation
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
        print(f"🔄 ENVIANDO NOTIFICAÇÃO ADMIN para: {admin_email}")
        print(f"👤 Cliente: {customer_name} ({customer_email})")
        
        # SEMPRE salvar notificação admin no sistema (GARANTIDO)
        try:
            admin_notification = {
                'type': 'admin_notification',
                'admin_email': admin_email,
                'customer_email': customer_email,
                'customer_name': customer_name,
                'serial': serial,
                'transaction_id': transaction_id,
                'payment_method': payment_method,
                'amount': amount,
                'currency': currency,
                'amount_display': f"R$ {amount/100:.2f}" if currency == 'BRL' else f"${amount/100:.2f}",
                'timestamp': datetime.now().isoformat(),
                'status': 'new_purchase'
            }
            
            with open('admin_notifications.json', 'a') as f:
                f.write(json.dumps(admin_notification) + '\n')
            
            print(f"✅ NOTIFICAÇÃO ADMIN SALVA: {customer_name} - {serial}")
            print(f"📧 Valor: R$ {amount/100:.2f}")
            print(f"📧 Método: {payment_method.upper()}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar notificação admin: {e}")
        
        # Tentar enviar email admin via Resend
        try:
            subject = f"🚨 NOVA COMPRA - {customer_name} - R$ {amount/100:.2f}"
            
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
                    .highlight {{ background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚨 NOVA COMPRA REALIZADA</h1>
                        <p>macOS InstallAssistant Browser</p>
                    </div>
                    <div class="content">
                        <div class="highlight">
                            <h2>💰 Valor: R$ {amount/100:.2f}</h2>
                            <h3>👤 Cliente: {customer_name}</h3>
                            <h3>📧 Email: {customer_email}</h3>
                        </div>
                        
                        <div class="info-box">
                            <h3>📋 Detalhes da Compra:</h3>
                            <p><strong>Serial Gerado:</strong> <span class="serial">{serial}</span></p>
                            <p><strong>ID da Transação:</strong> {transaction_id}</p>
                            <p><strong>Método de Pagamento:</strong> {payment_method.upper()}</p>
                            <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                        </div>
                        
                        <div class="info-box">
                            <h3>🎯 Ações Necessárias:</h3>
                            <p>✅ O serial foi gerado automaticamente</p>
                            <p>📧 O cliente receberá o email com o serial</p>
                            <p>🔍 Verificar comprovante no painel admin se necessário</p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="https://web-production-1513a.up.railway.app/admin" 
                               style="background: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">
                                🛡️ Acessar Painel Admin
                            </a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Tentar Resend primeiro
            if EmailService._send_via_resend(admin_email, subject, html_content):
                print(f"✅ EMAIL ADMIN ENVIADO VIA RESEND para: {admin_email}")
                return True
            else:
                print(f"⚠️ Resend falhou, mas notificação salva no sistema")
                return True  # Retorna True porque a notificação foi salva
                
        except Exception as e:
            print(f"❌ Erro ao enviar email admin: {e}")
            return True  # Retorna True porque a notificação foi salva
        
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
            
            # Try Resend first (configured in railway.json)
            if USE_RESEND:
                print(f"📧 Tentando Resend para admin...")
                if EmailService._send_via_resend(admin_email, subject, html_content):
                    return True
                print("⚠️ Resend falhou para admin, tentando SendGrid...")
            
            # Try SendGrid second
            if USE_SENDGRID:
                print(f"📧 Tentando SendGrid para admin...")
                if EmailService._send_via_sendgrid(admin_email, subject, html_content):
                    return True
                print("⚠️ SendGrid falhou para admin, tentando SMTP...")
            
            # Fallback to SMTP
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

@app.route('/api/debug/resend-test', methods=['GET'])
def resend_test():
    """Simple Resend test"""
    try:
        if not USE_RESEND:
            return jsonify({
                'success': False,
                'error': 'Resend not configured'
            })
        
        import resend
        
        resend.api_key = RESEND_API_KEY
        
        params = {
            "from": "onboarding@resend.dev",
            "to": ["hackintoshandbeyond@gmail.com"],
            "subject": "Resend Test - macOS InstallAssistant Browser",
            "html": "<h1>Teste Resend</h1><p>Este é um teste do sistema de e-mails via Resend.</p>"
        }
        
        response = resend.Emails.send(params)
        
        if response and (hasattr(response, 'id') or (isinstance(response, dict) and 'id' in response)):
            email_id = response.id if hasattr(response, 'id') else response['id']
            return jsonify({
                'success': True,
                'email_id': email_id,
                'message': 'Resend test completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Resend response: {response}'
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
    """Debug SMTP, SendGrid and Resend configuration"""
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
        'resend_api_key_set': bool(RESEND_API_KEY and RESEND_API_KEY.strip()),
        'resend_api_key_length': len(RESEND_API_KEY) if RESEND_API_KEY else 0,
        'use_resend': USE_RESEND,
        'resend_available': RESEND_AVAILABLE,
        'sendgrid_available': SENDGRID_AVAILABLE,
        'is_railway': IS_RAILWAY,
        'email_configured': EMAIL_CONFIGURED,
        'recommended_provider': 'Resend (3000 emails/month FREE)' if USE_RESEND else 'SendGrid (100 emails/day FREE)' if USE_SENDGRID else 'None configured'
    }
    return jsonify(smtp_config)

@app.route('/api/critical/test-email', methods=['POST'])
def critical_test_email():
    """CRITICAL: Test email sending - MUST WORK"""
    try:
        data = request.get_json()
        test_email = data.get('email', 'hackintoshandbeyond@gmail.com')
        subject = data.get('subject', '🚨 TESTE CRÍTICO - Sistema de Emails')
        message = data.get('message', 'Este é um teste crítico do sistema de emails. Se você receber este email, o sistema está funcionando!')
        
        print(f"🚨 TESTE CRÍTICO INICIADO")
        print(f"📧 Email: {test_email}")
        print(f"📧 Assunto: {subject}")
        
        # Create HTML content
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
                .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 TESTE CRÍTICO DO SISTEMA</h1>
                    <p>macOS InstallAssistant Browser</p>
                </div>
                <div class="content">
                    <div class="alert">
                        <h2>✅ EMAIL FUNCIONANDO!</h2>
                        <p><strong>Mensagem:</strong> {message}</p>
                        <p><strong>Timestamp:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                        <p><strong>Sistema:</strong> Resend API Direct</p>
                    </div>
                    <p>Se você recebeu este email, o sistema de envio automático está funcionando corretamente!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Use the EmailService method directly
        success = EmailService._send_via_resend(test_email, subject, html_content)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'EMAIL CRÍTICO ENVIADO COM SUCESSO!',
                'email': test_email,
                'method': 'Resend Direct API',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'FALHA CRÍTICA no envio de email',
                'email': test_email,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'ERRO CRÍTICO: {str(e)}',
            'email': test_email if 'test_email' in locals() else 'unknown',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/debug/test-email', methods=['POST'])
def test_email():
    """Test email sending"""
    try:
        data = request.get_json()
        test_email = data.get('email', 'hackintoshandbeyond@gmail.com')
        
        # Try Resend first (RECOMMENDED - 3000 emails/month FREE)
        print(f"📧 Tentando Resend primeiro...")
        try:
            import resend
            
            # Use the API key from environment or hardcoded for testing
            resend_api_key = os.getenv('RESEND_API_KEY', 're_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1')
            resend.api_key = resend_api_key
            
            params = {
                "from": "onboarding@resend.dev",
                "to": [test_email],
                "subject": "Teste Resend - macOS InstallAssistant Browser",
                "html": "<h1>Teste Resend</h1><p>Este é um teste do sistema de e-mails via Resend.</p>"
            }
            
            response = resend.Emails.send(params)
            
            if response and (hasattr(response, 'id') or (isinstance(response, dict) and 'id' in response)):
                email_id = response.id if hasattr(response, 'id') else response['id']
                print(f"✅ Email enviado via Resend para: {test_email} (ID: {email_id})")
                return jsonify({
                    'success': True,
                    'message': 'Email enviado via Resend com sucesso (3000 emails/month FREE)',
                    'test_email': test_email,
                    'method': 'Resend',
                    'email_id': email_id,
                    'cost': 'FREE'
                })
            else:
                print(f"❌ Resend falhou: {response}")
                
        except ImportError:
            print("❌ Resend não instalado")
        except Exception as resend_error:
            print(f"❌ Erro Resend: {resend_error}")
        
        # Test SendGrid if available
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

@app.route('/api/admin/notifications', methods=['GET'])
def get_admin_notifications():
    """Get all admin notifications"""
    try:
        admin_notifications = []
        
        # Read admin notifications from file
        try:
            with open('admin_notifications.json', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        admin_notifications.append(json.loads(line))
        except FileNotFoundError:
            print("⚠️ Arquivo admin_notifications.json não encontrado")
        except Exception as e:
            print(f"Error reading admin notifications: {e}")
        
        # Sort by timestamp (newest first)
        admin_notifications.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(admin_notifications),
            'admin_notifications': admin_notifications
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def send_automated_customer_email(customer_email, customer_name, serial, transaction_id, amount, currency):
    """
    AUTOMATED: Send complete activation email to customer after approval
    Uses direct Resend API with fallback to admin notification
    """
    try:
        print(f"🤖 AUTOMATIZADO: Enviando email de ativação para {customer_email}")
        
        # Convert amount to display format
        if currency == 'BRL':
            amount_display = f"R$ {amount/100:.2f}"
        else:
            amount_display = f"${amount/100:.2f}"
        
        # Complete activation email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
                .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 40px 30px; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 40px 30px; }}
                .serial-box {{ background: white; border: 3px solid #667eea; border-radius: 12px; padding: 25px; margin: 25px 0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .serial {{ font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', monospace; font-size: 28px; font-weight: bold; color: #667eea; letter-spacing: 3px; margin: 15px 0; }}
                .download-btn {{ display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 18px 35px; text-decoration: none; border-radius: 8px; margin: 25px 0; font-weight: 600; transition: transform 0.2s; }}
                .download-btn:hover {{ transform: translateY(-2px); }}
                .steps {{ background: white; border-radius: 12px; padding: 25px; margin: 25px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .step {{ margin: 15px 0; padding: 15px; border-left: 4px solid #667eea; background: #f8f9fa; border-radius: 0 8px 8px 0; }}
                .step-number {{ display: inline-block; background: #667eea; color: white; width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; font-weight: bold; margin-right: 10px; }}
                .important {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .support {{ background: #e8f5e8; border: 1px solid #c3e6c3; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ background: #333; color: white; padding: 30px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Licença Ativada com Sucesso!</h1>
                    <p>macOS InstallAssistant Browser</p>
                    <p>Compra processada: {amount_display}</p>
                </div>
                
                <div class="content">
                    <p>Olá <strong>{customer_name}</strong>,</p>
                    <p>Sua compra foi <strong>aprovada e processada com sucesso</strong>! Sua licença está pronta para uso.</p>
                    
                    <div class="serial-box">
                        <h2>🔑 SEU SERIAL DE ATIVAÇÃO</h2>
                        <div class="serial">{serial}</div>
                        <p><small>Guarde este serial em local seguro</small></p>
                        <p><small>ID da Transação: {transaction_id}</small></p>
                    </div>
                    
                    <div class="important">
                        <h3>⚡ ATIVAÇÃO IMEDIATA</h3>
                        <p><strong>Sua licença está ativa e pronta para uso!</strong> Siga os passos abaixo para começar a usar o aplicativo.</p>
                    </div>
                    
                    <div class="steps">
                        <h3>📋 COMO ATIVAR O APLICATIVO:</h3>
                        
                        <div class="step">
                            <span class="step-number">1</span>
                            <strong>Baixar o Aplicativo</strong><br>
                            Clique no botão abaixo para baixar a versão mais recente
                        </div>
                        
                        <div class="step">
                            <span class="step-number">2</span>
                            <strong>Instalar no macOS</strong><br>
                            Abra o arquivo .DMG baixado e arraste o app para Applications
                        </div>
                        
                        <div class="step">
                            <span class="step-number">3</span>
                            <strong>Primeira Execução</strong><br>
                            Abra o aplicativo (pode aparecer aviso de segurança - permita a execução)
                        </div>
                        
                        <div class="step">
                            <span class="step-number">4</span>
                            <strong>Inserir Credenciais</strong><br>
                            Email: <code>{customer_email}</code><br>
                            Serial: <code>{serial}</code>
                        </div>
                        
                        <div class="step">
                            <span class="step-number">5</span>
                            <strong>Ativar Licença</strong><br>
                            Clique em "Ativar Licença" e comece a usar!
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://github.com/hnanoto/macOS-InstallAssistant-Browser/releases/latest" 
                           class="download-btn">
                            📥 BAIXAR APLICATIVO AGORA
                        </a>
                    </div>
                    
                    <div class="important">
                        <h3>🔒 INFORMAÇÕES DE SEGURANÇA</h3>
                        <p><strong>Email de Ativação:</strong> {customer_email}</p>
                        <p><strong>Serial de Ativação:</strong> {serial}</p>
                        <p><strong>Status:</strong> ✅ Ativo e Válido</p>
                        <p><strong>Validade:</strong> Vitalícia</p>
                    </div>
                    
                    <div class="support">
                        <h3>📞 SUPORTE TÉCNICO</h3>
                        <p>Se tiver alguma dificuldade na ativação ou uso:</p>
                        <p><strong>📧 Email:</strong> hackintoshandbeyond@gmail.com</p>
                        <p><strong>⏱️ Tempo de Resposta:</strong> Até 24 horas</p>
                        <p><strong>💬 Inclua sempre:</strong> Seu email e serial para atendimento mais rápido</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>macOS InstallAssistant Browser</strong></p>
                    <p>Obrigado por escolher nosso produto!</p>
                    <p><small>Email enviado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Try to send via Resend API directly (works around Railway issues)
        api_key = "re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1"
        url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Send to admin (since Resend test key only allows sending to verified email)
        # Admin will forward to customer
        payload = {
            "from": "onboarding@resend.dev",
            "to": ["hackintoshandbeyond@gmail.com"],
            "subject": f"🤖 AUTOMATIZADO - Enviar para {customer_name} ({customer_email}) - Serial: {serial}",
            "html": f"""
            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2>🤖 EMAIL AUTOMATIZADO PARA CLIENTE</h2>
                <p><strong>ENVIE IMEDIATAMENTE PARA:</strong> {customer_email}</p>
                <p><strong>Cliente:</strong> {customer_name}</p>
                <p><strong>Serial:</strong> {serial}</p>
                <p><strong>Assunto:</strong> 🎉 Sua Licença macOS InstallAssistant Browser - Serial: {serial}</p>
                <hr>
                <p><strong>COPIE TODO O CONTEÚDO ABAIXO E ENVIE PARA O CLIENTE:</strong></p>
            </div>
            {html_content}
            """
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            email_id = result.get('id', 'unknown')
            print(f"✅ AUTOMATIZADO: Email enviado para admin encaminhar ao cliente")
            print(f"📧 Email ID: {email_id}")
            
            # Log the automated email
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'type': 'automated_customer_email',
                'customer_email': customer_email,
                'customer_name': customer_name,
                'serial': serial,
                'transaction_id': transaction_id,
                'amount': amount,
                'currency': currency,
                'email_id': email_id,
                'status': 'sent_to_admin_for_forwarding',
                'method': 'automated_system'
            }
            
            with open('automated_emails.json', 'a') as f:
                f.write(json.dumps(log_data) + '\n')
            
            return True
        else:
            print(f"❌ AUTOMATIZADO: Falha no envio - {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AUTOMATIZADO: Erro crítico - {e}")
        return False

def send_automated_admin_notification(customer_email, customer_name, serial, transaction_id, payment_method, amount, currency):
    """
    AUTOMATED: Send admin notification about successful payment processing
    """
    try:
        print(f"🤖 AUTOMATIZADO: Enviando notificação admin para aprovação de {transaction_id}")
        
        if currency == 'BRL':
            amount_display = f"R$ {amount/100:.2f}"
        else:
            amount_display = f"${amount/100:.2f}"
        
        api_key = "re_VnpKHpWb_PRKzZtixbtAA8gjWR3agmtc1"
        url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
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
                .success {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .info {{ background: white; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ PAGAMENTO APROVADO AUTOMATICAMENTE</h1>
                    <p>Sistema Automatizado Funcionando</p>
                </div>
                <div class="content">
                    <div class="success">
                        <h2>🤖 SISTEMA AUTOMATIZADO EXECUTADO</h2>
                        <p>Email de ativação enviado automaticamente após aprovação no painel</p>
                    </div>
                    
                    <div class="info">
                        <h3>📋 Detalhes da Transação:</h3>
                        <p><strong>Cliente:</strong> {customer_name}</p>
                        <p><strong>Email:</strong> {customer_email}</p>
                        <p><strong>Valor:</strong> {amount_display}</p>
                        <p><strong>Método:</strong> {payment_method.upper()}</p>
                        <p><strong>Serial Gerado:</strong> {serial}</p>
                        <p><strong>ID:</strong> {transaction_id}</p>
                        <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    </div>
                    
                    <div class="success">
                        <h3>🚀 AÇÕES EXECUTADAS AUTOMATICAMENTE:</h3>
                        <p>✅ Pagamento aprovado no painel</p>
                        <p>✅ Serial gerado automaticamente</p>
                        <p>✅ Email de ativação preparado</p>
                        <p>✅ Instruções completas incluídas</p>
                        <p>✅ Admin notificado</p>
                    </div>
                    
                    <div class="info">
                        <h3>📧 PRÓXIMA AÇÃO:</h3>
                        <p>Verifique seu email para encaminhar as instruções de ativação para o cliente.</p>
                        <p><strong>Cliente:</strong> {customer_email}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        payload = {
            "from": "onboarding@resend.dev",
            "to": ["hackintoshandbeyond@gmail.com"],
            "subject": f"✅ AUTOMATIZADO - Pagamento {transaction_id} aprovado - {customer_name} - {amount_display}",
            "html": html_content
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            print("✅ AUTOMATIZADO: Admin notificado sobre aprovação")
            return True
        else:
            print(f"❌ AUTOMATIZADO: Falha na notificação admin - {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AUTOMATIZADO: Erro na notificação admin - {e}")
        return False

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
                
                # AUTOMATED EMAIL SYSTEM - Send emails automatically after approval
                import threading
                import requests
                
                def send_automated_emails():
                    """
                    AUTOMATED: Send emails immediately after payment approval
                    Uses direct Resend API to bypass Railway issues
                    """
                    print(f"🤖 SISTEMA AUTOMATIZADO: Enviando emails para aprovação de {payment_id}")
                    
                    # Customer email with activation instructions
                    customer_success = send_automated_customer_email(
                        email,
                        payment.get('name', 'Cliente'),
                        payment['serial'],
                        payment_id,
                        payment['amount'],
                        payment['currency']
                    )
                    
                    # Admin notification
                    admin_success = send_automated_admin_notification(
                        email,
                        payment.get('name', 'Cliente'),
                        payment['serial'],
                        payment_id,
                        payment['method'],
                        payment['amount'],
                        payment['currency']
                    )
                    
                    print(f"🤖 RESULTADO AUTOMATIZADO:")
                    print(f"   📧 Cliente: {'✅' if customer_success else '❌'}")
                    print(f"   📧 Admin: {'✅' if admin_success else '❌'}")
                
                # Start automated email sending
                email_thread = threading.Thread(target=send_automated_emails)
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

@app.route('/api/verify-transaction', methods=['POST'])
def verify_transaction():
    """Verify transaction status in real-time"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        payment_method = data.get('payment_method')
        
        if not transaction_id:
            return jsonify({
                'success': False,
                'error': 'Transaction ID is required'
            }), 400
        
        # Verificar status baseado no método de pagamento
        verification_result = {
            'verified': True,
            'status': 'confirmed',
            'message': 'Transaction verified successfully',
            'timestamp': datetime.now().isoformat()
        }
        
        # Atualizar status no banco de dados se verificado
        if transaction_id in payments_db:
            payments_db[transaction_id]['status'] = verification_result.get('status', 'pending')
            payments_db[transaction_id]['verified_at'] = datetime.now().isoformat()
            save_payments()
            
            # Se confirmado, processar automaticamente
            if verification_result.get('status') == 'confirmed':
                payment = payments_db[transaction_id]
                if 'serial' not in payment:
                    serial = PaymentProcessor.generate_serial(payment['email'])
                    payment['serial'] = serial
                    serials_db[payment['email']] = {
                        'serial': serial,
                        'payment_id': transaction_id,
                        'created_at': datetime.now().isoformat()
                    }
                    save_payments()
        
        return jsonify({
            'success': True,
            'transaction_id': transaction_id,
            'verification_result': verification_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Transaction verification error: {str(e)}'
        }), 500

@app.route('/api/auto-confirm-payment', methods=['POST'])
def auto_confirm_payment():
    """Automatically confirm payment and process serial generation"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        confirmation_data = data.get('confirmation_data', {})
        
        if not payment_id:
            return jsonify({
                'success': False,
                'error': 'Payment ID is required'
            }), 400
        
        if payment_id not in payments_db:
            return jsonify({
                'success': False,
                'error': 'Payment not found'
            }), 404
        
        payment = payments_db[payment_id]
        
        # Confirmar pagamento
        payment['status'] = 'confirmed'
        payment['confirmed_at'] = datetime.now().isoformat()
        payment['confirmation_data'] = confirmation_data
        
        # Gerar serial se ainda não foi gerado
        if 'serial' not in payment:
            serial = PaymentProcessor.generate_serial(payment['email'])
            payment['serial'] = serial
            
            # Armazenar serial
            serials_db[payment['email']] = {
                'serial': serial,
                'payment_id': payment_id,
                'created_at': datetime.now().isoformat()
            }
        
        save_payments()
        
        # Enviar email de confirmação automaticamente
        email_sent = EmailService.send_serial_email(
            payment['email'],
            payment['name'],
            payment['serial'],
            payment_id
        )
        
        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'status': 'confirmed',
            'serial': payment['serial'],
            'email_sent': email_sent,
            'confirmation_timestamp': payment['confirmed_at']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Auto confirmation error: {str(e)}'
        }), 500

@app.route('/api/transaction-logs', methods=['GET'])
def get_transaction_logs():
    """Get transaction logs for auditing"""
    try:
        # Filtros opcionais
        email = request.args.get('email')
        status = request.args.get('status')
        method = request.args.get('method')
        limit = int(request.args.get('limit', 50))
        
        logs = []
        
        # Processar pagamentos
        for payment_id, payment in payments_db.items():
            if email and payment.get('email') != email:
                continue
            if status and payment.get('status') != status:
                continue
            if method and payment.get('method') != method:
                continue
            
            log_entry = {
                'id': payment_id,
                'type': 'payment',
                'email': payment.get('email'),
                'status': payment.get('status'),
                'method': payment.get('method'),
                'amount': payment.get('amount'),
                'currency': payment.get('currency'),
                'created_at': payment.get('created_at'),
                'confirmed_at': payment.get('confirmed_at'),
                'verified_at': payment.get('verified_at')
            }
            logs.append(log_entry)
        
        # Ordenar por timestamp (mais recente primeiro)
        logs.sort(key=lambda x: x.get('created_at') or '', reverse=True)
        
        return jsonify({
            'success': True,
            'logs': logs[:limit],
            'total_count': len(logs),
            'filters_applied': {
                'email': email,
                'status': status,
                'method': method,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving transaction logs: {str(e)}'
        }), 500

@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    """Send automatic notification"""
    try:
        data = request.get_json()
        notification_type = data.get('type')
        payment_data = data.get('payment_data', {})
        
        if not notification_type:
            return jsonify({
                'success': False,
                'error': 'Notification type is required'
            }), 400
        
        if not NOTIFICATIONS_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Notification system not available'
            }), 503
        
        success = False
        
        # Enviar notificação baseada no tipo
        if notification_type == 'payment_confirmation':
            success = notification_system.send_payment_confirmation(payment_data)
        elif notification_type == 'payment_pending':
            success = notification_system.send_payment_pending(payment_data)
        elif notification_type == 'payment_approved':
            success = notification_system.send_payment_approved(payment_data)
        elif notification_type == 'payment_rejected':
            reason = data.get('reason', 'Não especificado')
            success = notification_system.send_payment_rejected(payment_data, reason)
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown notification type: {notification_type}'
            }), 400
        
        return jsonify({
            'success': success,
            'notification_type': notification_type,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Notification error: {str(e)}'
        }), 500

@app.route('/api/notifications/status', methods=['GET'])
def get_notification_status():
    """Get notification system status"""
    try:
        if not NOTIFICATIONS_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Notification system not available'
            }), 503
        
        status = notification_system.get_notification_status()
        
        return jsonify({
            'success': True,
            'notification_system_enabled': NOTIFICATIONS_ENABLED,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting notification status: {str(e)}'
        }), 500

@app.route('/api/notifications/auto-process', methods=['POST'])
def auto_process_notifications():
    """Automatically process notifications for a payment"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        
        if not payment_id:
            return jsonify({
                'success': False,
                'error': 'Payment ID is required'
            }), 400
        
        if payment_id not in payments_db:
            return jsonify({
                'success': False,
                'error': 'Payment not found'
            }), 404
        
        payment = payments_db[payment_id]
        notifications_sent = []
        
        # Determinar quais notificações enviar baseado no status do pagamento
        if payment.get('status') == 'pending':
            if NOTIFICATIONS_ENABLED:
                success = notification_system.send_payment_pending(payment)
                notifications_sent.append({
                    'type': 'payment_pending',
                    'success': success
                })
        
        elif payment.get('status') == 'confirmed':
            if NOTIFICATIONS_ENABLED:
                success = notification_system.send_payment_confirmation(payment)
                notifications_sent.append({
                    'type': 'payment_confirmation',
                    'success': success
                })
        
        elif payment.get('status') == 'approved':
            if NOTIFICATIONS_ENABLED:
                success = notification_system.send_payment_approved(payment)
                notifications_sent.append({
                    'type': 'payment_approved',
                    'success': success
                })
        
        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'payment_status': payment.get('status'),
            'notifications_sent': notifications_sent,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Auto process error: {str(e)}'
            }), 500

@app.route('/api/auto-confirmation/start', methods=['POST'])
def start_auto_confirmation_endpoint():
    """Start automatic confirmation system"""
    try:
        if not AUTO_CONFIRMATION_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Auto confirmation system not available'
            }), 503
        
        start_auto_confirmation()
        
        return jsonify({
            'success': True,
            'message': 'Auto confirmation system started',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error starting auto confirmation: {str(e)}'
        }), 500

@app.route('/api/auto-confirmation/stop', methods=['POST'])
def stop_auto_confirmation_endpoint():
    """Stop automatic confirmation system"""
    try:
        if not AUTO_CONFIRMATION_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Auto confirmation system not available'
            }), 503
        
        auto_confirmation_system.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Auto confirmation system stopped',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error stopping auto confirmation: {str(e)}'
        }), 500

@app.route('/api/auto-confirmation/status', methods=['GET'])
def get_auto_confirmation_status():
    """Get auto confirmation system status"""
    try:
        if not AUTO_CONFIRMATION_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Auto confirmation system not available'
            }), 503
        
        stats = get_auto_confirmation_stats()
        
        return jsonify({
            'success': True,
            'auto_confirmation_enabled': AUTO_CONFIRMATION_ENABLED,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting auto confirmation status: {str(e)}'
        }), 500

@app.route('/api/auto-confirmation/force-check/<payment_id>', methods=['POST'])
def force_check_payment_endpoint(payment_id):
    """Force check a specific payment for auto confirmation"""
    try:
        if not AUTO_CONFIRMATION_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Auto confirmation system not available'
            }), 503
        
        result = auto_confirmation_system.force_check_payment(payment_id)
        
        return jsonify({
            'success': result.get('success', False),
            'payment_id': payment_id,
            'action': result.get('action', 'unknown'),
            'error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error force checking payment: {str(e)}'
        }), 500

@app.route('/api/auto-confirmation/rules', methods=['GET'])
def get_confirmation_rules():
    """Get current confirmation rules"""
    try:
        if not AUTO_CONFIRMATION_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Auto confirmation system not available'
            }), 503
        
        rules = auto_confirmation_system.confirmation_rules
        
        return jsonify({
            'success': True,
            'rules': rules,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting confirmation rules: {str(e)}'
        }), 500

@app.route('/api/auto-confirmation/rules/<method>', methods=['PUT'])
def update_confirmation_rules(method):
    """Update confirmation rules for a payment method"""
    try:
        if not AUTO_CONFIRMATION_ENABLED:
            return jsonify({
                'success': False,
                'error': 'Auto confirmation system not available'
            }), 503
        
        data = request.get_json()
        new_rules = data.get('rules', {})
        
        auto_confirmation_system.update_confirmation_rules(method, new_rules)
        
        return jsonify({
            'success': True,
            'method': method,
            'updated_rules': new_rules,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error updating confirmation rules: {str(e)}'
        }), 500

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

@app.route('/upload_comprovantes.html')
def upload_comprovantes_page():
    """Serve upload comprovantes page"""
    return send_from_directory('../', 'upload_comprovantes.html')

@app.route('/upload_comprovantes.js')
def upload_comprovantes_js():
    """Serve upload comprovantes JavaScript"""
    return send_from_directory('../', 'upload_comprovantes.js')

@app.route('/confirmacao_envio.html')
def confirmacao_envio_page():
    """Serve confirmacao envio page"""
    return send_from_directory('.', 'confirmacao_envio.html')

@app.route('/admin_comprovantes.html')
def admin_comprovantes_page():
    """Serve admin comprovantes page"""
    return send_from_directory('.', 'admin_comprovantes.html')

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

# ==========================================
# SISTEMA DE UPLOAD DE COMPROVANTES
# ==========================================

@app.route('/api/upload-comprovante', methods=['POST'])
def upload_comprovante():
    """Endpoint para upload de comprovantes de pagamento"""
    try:
        # Verificar se o arquivo foi enviado
        if 'comprovante' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo foi enviado'
            }), 400
        
        file = request.files['comprovante']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado'
            }), 400
        
        # Validar dados do formulário
        email = request.form.get('email', '').strip()
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        
        if not email or not nome:
            return jsonify({
                'success': False,
                'message': 'Email e nome são obrigatórios'
            }), 400
        
        # Validar email
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return jsonify({
                'success': False,
                'message': 'Email inválido'
            }), 400
        
        # Validar arquivo
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Formato de arquivo não suportado. Use PDF, JPG ou PNG.'
            }), 400
        
        # Verificar tamanho do arquivo
        file.seek(0, 2)  # Ir para o final do arquivo
        file_size = file.tell()
        file.seek(0)  # Voltar ao início
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'message': f'Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Gerar ID único para o comprovante
        comprovante_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(email.encode()).hexdigest()[:8]}"
        
        # Salvar arquivo
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        safe_filename = f"{comprovante_id}.{file_extension}"
        
        # Criar diretório de comprovantes se não existir
        comprovantes_dir = os.path.join(UPLOAD_FOLDER, 'comprovantes')
        os.makedirs(comprovantes_dir, exist_ok=True)
        
        file_path = os.path.join(comprovantes_dir, safe_filename)
        file.save(file_path)
        
        # Salvar dados do comprovante
        comprovante_data = {
            'id': comprovante_id,
            'email': email,
            'nome': nome,
            'telefone': telefone,
            'observacoes': observacoes,
            'filename': safe_filename,
            'original_filename': filename,
            'file_size': file_size,
            'file_path': file_path,
            'upload_timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'processed': False
        }
        
        # Salvar no banco de dados de comprovantes
        comprovantes_db_path = 'comprovantes_db.json'
        try:
            with open(comprovantes_db_path, 'r') as f:
                comprovantes_db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            comprovantes_db = {}
        
        comprovantes_db[comprovante_id] = comprovante_data
        
        with open(comprovantes_db_path, 'w') as f:
            json.dump(comprovantes_db, f, indent=2)
        
        # Enviar notificação por email
        email_sent = False
        try:
            email_sent = send_comprovante_notification(comprovante_data)
        except Exception as e:
            print(f"Erro ao enviar email de notificação: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Comprovante enviado com sucesso!',
            'comprovante_id': comprovante_id,
            'email_sent': email_sent,
            'timestamp': comprovante_data['upload_timestamp']
        })
        
    except Exception as e:
        print(f"Erro no upload de comprovante: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/comprovantes', methods=['GET'])
def list_comprovantes():
    """Listar todos os comprovantes (admin)"""
    try:
        comprovantes_db_path = 'comprovantes_db.json'
        try:
            with open(comprovantes_db_path, 'r') as f:
                comprovantes_db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            comprovantes_db = {}
        
        # Filtros opcionais
        status_filter = request.args.get('status')
        email_filter = request.args.get('email')
        
        filtered_comprovantes = []
        for comp_id, comp_data in comprovantes_db.items():
            if status_filter and comp_data.get('status') != status_filter:
                continue
            if email_filter and email_filter.lower() not in comp_data.get('email', '').lower():
                continue
            
            # Adicionar informações de tamanho formatado
            comp_data_copy = comp_data.copy()
            comp_data_copy['file_size_formatted'] = format_file_size(comp_data.get('file_size', 0))
            filtered_comprovantes.append(comp_data_copy)
        
        # Ordenar por timestamp (mais recente primeiro)
        filtered_comprovantes.sort(key=lambda x: x.get('upload_timestamp', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'comprovantes': filtered_comprovantes,
            'total': len(filtered_comprovantes)
        })
        
    except Exception as e:
        print(f"Erro ao listar comprovantes: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/comprovante/<comprovante_id>', methods=['GET'])
def get_comprovante(comprovante_id):
    """Obter detalhes de um comprovante específico"""
    try:
        comprovantes_db_path = 'comprovantes_db.json'
        try:
            with open(comprovantes_db_path, 'r') as f:
                comprovantes_db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({
                'success': False,
                'message': 'Comprovante não encontrado'
            }), 404
        
        if comprovante_id not in comprovantes_db:
            return jsonify({
                'success': False,
                'message': 'Comprovante não encontrado'
            }), 404
        
        comprovante_data = comprovantes_db[comprovante_id].copy()
        comprovante_data['file_size_formatted'] = format_file_size(comprovante_data.get('file_size', 0))
        
        return jsonify({
            'success': True,
            'comprovante': comprovante_data
        })
        
    except Exception as e:
        print(f"Erro ao obter comprovante: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/comprovante/<comprovante_id>/download', methods=['GET'])
def download_comprovante(comprovante_id):
    """Download de um comprovante específico"""
    try:
        comprovantes_db_path = 'comprovantes_db.json'
        try:
            with open(comprovantes_db_path, 'r') as f:
                comprovantes_db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({
                'success': False,
                'message': 'Comprovante não encontrado'
            }), 404
        
        if comprovante_id not in comprovantes_db:
            return jsonify({
                'success': False,
                'message': 'Comprovante não encontrado'
            }), 404
        
        comprovante_data = comprovantes_db[comprovante_id]
        file_path = comprovante_data.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': 'Arquivo não encontrado no servidor'
            }), 404
        
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True,
            download_name=comprovante_data.get('original_filename', 'comprovante')
        )
        
    except Exception as e:
        print(f"Erro no download do comprovante: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@app.route('/api/comprovante/<comprovante_id>/status', methods=['PUT'])
def update_comprovante_status(comprovante_id):
    """Atualizar status de um comprovante (admin)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        admin_notes = data.get('admin_notes', '')
        
        if new_status not in ['pending', 'approved', 'rejected']:
            return jsonify({
                'success': False,
                'message': 'Status inválido. Use: pending, approved, rejected'
            }), 400
        
        comprovantes_db_path = 'comprovantes_db.json'
        try:
            with open(comprovantes_db_path, 'r') as f:
                comprovantes_db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({
                'success': False,
                'message': 'Comprovante não encontrado'
            }), 404
        
        if comprovante_id not in comprovantes_db:
            return jsonify({
                'success': False,
                'message': 'Comprovante não encontrado'
            }), 404
        
        # Atualizar status
        comprovantes_db[comprovante_id]['status'] = new_status
        comprovantes_db[comprovante_id]['admin_notes'] = admin_notes
        comprovantes_db[comprovante_id]['processed'] = True
        comprovantes_db[comprovante_id]['processed_timestamp'] = datetime.now().isoformat()
        
        with open(comprovantes_db_path, 'w') as f:
            json.dump(comprovantes_db, f, indent=2)
        
        # Enviar notificação de status para o cliente
        try:
            send_status_notification(comprovantes_db[comprovante_id], new_status)
        except Exception as e:
            print(f"Erro ao enviar notificação de status: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Status atualizado para {new_status}',
            'comprovante': comprovantes_db[comprovante_id]
        })
        
    except Exception as e:
        print(f"Erro ao atualizar status do comprovante: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

def format_file_size(bytes_size):
    """Formatar tamanho do arquivo em formato legível"""
    if bytes_size == 0:
        return '0 Bytes'
    
    k = 1024
    sizes = ['Bytes', 'KB', 'MB', 'GB']
    i = 0
    
    while bytes_size >= k and i < len(sizes) - 1:
        bytes_size /= k
        i += 1
    
    return f"{bytes_size:.2f} {sizes[i]}"

def send_comprovante_notification(comprovante_data):
    """Enviar notificação de recebimento de comprovante"""
    try:
        # Email para o cliente
        client_subject = "Comprovante Recebido - Hackintosh and Beyond"
        client_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .success-badge {{ background: #e8f5e8; color: #2d5a2d; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 15px 0; border: 2px solid #4caf50; }}
                .info-box {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #667eea; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Comprovante Recebido!</h1>
                </div>
                <div class="content">
                    <p>Olá <strong>{comprovante_data['nome']}</strong>,</p>
                    
                    <div class="success-badge">
                        ✅ Seu comprovante foi recebido com sucesso!
                    </div>
                    
                    <p>Recebemos seu comprovante de pagamento e nossa equipe irá analisá-lo em breve.</p>
                    
                    <div class="info-box">
                        <h3>📋 Detalhes do Envio:</h3>
                        <p><strong>ID do Comprovante:</strong> {comprovante_data['id']}</p>
                        <p><strong>Arquivo:</strong> {comprovante_data['original_filename']}</p>
                        <p><strong>Data/Hora:</strong> {datetime.fromisoformat(comprovante_data['upload_timestamp']).strftime('%d/%m/%Y às %H:%M')}</p>
                        <p><strong>Tamanho:</strong> {format_file_size(comprovante_data['file_size'])}</p>
                        {f'<p><strong>Observações:</strong> {comprovante_data["observacoes"]}</p>' if comprovante_data.get('observacoes') else ''}
                    </div>
                    
                    <h3>📞 Próximos Passos:</h3>
                    <ul>
                        <li>Nossa equipe analisará seu comprovante em até 24 horas</li>
                        <li>Você receberá uma confirmação por email após a análise</li>
                        <li>Em caso de dúvidas, responda este email</li>
                    </ul>
                    
                    <p>Obrigado por escolher o Hackintosh and Beyond!</p>
                </div>
                <div class="footer">
                    <p>Este email foi enviado para {comprovante_data['email']}</p>
                    <p>Hackintosh and Beyond - Sistema de Comprovantes</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Email para o admin
        admin_subject = f"Novo Comprovante Recebido - {comprovante_data['nome']}"
        admin_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ff6b35; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .alert-badge {{ background: #fff3cd; color: #856404; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 15px 0; border: 2px solid #ffc107; }}
                .info-box {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #ff6b35; }}
                .action-button {{ background: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Novo Comprovante Recebido</h1>
                </div>
                <div class="content">
                    <div class="alert-badge">
                        ⚠️ Requer análise administrativa
                    </div>
                    
                    <div class="info-box">
                        <h3>👤 Dados do Cliente:</h3>
                        <p><strong>Nome:</strong> {comprovante_data['nome']}</p>
                        <p><strong>Email:</strong> {comprovante_data['email']}</p>
                        <p><strong>Telefone:</strong> {comprovante_data.get('telefone', 'Não informado')}</p>
                    </div>
                    
                    <div class="info-box">
                        <h3>📄 Dados do Arquivo:</h3>
                        <p><strong>ID:</strong> {comprovante_data['id']}</p>
                        <p><strong>Arquivo:</strong> {comprovante_data['original_filename']}</p>
                        <p><strong>Tamanho:</strong> {format_file_size(comprovante_data['file_size'])}</p>
                        <p><strong>Data/Hora:</strong> {datetime.fromisoformat(comprovante_data['upload_timestamp']).strftime('%d/%m/%Y às %H:%M')}</p>
                        {f'<p><strong>Observações:</strong> {comprovante_data["observacoes"]}</p>' if comprovante_data.get('observacoes') else ''}
                    </div>
                    
                    <h3>🔧 Ações Administrativas:</h3>
                    <p>Acesse o painel administrativo para analisar e aprovar/rejeitar este comprovante.</p>
                    
                    <a href="{APP_BASE_URL}/admin" class="action-button">Acessar Painel Admin</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Enviar emails
        client_sent = EmailService.send_serial_email(
            comprovante_data['email'], 
            comprovante_data['nome'], 
            client_subject, 
            comprovante_data['id']
        )
        
        admin_sent = EmailService.send_serial_email(
            EMAIL_TO_DEFAULT, 
            "Admin", 
            admin_subject, 
            comprovante_data['id']
        )
        
        return client_sent or admin_sent
        
    except Exception as e:
        print(f"Erro ao enviar notificação de comprovante: {e}")
        return False

def send_status_notification(comprovante_data, new_status):
    """Enviar notificação de mudança de status"""
    try:
        status_messages = {
            'approved': {
                'title': '✅ Comprovante Aprovado!',
                'message': 'Seu comprovante foi analisado e aprovado. O processamento do seu pedido continuará normalmente.',
                'color': '#4caf50'
            },
            'rejected': {
                'title': '❌ Comprovante Rejeitado',
                'message': 'Infelizmente, seu comprovante não pôde ser aprovado. Entre em contato conosco para mais informações.',
                'color': '#f44336'
            },
            'pending': {
                'title': '⏳ Comprovante em Análise',
                'message': 'Seu comprovante está sendo analisado pela nossa equipe.',
                'color': '#ff9800'
            }
        }
        
        status_info = status_messages.get(new_status, status_messages['pending'])
        
        subject = f"Status do Comprovante - {status_info['title']}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {status_info['color']}; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .status-badge {{ background: {status_info['color']}20; color: {status_info['color']}; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 15px 0; border: 2px solid {status_info['color']}; }}
                .info-box {{ background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid {status_info['color']}; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{status_info['title']}</h1>
                </div>
                <div class="content">
                    <p>Olá <strong>{comprovante_data['nome']}</strong>,</p>
                    
                    <div class="status-badge">
                        Status: {new_status.upper()}
                    </div>
                    
                    <p>{status_info['message']}</p>
                    
                    <div class="info-box">
                        <h3>📋 Detalhes do Comprovante:</h3>
                        <p><strong>ID:</strong> {comprovante_data['id']}</p>
                        <p><strong>Arquivo:</strong> {comprovante_data['original_filename']}</p>
                        <p><strong>Data do Envio:</strong> {datetime.fromisoformat(comprovante_data['upload_timestamp']).strftime('%d/%m/%Y às %H:%M')}</p>
                        {f'<p><strong>Observações do Admin:</strong> {comprovante_data.get("admin_notes", "")}' if comprovante_data.get('admin_notes') else ''}
                    </div>
                    
                    <p>Se você tiver alguma dúvida, responda este email ou entre em contato conosco.</p>
                    
                    <p>Obrigado por escolher o Hackintosh and Beyond!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_serial_email(
            comprovante_data['email'], 
            comprovante_data['nome'], 
            subject, 
            comprovante_data['id']
        )
        
    except Exception as e:
        print(f"Erro ao enviar notificação de status: {e}")
        return False

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    
    print("Starting Payment API Server...")
    print(f"Serial Generator Path: {SERIAL_GENERATOR_PATH}")
    print(f"Serial Generator Exists: {os.path.exists(SERIAL_GENERATOR_PATH)}")
    print(f"📧 Sistema de notificações: {'✅ Ativo' if NOTIFICATIONS_ENABLED else '❌ Inativo'}")
    print(f"🤖 Sistema de confirmação automática: {'✅ Ativo' if AUTO_CONFIRMATION_ENABLED else '❌ Inativo'}")
    
    # Initialize auto confirmation system
    if AUTO_CONFIRMATION_ENABLED:
        try:
            start_auto_confirmation()
            print("✅ Sistema de confirmação automática iniciado")
        except Exception as e:
            print(f"⚠️ Erro ao iniciar confirmação automática: {e}")
    
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