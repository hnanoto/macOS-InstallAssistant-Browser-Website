#!/usr/bin/env python3
"""
🥑 ROTAS API ABACATEPAY HÍBRIDAS
===============================

Rotas da API que funcionam com AbacatePay real ou simulação
Integração completa com sistema existente

Autor: Sistema de Migração Automática
Data: 24 de Setembro de 2025
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

# Importar integração híbrida
from abacatepay_hybrid_integration import get_abacatepay_hybrid

# Importar app Flask do sistema principal
try:
    from payment_api import app
except ImportError:
    app = Flask(__name__)

# ==========================================
# ROTAS ABACATEPAY HÍBRIDAS
# ==========================================

@app.route('/api/abacatepay/create-pix-payment', methods=['POST'])
def abacatepay_create_pix_payment():
    """Criar pagamento PIX via AbacatePay (híbrido)"""
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
        
        # Obter instância híbrida
        hybrid = get_abacatepay_hybrid()
        
        # Criar pagamento PIX
        result = hybrid.create_pix_payment(
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

@app.route('/api/abacatepay/payment-status/<payment_id>', methods=['GET'])
def abacatepay_payment_status(payment_id):
    """Obter status de pagamento AbacatePay"""
    try:
        print(f"🔍 Consultando status AbacatePay: {payment_id}")
        
        hybrid = get_abacatepay_hybrid()
        payment = hybrid.get_payment_status(payment_id)
        
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
            'payment_url': payment.get('payment_url'),
            'pix_code': payment.get('pix_code'),
            'mode': payment.get('mode', 'unknown'),
            'provider': 'abacatepay'
        }
        
        print(f"✅ Status encontrado: {payment['status']} ({payment.get('mode', 'unknown')})")
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
        
        hybrid = get_abacatepay_hybrid()
        payments = hybrid.list_payments(status_filter)
        
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
                'payment_url': payment.get('payment_url'),
                'mode': payment.get('mode', 'unknown'),
                'provider': 'abacatepay'
            })
        
        print(f"✅ {len(formatted_payments)} pagamentos encontrados")
        return jsonify({
            'payments': formatted_payments,
            'total': len(formatted_payments),
            'provider': 'abacatepay',
            'modes': list(set(p.get('mode', 'unknown') for p in payments))
        })
        
    except Exception as e:
        print(f"❌ Erro ao listar pagamentos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/simulate-approval/<payment_id>', methods=['POST'])
def abacatepay_simulate_approval(payment_id):
    """Simular aprovação de pagamento (para testes)"""
    try:
        print(f"🤖 Simulando aprovação: {payment_id}")
        
        hybrid = get_abacatepay_hybrid()
        result = hybrid.simulate_payment_approval(payment_id)
        
        if result['success']:
            print(f"✅ Aprovação simulada: {payment_id}")
            return jsonify(result)
        else:
            print(f"❌ Erro na aprovação simulada: {result['error']}")
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Erro na simulação: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/abacatepay/health', methods=['GET'])
def abacatepay_health():
    """Health check da integração AbacatePay híbrida"""
    try:
        hybrid = get_abacatepay_hybrid()
        
        status = {
            'status': 'healthy',
            'provider': 'abacatepay_hybrid',
            'timestamp': datetime.now().isoformat(),
            'config': {
                'api_key_configured': bool(hybrid.api_key),
                'sdk_available': hybrid.client is not None,
                'simulation_mode': hybrid.use_simulation,
                'mode': 'simulation' if hybrid.use_simulation else 'real_api'
            },
            'stats': {
                'total_payments': len(hybrid.payments_cache),
                'pending_payments': len([p for p in hybrid.payments_cache.values() if p.get('status') == 'pending']),
                'approved_payments': len([p for p in hybrid.payments_cache.values() if p.get('status') == 'approved'])
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

@app.route('/api/abacatepay/admin/dashboard', methods=['GET'])
def abacatepay_admin_dashboard():
    """Dashboard administrativo AbacatePay"""
    try:
        hybrid = get_abacatepay_hybrid()
        payments = hybrid.list_payments()
        
        # Estatísticas
        total_payments = len(payments)
        pending_payments = len([p for p in payments if p.get('status') == 'pending'])
        approved_payments = len([p for p in payments if p.get('status') == 'approved'])
        failed_payments = len([p for p in payments if p.get('status') in ['failed', 'expired']])
        
        # Valor total
        total_amount = sum(p.get('amount', 0) for p in payments if p.get('status') == 'approved')
        
        # Estatísticas por modo
        real_api_count = len([p for p in payments if p.get('mode') == 'real_api'])
        simulation_count = len([p for p in payments if p.get('mode') == 'simulation'])
        
        dashboard_data = {
            'provider': 'abacatepay_hybrid',
            'timestamp': datetime.now().isoformat(),
            'mode': 'simulation' if hybrid.use_simulation else 'real_api',
            'stats': {
                'total_payments': total_payments,
                'pending_payments': pending_payments,
                'approved_payments': approved_payments,
                'failed_payments': failed_payments,
                'total_revenue': total_amount / 100,  # Converter de centavos
                'currency': 'BRL'
            },
            'mode_stats': {
                'real_api_payments': real_api_count,
                'simulation_payments': simulation_count,
                'current_mode': 'simulation' if hybrid.use_simulation else 'real_api'
            },
            'recent_payments': payments[:10]  # 10 mais recentes
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# ROTA DE COMPATIBILIDADE COM SISTEMA LEGADO
# ==========================================

@app.route('/api/create-pix-payment-abacatepay', methods=['POST'])
def create_pix_payment_abacatepay_compat():
    """Rota de compatibilidade que redireciona para AbacatePay"""
    try:
        data = request.get_json()
        
        print("🔄 Redirecionando pagamento PIX para AbacatePay...")
        
        # Redirecionar para endpoint AbacatePay
        return abacatepay_create_pix_payment()
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# PÁGINA DE PAGAMENTO SIMULADO
# ==========================================

@app.route('/simulated-payment')
def simulated_payment_page():
    """Página para pagamento simulado"""
    payment_id = request.args.get('id')
    
    if not payment_id:
        return "ID do pagamento não fornecido", 400
    
    try:
        hybrid = get_abacatepay_hybrid()
        payment = hybrid.get_payment_status(payment_id)
        
        # HTML da página de pagamento simulado
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pagamento PIX - AbacatePay (Simulação)</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 24px; color: #4CAF50; margin-bottom: 10px; }}
                .amount {{ font-size: 32px; font-weight: bold; color: #333; margin: 20px 0; }}
                .pix-code {{ background: #f8f9fa; padding: 20px; border-radius: 8px; font-family: monospace; font-size: 14px; word-break: break-all; margin: 20px 0; }}
                .status {{ padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; }}
                .status.pending {{ background: #fff3cd; color: #856404; }}
                .status.approved {{ background: #d4edda; color: #155724; }}
                .button {{ display: inline-block; background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .info {{ background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .simulation-notice {{ background: #ffe4e1; border: 2px solid #ff6b6b; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🥑 AbacatePay</div>
                    <h1>Pagamento PIX</h1>
                    <div class="amount">R$ {payment['amount']/100:.2f}</div>
                </div>
                
                <div class="simulation-notice">
                    <h3>🧪 MODO SIMULAÇÃO ATIVO</h3>
                    <p>Este é um pagamento simulado para testes. Nenhuma cobrança real será feita.</p>
                </div>
                
                <div class="status {'approved' if payment['status'] == 'approved' else 'pending'}">
                    {'✅ PAGAMENTO APROVADO!' if payment['status'] == 'approved' else '⏳ Aguardando Pagamento'}
                </div>
                
                <div class="info">
                    <h3>📋 Detalhes do Pagamento:</h3>
                    <p><strong>ID:</strong> {payment['id']}</p>
                    <p><strong>Cliente:</strong> {payment['name']} ({payment['email']})</p>
                    <p><strong>Produto:</strong> Licença macOS InstallAssistant Browser</p>
                    <p><strong>Status:</strong> {payment['status'].title()}</p>
                    {'<p><strong>Serial:</strong> ' + payment['serial'] + '</p>' if payment['status'] == 'approved' else ''}
                </div>
                
                {'<div class="pix-code"><strong>Código PIX:</strong><br>' + payment.get('pix_code', 'N/A') + '</div>' if payment['status'] != 'approved' else ''}
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="#" onclick="location.reload()" class="button">🔄 Atualizar Status</a>
                    {'<a href="#" onclick="approvePayment()" class="button">🤖 Simular Aprovação</a>' if payment['status'] == 'pending' else ''}
                </div>
                
                <div class="info">
                    <h3>🧪 Para Desenvolvedores:</h3>
                    <p>Este pagamento será aprovado automaticamente em 2 minutos.</p>
                    <p>Ou use o botão "Simular Aprovação" para aprovação imediata.</p>
                    <p><strong>API Endpoint:</strong> <code>/api/abacatepay/simulate-approval/{payment['id']}</code></p>
                </div>
            </div>
            
            <script>
                function approvePayment() {{
                    if (confirm('Simular aprovação deste pagamento?')) {{
                        fetch('/api/abacatepay/simulate-approval/{payment['id']}', {{
                            method: 'POST'
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.success) {{
                                alert('Pagamento aprovado com sucesso!');
                                location.reload();
                            }} else {{
                                alert('Erro: ' + data.error);
                            }}
                        }})
                        .catch(error => {{
                            alert('Erro na requisição: ' + error);
                        }});
                    }}
                }}
                
                // Auto-refresh a cada 30 segundos
                setTimeout(() => location.reload(), 30000);
            </script>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"Erro ao carregar pagamento: {str(e)}", 500

if __name__ == "__main__":
    print("🥑 Rotas AbacatePay Híbridas carregadas")
    print("Endpoints disponíveis:")
    print("- POST /api/abacatepay/create-pix-payment")
    print("- GET  /api/abacatepay/payment-status/<id>")
    print("- GET  /api/abacatepay/payments")
    print("- POST /api/abacatepay/simulate-approval/<id>")
    print("- GET  /api/abacatepay/health")
    print("- GET  /api/abacatepay/admin/dashboard")
    print("- GET  /simulated-payment?id=<payment_id>")
