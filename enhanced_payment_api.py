#!/usr/bin/env python3
"""
API de Pagamentos Avançada - Sistema Totalmente Funcional
Integra verificação de transações, confirmação automática e notificações
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

# Importar sistemas avançados
from payment_verification import PaymentVerificationSystem, PaymentConfirmationSystem
from notification_system import NotificationSystem
from payment_confirmation import PaymentConfirmationSystem as ConfirmationSystem, PaymentReceiptSystem

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

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'hackintoshandbeyond@gmail.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'hackintoshandbeyond@gmail.com')

# Serial generation configuration
SECRET_KEY = "HackintoshAndBeyond2024!"
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
    """Save payments to file"""
    try:
        with open('payments.json', 'w') as f:
            json.dump(payments_db, f, separators=(',', ':'))
    except Exception as e:
        print(f"❌ Erro ao salvar pagamentos: {e}")

# Load payments on startup
load_payments()

# Initialize advanced systems
payment_verifier = PaymentVerificationSystem()
notification_system = NotificationSystem()
confirmation_system = ConfirmationSystem()
receipt_system = PaymentReceiptSystem()

class EnhancedPaymentProcessor:
    """Processador de pagamentos avançado com verificação robusta"""
    
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
    def process_stripe_payment_enhanced(token: str, amount: int, currency: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Stripe payment with enhanced verification"""
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
                # Verificar pagamento com sistema avançado
                verification_result = payment_verifier.verify_stripe_payment(
                    charge.id, amount, currency
                )
                
                if verification_result['success']:
                    # Generate serial
                    serial = EnhancedPaymentProcessor.generate_serial(customer_data['email'])
                    
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
                        'status': 'verified',
                        'serial': serial,
                        'verification_data': verification_result,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Gerar comprovante
                    receipt = receipt_system.generate_receipt(payments_db[payment_id])
                    
                    # Adicionar confirmação automática
                    confirmation_id = confirmation_system.add_confirmation_request(payments_db[payment_id])
                    
                    return {
                        'success': True,
                        'transactionId': payment_id,
                        'serial': serial,
                        'email': customer_data['email'],
                        'name': customer_data['name'],
                        'verification': verification_result,
                        'receipt_id': receipt.get('id', ''),
                        'confirmation_id': confirmation_id
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Falha na verificação de segurança',
                        'verification': verification_result
                    }
            else:
                return {'success': False, 'error': 'Payment failed'}
                
        except stripe.error.CardError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': f'Payment processing error: {str(e)}'}
    
    @staticmethod
    def process_paypal_payment_enhanced(order_id: str, amount: float, currency: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process PayPal payment with enhanced verification"""
        try:
            # Verificar pagamento PayPal
            verification_result = payment_verifier.verify_paypal_payment(
                order_id, amount, currency
            )
            
            if verification_result['success']:
                # Generate serial
                serial = EnhancedPaymentProcessor.generate_serial(customer_data['email'])
                
                # Store payment record
                payment_id = order_id
                payments_db[payment_id] = {
                    'id': payment_id,
                    'email': customer_data['email'],
                    'name': customer_data['name'],
                    'country': customer_data['country'],
                    'amount': int(amount * 100),  # Convert to cents
                    'currency': currency,
                    'method': 'paypal',
                    'status': 'verified',
                    'serial': serial,
                    'verification_data': verification_result,
                    'created_at': datetime.now().isoformat()
                }
                
                # Gerar comprovante
                receipt = receipt_system.generate_receipt(payments_db[payment_id])
                
                # Adicionar confirmação automática
                confirmation_id = confirmation_system.add_confirmation_request(payments_db[payment_id])
                
                return {
                    'success': True,
                    'transactionId': payment_id,
                    'serial': serial,
                    'email': customer_data['email'],
                    'name': customer_data['name'],
                    'verification': verification_result,
                    'receipt_id': receipt.get('id', ''),
                    'confirmation_id': confirmation_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Falha na verificação do PayPal',
                    'verification': verification_result
                }
                
        except Exception as e:
            return {'success': False, 'error': f'PayPal processing error: {str(e)}'}
    
    @staticmethod
    def process_pix_payment_enhanced(payment_id: str, proof_data: Dict[str, Any], customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process PIX payment with enhanced verification"""
        try:
            # Verificar pagamento PIX
            verification_result = payment_verifier.verify_pix_payment(
                payment_id, proof_data
            )
            
            if verification_result['success']:
                # Generate serial
                serial = EnhancedPaymentProcessor.generate_serial(customer_data['email'])
                
                # Store payment record
                payments_db[payment_id] = {
                    'id': payment_id,
                    'email': customer_data['email'],
                    'name': customer_data['name'],
                    'country': customer_data['country'],
                    'amount': proof_data.get('amount', 2650),  # Default R$ 26,50
                    'currency': 'BRL',
                    'method': 'pix',
                    'status': 'verified',
                    'serial': serial,
                    'verification_data': verification_result,
                    'proof_data': proof_data,
                    'created_at': datetime.now().isoformat()
                }
                
                # Gerar comprovante
                receipt = receipt_system.generate_receipt(payments_db[payment_id])
                
                # Adicionar confirmação automática
                confirmation_id = confirmation_system.add_confirmation_request(payments_db[payment_id])
                
                return {
                    'success': True,
                    'transactionId': payment_id,
                    'serial': serial,
                    'email': customer_data['email'],
                    'name': customer_data['name'],
                    'verification': verification_result,
                    'receipt_id': receipt.get('id', ''),
                    'confirmation_id': confirmation_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Falha na verificação do PIX',
                    'verification': verification_result
                }
                
        except Exception as e:
            return {'success': False, 'error': f'PIX processing error: {str(e)}'}

# API Routes

@app.route('/api/enhanced/process-payment', methods=['POST'])
def enhanced_process_payment():
    """Process payment with enhanced verification and confirmation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['token', 'amount', 'currency', 'email', 'name', 'country', 'method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Process payment based on method
        customer_data = {
            'email': data['email'],
            'name': data['name'],
            'country': data['country']
        }
        
        if data['method'] == 'stripe':
            result = EnhancedPaymentProcessor.process_stripe_payment_enhanced(
                data['token'],
                data['amount'],
                data['currency'],
                customer_data
            )
        elif data['method'] == 'paypal':
            result = EnhancedPaymentProcessor.process_paypal_payment_enhanced(
                data.get('order_id', ''),
                data['amount'] / 100,  # Convert from cents
                data['currency'],
                customer_data
            )
        else:
            return jsonify({'error': 'Unsupported payment method'}), 400
        
        if result['success']:
            # Enviar notificações automáticas
            notification_system.send_payment_confirmation({
                'email': result['email'],
                'name': result['name'],
                'payment_id': result['transactionId'],
                'amount': data['amount'],
                'currency': data['currency'],
                'serial': result['serial'],
                'method': data['method']
            })
            
            save_payments()
            
            return jsonify(result)
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/verify-payment', methods=['POST'])
def enhanced_verify_payment():
    """Verify payment with enhanced security checks"""
    try:
        data = request.get_json()
        
        if 'payment_id' not in data or 'method' not in data:
            return jsonify({'error': 'Missing payment_id or method'}), 400
        
        payment_id = data['payment_id']
        method = data['method']
        
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payments_db[payment_id]
        
        # Verificar baseado no método
        if method == 'stripe':
            verification_result = payment_verifier.verify_stripe_payment(
                payment_id, payment['amount'], payment['currency']
            )
        elif method == 'paypal':
            verification_result = payment_verifier.verify_paypal_payment(
                payment_id, payment['amount'] / 100, payment['currency']
            )
        elif method == 'pix':
            verification_result = payment_verifier.verify_pix_payment(
                payment_id, payment.get('proof_data', {})
            )
        else:
            return jsonify({'error': 'Unsupported payment method'}), 400
        
        return jsonify(verification_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/confirmation-status/<confirmation_id>', methods=['GET'])
def get_confirmation_status(confirmation_id):
    """Get confirmation status"""
    try:
        status = confirmation_system.get_confirmation_status(confirmation_id)
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/force-confirmation', methods=['POST'])
def force_confirmation():
    """Force confirmation for specific payment"""
    try:
        data = request.get_json()
        
        if 'confirmation_id' not in data:
            return jsonify({'error': 'Missing confirmation_id'}), 400
        
        success = confirmation_system.force_confirmation(data['confirmation_id'])
        
        return jsonify({
            'success': success,
            'message': 'Confirmação forçada' if success else 'Falha ao forçar confirmação'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/confirmation-statistics', methods=['GET'])
def get_confirmation_statistics():
    """Get confirmation statistics"""
    try:
        stats = confirmation_system.get_confirmation_statistics()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/receipt/<receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get payment receipt"""
    try:
        receipt = receipt_system.get_receipt(receipt_id)
        return jsonify(receipt)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/receipts/<payment_id>', methods=['GET'])
def get_receipts_by_payment(payment_id):
    """Get receipts by payment ID"""
    try:
        receipts = receipt_system.get_receipts_by_payment(payment_id)
        return jsonify({
            'success': True,
            'payment_id': payment_id,
            'receipts': receipts,
            'count': len(receipts)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/notification-status', methods=['GET'])
def get_notification_status():
    """Get notification system status"""
    try:
        status = notification_system.get_notification_status()
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enhanced/system-health', methods=['GET'])
def get_system_health():
    """Get overall system health"""
    try:
        # Verificar status de todos os sistemas
        notification_status = notification_system.get_notification_status()
        confirmation_stats = confirmation_system.get_confirmation_statistics()
        
        # Verificar banco de dados
        db_status = {
            'payments_count': len(payments_db),
            'file_exists': os.path.exists('payments.json'),
            'file_size': os.path.getsize('payments.json') if os.path.exists('payments.json') else 0
        }
        
        # Verificar configurações
        config_status = {
            'stripe_configured': bool(STRIPE_SECRET_KEY),
            'paypal_configured': bool(PAYPAL_CLIENT_ID),
            'smtp_configured': bool(SMTP_PASSWORD),
            'serial_generator_exists': os.path.exists(SERIAL_GENERATOR_PATH)
        }
        
        # Calcular saúde geral
        overall_health = 'healthy'
        if not config_status['stripe_configured'] or not config_status['smtp_configured']:
            overall_health = 'degraded'
        if not config_status['serial_generator_exists']:
            overall_health = 'critical'
        
        return jsonify({
            'success': True,
            'overall_health': overall_health,
            'timestamp': datetime.now().isoformat(),
            'systems': {
                'notifications': notification_status,
                'confirmations': confirmation_stats,
                'database': db_status,
                'configuration': config_status
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'overall_health': 'error'
        }), 500

@app.route('/api/enhanced/test-payment', methods=['POST'])
def test_enhanced_payment():
    """Test enhanced payment system"""
    try:
        data = request.get_json()
        
        # Dados de teste
        test_payment = {
            'id': f"test_{int(datetime.now().timestamp())}",
            'email': data.get('email', 'teste@exemplo.com'),
            'name': data.get('name', 'Cliente Teste'),
            'country': data.get('country', 'BR'),
            'amount': 500,  # $5.00
            'currency': 'USD',
            'method': data.get('method', 'stripe'),
            'status': 'test',
            'serial': EnhancedPaymentProcessor.generate_serial(data.get('email', 'teste@exemplo.com')),
            'created_at': datetime.now().isoformat()
        }
        
        # Armazenar pagamento de teste
        payments_db[test_payment['id']] = test_payment
        
        # Gerar comprovante
        receipt = receipt_system.generate_receipt(test_payment)
        
        # Adicionar confirmação
        confirmation_id = confirmation_system.add_confirmation_request(test_payment)
        
        # Enviar notificação de teste
        notification_system.send_payment_confirmation(test_payment)
        
        save_payments()
        
        return jsonify({
            'success': True,
            'message': 'Sistema de pagamentos testado com sucesso',
            'test_payment': test_payment,
            'receipt_id': receipt.get('id', ''),
            'confirmation_id': confirmation_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Upload payment proof endpoint
@app.route('/api/upload-payment-proof', methods=['POST'])
def upload_payment_proof():
    """Upload payment proof for PIX payments"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        payment_id = request.form.get('payment_id')
        email = request.form.get('email')
        
        if not payment_id:
            return jsonify({'error': 'Missing payment_id'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        # Check if payment exists
        payment = None
        if payment_id in payments_db:
            payment = payments_db[payment_id]
        else:
            return jsonify({
                'error': f'Payment ID "{payment_id}" não encontrado',
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
        payment['proof_uploaded_by'] = email or payment.get('email', 'unknown')
        payment['proof_filename'] = filename
        save_payments()
        
        # Send notification to admin
        try:
            EmailService.send_proof_pending_notification(
                payment.get('email', 'unknown'),
                payment.get('name', 'Cliente'),
                payment_id,
                payment['method'],
                payment['amount'],
                payment['currency'],
                filename,
                False
            )
        except Exception as e:
            print(f"❌ Erro ao enviar notificação: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Comprovante enviado com sucesso! Aguarde aprovação.',
            'payment_id': payment_id,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def save_payment_proof(file, payment_id):
    """Save uploaded payment proof file"""
    try:
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return None
        
        # Create uploads directory if it doesn't exist
        upload_dir = 'uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{payment_id}_{timestamp}_{file.filename}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(filepath)
        return filename
        
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return None

# Serve enhanced checkout page
@app.route('/enhanced_checkout.html')
def enhanced_checkout():
    """Serve enhanced checkout page"""
    return send_from_directory('../', 'enhanced_checkout.html')

# Serve upload test page
@app.route('/test_upload_page.html')
def test_upload_page():
    """Serve upload test page"""
    return send_from_directory('.', 'test_upload_page.html')

# ===== ROTAS ADMINISTRATIVAS =====

@app.route('/api/admin/pending-payments', methods=['GET'])
def admin_pending_payments():
    """Get pending payments for admin review"""
    try:
        pending_payments = []
        for payment_id, payment in payments_db.items():
            if payment.get('status') == 'pending':
                pending_payments.append({
                    'id': payment_id,
                    'email': payment.get('email', ''),
                    'amount': payment.get('amount', 0),
                    'method': payment.get('method', ''),
                    'timestamp': payment.get('timestamp', ''),
                    'proof_filename': payment.get('proof_filename', '')
                })
        
        return jsonify({
            'success': True,
            'pending_payments': pending_payments,
            'count': len(pending_payments)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/approve-payment', methods=['POST'])
def admin_approve_payment():
    """Approve a payment manually"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        
        if not payment_id or payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Update payment status
        payments_db[payment_id]['status'] = 'approved'
        payments_db[payment_id]['approved_at'] = datetime.now().isoformat()
        save_payments()
        
        return jsonify({
            'success': True,
            'message': 'Payment approved successfully',
            'payment_id': payment_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/view-proof/<payment_id>')
def admin_view_proof(payment_id):
    """View payment proof file"""
    try:
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payment = payments_db[payment_id]
        proof_filename = payment.get('proof_filename')
        
        if not proof_filename:
            return jsonify({'error': 'No proof file found'}), 404
        
        return send_from_directory('uploads', proof_filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/payments', methods=['GET'])
def admin_payments():
    """Get all payments for admin"""
    try:
        all_payments = []
        for payment_id, payment in payments_db.items():
            all_payments.append({
                'id': payment_id,
                'email': payment.get('email', ''),
                'amount': payment.get('amount', 0),
                'method': payment.get('method', ''),
                'status': payment.get('status', ''),
                'timestamp': payment.get('timestamp', ''),
                'proof_filename': payment.get('proof_filename', '')
            })
        
        return jsonify({
            'success': True,
            'payments': all_payments,
            'count': len(all_payments)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/payments/<payment_id>/approve', methods=['POST'])
def admin_approve_payment_by_id(payment_id):
    """Approve payment by ID"""
    try:
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payments_db[payment_id]['status'] = 'approved'
        payments_db[payment_id]['approved_at'] = datetime.now().isoformat()
        save_payments()
        
        return jsonify({
            'success': True,
            'message': 'Payment approved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/payments/<payment_id>/reject', methods=['POST'])
def admin_reject_payment_by_id(payment_id):
    """Reject payment by ID"""
    try:
        if payment_id not in payments_db:
            return jsonify({'error': 'Payment not found'}), 404
        
        payments_db[payment_id]['status'] = 'rejected'
        payments_db[payment_id]['rejected_at'] = datetime.now().isoformat()
        save_payments()
        
        return jsonify({
            'success': True,
            'message': 'Payment rejected successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/portal')
def admin_portal():
    """Admin portal page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Portal</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .payment { border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
            .pending { background-color: #fff3cd; }
            .approved { background-color: #d4edda; }
            .rejected { background-color: #f8d7da; }
            button { margin: 5px; padding: 5px 10px; }
        </style>
    </head>
    <body>
        <h1>Admin Portal - Payment Management</h1>
        <div id="payments"></div>
        
        <script>
            async function loadPayments() {
                try {
                    const response = await fetch('/api/admin/payments');
                    const data = await response.json();
                    
                    const container = document.getElementById('payments');
                    container.innerHTML = '';
                    
                    data.payments.forEach(payment => {
                        const div = document.createElement('div');
                        div.className = `payment ${payment.status}`;
                        div.innerHTML = `
                            <h3>Payment ID: ${payment.id}</h3>
                            <p>Email: ${payment.email}</p>
                            <p>Amount: $${payment.amount}</p>
                            <p>Method: ${payment.method}</p>
                            <p>Status: ${payment.status}</p>
                            <p>Date: ${payment.timestamp}</p>
                            ${payment.proof_filename ? `<p><a href="/api/admin/view-proof/${payment.id}" target="_blank">View Proof</a></p>` : ''}
                            ${payment.status === 'pending' ? `
                                <button onclick="approvePayment('${payment.id}')">Approve</button>
                                <button onclick="rejectPayment('${payment.id}')">Reject</button>
                            ` : ''}
                        `;
                        container.appendChild(div);
                    });
                } catch (error) {
                    console.error('Error loading payments:', error);
                }
            }
            
            async function approvePayment(paymentId) {
                try {
                    const response = await fetch(`/api/admin/payments/${paymentId}/approve`, {
                        method: 'POST'
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        alert('Payment approved successfully');
                        loadPayments();
                    } else {
                        alert('Error approving payment: ' + data.error);
                    }
                } catch (error) {
                    alert('Error approving payment: ' + error.message);
                }
            }
            
            async function rejectPayment(paymentId) {
                try {
                    const response = await fetch(`/api/admin/payments/${paymentId}/reject`, {
                        method: 'POST'
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        alert('Payment rejected successfully');
                        loadPayments();
                    } else {
                        alert('Error rejecting payment: ' + data.error);
                    }
                } catch (error) {
                    alert('Error rejecting payment: ' + error.message);
                }
            }
            
            // Load payments on page load
            loadPayments();
            
            // Refresh every 30 seconds
            setInterval(loadPayments, 30000);
        </script>
    </body>
    </html>
    """

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'features': [
                'Enhanced Payment Verification',
                'Automatic Confirmation System',
                'Real-time Notifications',
                'Receipt Generation',
                'Multi-method Support'
            ]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    
    print("🚀 Starting Enhanced Payment API Server...")
    print(f"📊 Serial Generator Path: {SERIAL_GENERATOR_PATH}")
    print(f"✅ Serial Generator Exists: {os.path.exists(SERIAL_GENERATOR_PATH)}")
    print("🔧 Advanced Systems Initialized:")
    print("   ✅ Payment Verification System")
    print("   ✅ Notification System")
    print("   ✅ Confirmation System")
    print("   ✅ Receipt System")
    
    # Get port from environment
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Server starting on port: {port}")
    print(f"🔧 Debug mode: {debug}")
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
