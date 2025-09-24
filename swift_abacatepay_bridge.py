#!/usr/bin/env python3
"""
🌉 BRIDGE SWIFT ↔ ABACATEPAY
============================

Mantém os endpoints Swift funcionando EXATAMENTE igual,
mas usa AbacatePay no backend de forma transparente.

O aplicativo macOS não precisa de NENHUMA mudança!
"""

from flask import Flask, request, jsonify
from datetime import datetime
from abacatepay_hybrid_integration import get_abacatepay_hybrid

# Evitar importação circular - app será injetado
app = None

def set_app(flask_app):
    """Definir app Flask externamente"""
    global app
    app = flask_app

def swift_process_purchase_abacatepay():
    """
    Endpoint que substitui o PIX manual por AbacatePay
    Mantém EXATA compatibilidade com aplicativo Swift
    """
    try:
        data = request.get_json()
        print(f"🍎 Swift → AbacatePay: process-purchase")
        print(f"📧 Email: {data.get('email')}")
        print(f"🔧 Método: {data.get('method')}")
        
        # Validar dados obrigatórios
        required_fields = ['email', 'method']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}'
                }), 400
        
        # Se for PIX, usar AbacatePay
        if data.get('method') == 'pix':
            print("🥑 Processando via AbacatePay...")
            
            # Preparar dados do cliente
            customer_data = {
                'email': data['email'],
                'name': data.get('name', 'Cliente macOS'),
                'document': data.get('document'),
                'country': 'BR'
            }
            
            # Criar pagamento via AbacatePay
            hybrid = get_abacatepay_hybrid()
            result = hybrid.create_pix_payment(26.50, customer_data)
            
            if result['success']:
                # Resposta no formato que o Swift espera
                response = {
                    'success': True,
                    'paymentId': result['payment_id'],
                    'serial': result['serial'],
                    'pixCode': result.get('pix_code', 'PIX_CODE_ABACATEPAY'),
                    'paypalUrl': None,  # Não usado para PIX
                    'message': 'Pagamento PIX criado via AbacatePay'
                }
                
                print(f"✅ Pagamento AbacatePay criado: {result['payment_id']}")
                return jsonify(response)
            else:
                print(f"❌ Erro AbacatePay: {result['error']}")
                return jsonify({
                    'success': False,
                    'error': f'Erro ao processar pagamento: {result["error"]}'
                }), 400
        
        # Se for PayPal, manter lógica original
        elif data.get('method') == 'paypal':
            print("💳 Processando PayPal (lógica original)...")
            
            # Importar lógica original do PayPal
            from payment_api import PaymentProcessor
            
            # Gerar serial
            serial = PaymentProcessor.generate_serial(data['email'])
            payment_id = f"paypal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data['email'][:5]}"
            
            response = {
                'success': True,
                'paymentId': payment_id,
                'serial': serial,
                'pixCode': None,
                'paypalUrl': 'https://www.paypal.com/donate?business=jobsremoto79henri@gmail.com',
                'message': 'Pagamento PayPal criado'
            }
            
            print(f"✅ Pagamento PayPal criado: {payment_id}")
            return jsonify(response)
        
        else:
            return jsonify({
                'success': False,
                'error': 'Método de pagamento não suportado'
            }), 400
            
    except Exception as e:
        print(f"❌ Erro no bridge Swift→AbacatePay: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

def swift_confirm_payment_abacatepay():
    """
    Endpoint que confirma pagamento AbacatePay
    Mantém EXATA compatibilidade com aplicativo Swift
    """
    try:
        data = request.get_json()
        print(f"🍎 Swift → AbacatePay: confirm-payment")
        print(f"💳 Payment ID: {data.get('paymentId')}")
        print(f"📧 Email: {data.get('email')}")
        
        # Validar dados obrigatórios
        payment_id = data.get('paymentId')
        email = data.get('email')
        
        if not payment_id or not email:
            return jsonify({
                'success': False,
                'error': 'PaymentId e email são obrigatórios'
            }), 400
        
        # Se for pagamento AbacatePay (PIX)
        if payment_id.startswith('pix_'):
            print("🥑 Confirmando via AbacatePay...")
            
            try:
                hybrid = get_abacatepay_hybrid()
                payment = hybrid.get_payment_status(payment_id)
                
                # Se já foi aprovado
                if payment['status'] == 'approved':
                    response = {
                        'success': True,
                        'serial': payment['serial'],
                        'message': 'Pagamento confirmado via AbacatePay',
                        'requiresProof': False,
                        'proofUploadURL': None
                    }
                    
                    print(f"✅ Pagamento já aprovado: {payment_id}")
                    return jsonify(response)
                
                # Se ainda está pendente
                elif payment['status'] == 'pending':
                    # Para simulação, aprovar automaticamente
                    if payment.get('mode') == 'simulation':
                        approval_result = hybrid.simulate_payment_approval(payment_id)
                        
                        if approval_result['success']:
                            # Buscar status atualizado
                            updated_payment = hybrid.get_payment_status(payment_id)
                            
                            response = {
                                'success': True,
                                'serial': updated_payment['serial'],
                                'message': 'Pagamento aprovado via simulação AbacatePay',
                                'requiresProof': False,
                                'proofUploadURL': None
                            }
                            
                            print(f"✅ Pagamento simulado aprovado: {payment_id}")
                            return jsonify(response)
                    
                    # Se não conseguiu aprovar automaticamente
                    response = {
                        'success': False,
                        'error': 'Pagamento ainda está sendo processado. Aguarde alguns minutos.',
                        'requiresProof': True,
                        'proofUploadURL': f'https://web-production-1513a.up.railway.app/upload-proof?payment_id={payment_id}'
                    }
                    
                    print(f"⏳ Pagamento pendente: {payment_id}")
                    return jsonify(response)
                
                # Se falhou
                else:
                    response = {
                        'success': False,
                        'error': f'Pagamento {payment["status"]}',
                        'requiresProof': False,
                        'proofUploadURL': None
                    }
                    
                    print(f"❌ Pagamento falhou: {payment_id} - {payment['status']}")
                    return jsonify(response)
                    
            except ValueError:
                # Pagamento não encontrado no AbacatePay
                response = {
                    'success': False,
                    'error': 'Pagamento não encontrado. Verifique o ID.',
                    'requiresProof': True,
                    'proofUploadURL': f'https://web-production-1513a.up.railway.app/upload-proof?payment_id={payment_id}'
                }
                
                print(f"❌ Pagamento não encontrado: {payment_id}")
                return jsonify(response)
        
        # Se for pagamento PayPal (lógica original)
        elif payment_id.startswith('paypal_'):
            print("💳 Confirmando PayPal (lógica original)...")
            
            # Para PayPal, simular confirmação imediata
            from payment_api import PaymentProcessor
            serial = PaymentProcessor.generate_serial(email)
            
            # Enviar email
            from payment_api import send_automated_customer_email, send_automated_admin_notification
            
            # Email para cliente
            send_automated_customer_email(
                email,
                'Cliente PayPal',
                serial,
                payment_id,
                500,  # $5.00 em centavos
                'USD'
            )
            
            # Email para admin
            send_automated_admin_notification(
                email,
                'Cliente PayPal',
                serial,
                payment_id,
                'paypal',
                500,
                'USD'
            )
            
            response = {
                'success': True,
                'serial': serial,
                'message': 'Pagamento PayPal confirmado',
                'requiresProof': False,
                'proofUploadURL': None
            }
            
            print(f"✅ Pagamento PayPal confirmado: {payment_id}")
            return jsonify(response)
        
        else:
            return jsonify({
                'success': False,
                'error': 'Tipo de pagamento não reconhecido'
            }), 400
            
    except Exception as e:
        print(f"❌ Erro na confirmação Swift→AbacatePay: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

# Função para substituir os endpoints originais
def enable_abacatepay_bridge(flask_app):
    """
    Substitui os endpoints Swift originais pelos que usam AbacatePay
    """
    global app
    app = flask_app
    
    print("🌉 Ativando Bridge Swift ↔ AbacatePay")
    
    try:
        # Substituir rotas existentes
        app.add_url_rule('/api/swift/process-purchase', 'swift_process_purchase_abacatepay', 
                        swift_process_purchase_abacatepay, methods=['POST'])
        app.add_url_rule('/api/swift/confirm-payment', 'swift_confirm_payment_abacatepay', 
                        swift_confirm_payment_abacatepay, methods=['POST'])
        
        print("✅ Bridge ativado - Aplicativo Swift agora usa AbacatePay!")
        return True
        
    except Exception as e:
        print(f"⚠️ Erro ao ativar bridge: {e}")
        return False

if __name__ == "__main__":
    print("🌉 Bridge Swift ↔ AbacatePay")
    print("Endpoints disponíveis:")
    print("- POST /api/swift/process-purchase (→ AbacatePay)")
    print("- POST /api/swift/confirm-payment (→ AbacatePay)")
    print("")
    print("✅ Aplicativo macOS funciona EXATAMENTE igual!")
    print("✅ Backend usa AbacatePay transparentemente!")
    
    # Testar bridge
    from abacatepay_hybrid_integration import get_abacatepay_hybrid
    hybrid = get_abacatepay_hybrid()
    print(f"🥑 AbacatePay: Modo {hybrid.use_simulation and 'Simulação' or 'API Real'}")
