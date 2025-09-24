#!/usr/bin/env python3
"""
🥑 ROTAS ABACATEPAY - API Endpoints
==================================

Rotas da API integradas com AbacatePay
Mantém compatibilidade com sistema existente

Autor: Sistema de Migração Automática
Data: 24 de Setembro de 2025
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
from abacatepay_integration import abacatepay_processor, PaymentMethod

# Importar app Flask do sistema principal
try:
    from payment_api import app
except ImportError:
    # Se não conseguir importar, criar nova instância
    app = Flask(__name__)

# ==========================================
# ROTAS DE PAGAMENTO ABACATEPAY
# ==========================================

@app.route('/api/abacatepay/create-pix-payment', methods=['POST'])
def abacatepay_create_pix_payment():
    """Criar pagamento PIX via AbacatePay"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['email', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Preparar dados do cliente
        customer_data = {
            'email': data['email'],
            'name': data.get('name', 'Cliente'),
            'document': data.get('document'),
            'country': data.get('country', 'BR')
        }
        
        # Criar pagamento PIX
        result = abacatepay_processor.create_pix_payment(
            amount=float(data['amount']),
            customer_data=customer_data
        )
        
        if result['success']:
            print(f"✅ Pagamento PIX AbacatePay criado: {result['payment_id']}")
            return jsonify(result)
        else:
            print(f"❌ Erro ao criar pagamento PIX: {result['error']}")
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Erro na rota create-pix-payment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/create-card-payment', methods=['POST'])
def abacatepay_create_card_payment():
    """Criar pagamento com cartão via AbacatePay"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['email', 'amount', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Preparar dados do cliente
        customer_data = {
            'email': data['email'],
            'name': data['name'],
            'document': data.get('document'),
            'country': data.get('country', 'BR')
        }
        
        # Dados do cartão (se fornecidos)
        card_data = {
            'number': data.get('card_number'),
            'holder_name': data.get('card_holder_name'),
            'expiry_month': data.get('card_expiry_month'),
            'expiry_year': data.get('card_expiry_year'),
            'cvv': data.get('card_cvv')
        }
        
        # Criar pagamento com cartão
        result = abacatepay_processor.create_card_payment(
            amount=float(data['amount']),
            customer_data=customer_data,
            card_data=card_data
        )
        
        if result['success']:
            print(f"✅ Pagamento cartão AbacatePay criado: {result['payment_id']}")
            return jsonify(result)
        else:
            print(f"❌ Erro ao criar pagamento cartão: {result['error']}")
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Erro na rota create-card-payment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/webhook', methods=['POST'])
def abacatepay_webhook():
    """Webhook para receber notificações da AbacatePay"""
    try:
        # Obter dados do webhook
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-AbacatePay-Signature', '')
        
        print(f"🥑 Webhook AbacatePay recebido")
        print(f"📝 Payload size: {len(payload)} bytes")
        print(f"🔐 Signature: {signature[:20]}...")
        
        # Verificar assinatura (se configurada)
        if abacatepay_processor.config.webhook_secret:
            if not abacatepay_processor.client.verify_webhook(payload, signature):
                print("❌ Assinatura do webhook inválida")
                return jsonify({'error': 'Invalid signature'}), 401
        
        # Processar webhook
        webhook_data = json.loads(payload)
        result = abacatepay_processor.handle_webhook(webhook_data)
        
        if result['success']:
            print(f"✅ Webhook processado: {result['message']}")
            return jsonify(result)
        else:
            print(f"❌ Erro ao processar webhook: {result['error']}")
            return jsonify(result), 400
            
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON do webhook: {e}")
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/payment-status/<payment_id>', methods=['GET'])
def abacatepay_payment_status(payment_id):
    """Obter status de pagamento AbacatePay"""
    try:
        print(f"🔍 Consultando status AbacatePay: {payment_id}")
        
        payment = abacatepay_processor.get_payment_status(payment_id)
        
        # Formato compatível com API original
        response = {
            'id': payment['id'],
            'email': payment['email'],
            'name': payment['name'],
            'amount': payment['amount'],
            'currency': payment['currency'],
            'method': payment['method'],
            'status': payment['status'],
            'serial': payment.get('serial'),
            'created_at': payment['created_at'],
            'approved_at': payment.get('approved_at'),
            'abacatepay_id': payment.get('abacatepay_id'),
            'provider': 'abacatepay'
        }
        
        print(f"✅ Status encontrado: {payment['status']}")
        return jsonify(response)
        
    except ValueError as e:
        print(f"❌ Pagamento não encontrado: {payment_id}")
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        print(f"❌ Erro ao consultar status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/payments', methods=['GET'])
def abacatepay_list_payments():
    """Listar pagamentos AbacatePay (para painel admin)"""
    try:
        status_filter = request.args.get('status')
        
        print(f"📋 Listando pagamentos AbacatePay (status: {status_filter or 'todos'})")
        
        payments = abacatepay_processor.list_payments(status_filter)
        
        # Formato para painel admin
        formatted_payments = []
        for payment in payments:
            formatted_payments.append({
                'id': payment['id'],
                'email': payment['email'],
                'name': payment['name'],
                'amount': payment['amount'] / 100,  # Converter de centavos
                'currency': payment['currency'],
                'method': payment['method'],
                'status': payment['status'],
                'serial': payment.get('serial'),
                'created_at': payment['created_at'],
                'approved_at': payment.get('approved_at'),
                'abacatepay_id': payment.get('abacatepay_id'),
                'provider': 'abacatepay'
            })
        
        print(f"✅ {len(formatted_payments)} pagamentos encontrados")
        return jsonify({
            'payments': formatted_payments,
            'total': len(formatted_payments),
            'provider': 'abacatepay'
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar pagamentos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/cancel-payment/<payment_id>', methods=['POST'])
def abacatepay_cancel_payment(payment_id):
    """Cancelar pagamento AbacatePay"""
    try:
        print(f"❌ Cancelando pagamento AbacatePay: {payment_id}")
        
        # Obter dados do pagamento local
        payment = abacatepay_processor.get_payment_status(payment_id)
        abacatepay_id = payment.get('abacatepay_id')
        
        if not abacatepay_id:
            return jsonify({'error': 'ID AbacatePay não encontrado'}), 400
        
        # Cancelar na AbacatePay
        result = abacatepay_processor.client.cancel_payment(abacatepay_id)
        
        # Atualizar status local
        abacatepay_processor.payments_db[payment_id]['status'] = 'cancelled'
        abacatepay_processor.payments_db[payment_id]['cancelled_at'] = datetime.now().isoformat()
        
        print(f"✅ Pagamento cancelado: {payment_id}")
        return jsonify({
            'success': True,
            'message': 'Pagamento cancelado',
            'payment_id': payment_id,
            'abacatepay_result': result
        })
        
    except Exception as e:
        print(f"❌ Erro ao cancelar pagamento: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/refund-payment/<payment_id>', methods=['POST'])
def abacatepay_refund_payment(payment_id):
    """Estornar pagamento AbacatePay"""
    try:
        data = request.get_json() or {}
        refund_amount = data.get('amount')  # Valor do estorno (opcional)
        
        print(f"💸 Estornando pagamento AbacatePay: {payment_id}")
        
        # Obter dados do pagamento local
        payment = abacatepay_processor.get_payment_status(payment_id)
        abacatepay_id = payment.get('abacatepay_id')
        
        if not abacatepay_id:
            return jsonify({'error': 'ID AbacatePay não encontrado'}), 400
        
        # Estornar na AbacatePay
        result = abacatepay_processor.client.refund_payment(abacatepay_id, refund_amount)
        
        # Atualizar status local
        abacatepay_processor.payments_db[payment_id]['status'] = 'refunded'
        abacatepay_processor.payments_db[payment_id]['refunded_at'] = datetime.now().isoformat()
        if refund_amount:
            abacatepay_processor.payments_db[payment_id]['refund_amount'] = int(refund_amount * 100)
        
        print(f"✅ Pagamento estornado: {payment_id}")
        return jsonify({
            'success': True,
            'message': 'Pagamento estornado',
            'payment_id': payment_id,
            'refund_amount': refund_amount,
            'abacatepay_result': result
        })
        
    except Exception as e:
        print(f"❌ Erro ao estornar pagamento: {e}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTAS DE COMPATIBILIDADE
# ==========================================

@app.route('/api/abacatepay/migrate-from-legacy', methods=['POST'])
def migrate_from_legacy():
    """Migrar pagamento do sistema legado para AbacatePay"""
    try:
        data = request.get_json()
        legacy_payment_id = data.get('legacy_payment_id')
        
        if not legacy_payment_id:
            return jsonify({'error': 'legacy_payment_id é obrigatório'}), 400
        
        print(f"🔄 Migrando pagamento legado: {legacy_payment_id}")
        
        # Importar dados do sistema legado
        try:
            from payment_api import payments_db
            legacy_payment = payments_db.get(legacy_payment_id)
            
            if not legacy_payment:
                return jsonify({'error': 'Pagamento legado não encontrado'}), 404
            
            # Criar equivalente no AbacatePay (se ainda não foi pago)
            if legacy_payment.get('status') == 'pending':
                customer_data = {
                    'email': legacy_payment['email'],
                    'name': legacy_payment.get('name', 'Cliente'),
                    'country': legacy_payment.get('country', 'BR')
                }
                
                # Determinar método de pagamento
                if legacy_payment.get('method') == 'pix':
                    result = abacatepay_processor.create_pix_payment(
                        amount=legacy_payment['amount'] / 100,  # Converter de centavos
                        customer_data=customer_data
                    )
                else:
                    return jsonify({'error': 'Método de pagamento não suportado para migração'}), 400
                
                if result['success']:
                    # Marcar pagamento legado como migrado
                    legacy_payment['migrated_to_abacatepay'] = True
                    legacy_payment['abacatepay_payment_id'] = result['payment_id']
                    legacy_payment['migrated_at'] = datetime.now().isoformat()
                    
                    print(f"✅ Pagamento migrado: {legacy_payment_id} → {result['payment_id']}")
                    return jsonify({
                        'success': True,
                        'message': 'Pagamento migrado com sucesso',
                        'legacy_payment_id': legacy_payment_id,
                        'abacatepay_payment_id': result['payment_id'],
                        'abacatepay_data': result
                    })
                else:
                    return jsonify({'error': f'Erro na migração: {result["error"]}'}), 400
            else:
                return jsonify({'error': 'Pagamento legado já foi processado'}), 400
                
        except ImportError:
            return jsonify({'error': 'Sistema legado não disponível'}), 500
            
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/health', methods=['GET'])
def abacatepay_health():
    """Health check da integração AbacatePay"""
    try:
        # Testar conectividade com AbacatePay
        config_ok = bool(abacatepay_processor.config.api_key and abacatepay_processor.config.secret_key)
        
        status = {
            'status': 'healthy' if config_ok else 'unhealthy',
            'provider': 'abacatepay',
            'timestamp': datetime.now().isoformat(),
            'config': {
                'api_key_configured': bool(abacatepay_processor.config.api_key),
                'secret_key_configured': bool(abacatepay_processor.config.secret_key),
                'webhook_secret_configured': bool(abacatepay_processor.config.webhook_secret),
                'sandbox_mode': abacatepay_processor.config.sandbox_mode,
                'base_url': abacatepay_processor.config.base_url
            },
            'stats': {
                'total_payments': len(abacatepay_processor.payments_db),
                'pending_payments': len([p for p in abacatepay_processor.payments_db.values() if p.get('status') == 'pending']),
                'approved_payments': len([p for p in abacatepay_processor.payments_db.values() if p.get('status') == 'approved'])
            }
        }
        
        return jsonify(status)
        
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==========================================
# ROTAS DE ADMINISTRAÇÃO
# ==========================================

@app.route('/api/abacatepay/admin/dashboard', methods=['GET'])
def abacatepay_admin_dashboard():
    """Dashboard administrativo AbacatePay"""
    try:
        payments = abacatepay_processor.list_payments()
        
        # Estatísticas
        total_payments = len(payments)
        pending_payments = len([p for p in payments if p.get('status') == 'pending'])
        approved_payments = len([p for p in payments if p.get('status') == 'approved'])
        failed_payments = len([p for p in payments if p.get('status') == 'failed'])
        
        # Valor total
        total_amount = sum(p.get('amount', 0) for p in payments if p.get('status') == 'approved')
        
        dashboard_data = {
            'provider': 'abacatepay',
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total_payments': total_payments,
                'pending_payments': pending_payments,
                'approved_payments': approved_payments,
                'failed_payments': failed_payments,
                'total_revenue': total_amount / 100,  # Converter de centavos
                'currency': 'BRL'
            },
            'recent_payments': payments[:10]  # 10 mais recentes
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    print("🥑 Rotas AbacatePay carregadas")
    print("Endpoints disponíveis:")
    print("- POST /api/abacatepay/create-pix-payment")
    print("- POST /api/abacatepay/create-card-payment")
    print("- POST /api/abacatepay/webhook")
    print("- GET  /api/abacatepay/payment-status/<id>")
    print("- GET  /api/abacatepay/payments")
    print("- POST /api/abacatepay/cancel-payment/<id>")
    print("- POST /api/abacatepay/refund-payment/<id>")
    print("- GET  /api/abacatepay/health")
    print("- GET  /api/abacatepay/admin/dashboard")
