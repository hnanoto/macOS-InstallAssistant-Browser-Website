#!/usr/bin/env python3
"""
🥑 INTEGRAÇÃO ABACATEPAY SDK OFICIAL
===================================

Integração usando o SDK oficial da AbacatePay
Baseado na documentação oficial e estrutura correta

Autor: Sistema de Migração Automática
Data: 24 de Setembro de 2025
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import abacatepay
from abacatepay.products import Product

class AbacatePaySDKIntegration:
    """Integração oficial com AbacatePay usando SDK"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = abacatepay.AbacatePay(api_key)
        self.payments_cache = {}
        
        print(f"🥑 AbacatePay SDK inicializado")
        print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    def create_pix_payment(self, amount: float, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar pagamento PIX usando SDK oficial"""
        try:
            payment_id = f"pix_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_data['email'][:5]}"
            
            print(f"🥑 Criando cobrança PIX AbacatePay...")
            print(f"💰 Valor: R$ {amount}")
            print(f"📧 Cliente: {customer_data['email']}")
            
            # Criar produto para a cobrança
            products = [
                Product(
                    external_id=payment_id,
                    name="Licença macOS InstallAssistant Browser",
                    quantity=1,
                    price=int(amount * 100),  # Converter para centavos
                    description=f"Licença vitalícia para {customer_data['email']}"
                )
            ]
            
            # URLs de retorno
            return_url = "https://web-production-1513a.up.railway.app/payment-success"
            completion_url = "https://web-production-1513a.up.railway.app/payment-complete"
            
            # Criar cobrança
            billing = self.client.billing.create(
                products=products,
                return_url=return_url,
                completion_url=completion_url
            )
            
            # Gerar serial (mantém lógica original)
            from payment_api import PaymentProcessor
            serial = PaymentProcessor.generate_serial(customer_data['email'])
            
            # Armazenar no cache local
            payment_data = {
                'id': payment_id,
                'abacatepay_id': billing.data.id,
                'email': customer_data['email'],
                'name': customer_data.get('name', 'Cliente'),
                'amount': int(amount * 100),
                'currency': 'BRL',
                'method': 'pix',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'serial': serial,
                'billing_url': billing.data.url,
                'billing_data': billing.data.__dict__
            }
            
            self.payments_cache[payment_id] = payment_data
            
            print(f"✅ Cobrança PIX criada com sucesso!")
            print(f"🆔 Payment ID: {payment_id}")
            print(f"🥑 AbacatePay ID: {billing.data.id}")
            print(f"🔑 Serial: {serial}")
            print(f"🔗 URL Pagamento: {billing.data.url}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'abacatepay_id': billing.data.id,
                'payment_url': billing.data.url,
                'amount': amount,
                'currency': 'BRL',
                'serial': serial,
                'qr_code': billing.data.url,  # URL pode ser usada para gerar QR
                'expires_at': None  # AbacatePay gerencia expiração
            }
            
        except Exception as e:
            print(f"❌ Erro ao criar cobrança PIX: {e}")
            return {
                'success': False,
                'error': f'Erro ao processar pagamento: {str(e)}'
            }
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Obter status do pagamento"""
        try:
            if payment_id not in self.payments_cache:
                raise ValueError(f"Pagamento não encontrado: {payment_id}")
            
            payment = self.payments_cache[payment_id]
            abacatepay_id = payment['abacatepay_id']
            
            # Consultar status na AbacatePay
            billing = self.client.billing.retrieve(abacatepay_id)
            
            # Atualizar status local baseado na AbacatePay
            abacate_status = billing.data.status.lower()
            
            if abacate_status == 'paid':
                payment['status'] = 'approved'
                payment['approved_at'] = datetime.now().isoformat()
                
                # Enviar email automático
                self._send_approval_email(payment)
            elif abacate_status == 'pending':
                payment['status'] = 'pending'
            elif abacate_status == 'expired':
                payment['status'] = 'expired'
            elif abacate_status == 'cancelled':
                payment['status'] = 'cancelled'
            
            payment['abacatepay_status'] = abacate_status
            payment['updated_at'] = datetime.now().isoformat()
            
            return payment
            
        except Exception as e:
            print(f"❌ Erro ao consultar status: {e}")
            raise
    
    def list_payments(self, status: Optional[str] = None) -> list:
        """Listar pagamentos"""
        payments = list(self.payments_cache.values())
        
        if status:
            payments = [p for p in payments if p.get('status') == status]
        
        # Ordenar por data de criação (mais recente primeiro)
        payments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return payments
    
    def _send_approval_email(self, payment: Dict[str, Any]) -> None:
        """Enviar email de aprovação (integração com sistema existente)"""
        try:
            from payment_api import send_automated_customer_email, send_automated_admin_notification
            
            # Email para cliente
            send_automated_customer_email(
                payment['email'],
                payment['name'],
                payment['serial'],
                payment['id'],
                payment['amount'],
                payment['currency']
            )
            
            # Email para admin
            send_automated_admin_notification(
                payment['email'],
                payment['name'],
                payment['serial'],
                payment['id'],
                payment['method'],
                payment['amount'],
                payment['currency']
            )
            
            print(f"📧 Emails de aprovação enviados para: {payment['email']}")
            
        except Exception as e:
            print(f"❌ Erro ao enviar emails: {e}")
    
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processar webhook da AbacatePay"""
        try:
            print(f"🥑 Webhook AbacatePay recebido: {payload}")
            
            # Extrair dados do webhook
            billing_id = payload.get('billing', {}).get('id')
            event_type = payload.get('event')
            
            if not billing_id:
                return {'success': False, 'error': 'Billing ID não encontrado'}
            
            # Encontrar pagamento local
            payment = None
            for p in self.payments_cache.values():
                if p.get('abacatepay_id') == billing_id:
                    payment = p
                    break
            
            if not payment:
                print(f"⚠️ Pagamento não encontrado para billing ID: {billing_id}")
                return {'success': False, 'error': 'Pagamento não encontrado'}
            
            # Processar evento
            if event_type == 'billing.paid':
                payment['status'] = 'approved'
                payment['approved_at'] = datetime.now().isoformat()
                
                print(f"✅ Pagamento aprovado via webhook: {payment['id']}")
                
                # Enviar emails
                self._send_approval_email(payment)
                
                return {'success': True, 'message': 'Pagamento aprovado'}
                
            elif event_type == 'billing.expired':
                payment['status'] = 'expired'
                payment['expired_at'] = datetime.now().isoformat()
                
                print(f"⏰ Pagamento expirado: {payment['id']}")
                
                return {'success': True, 'message': 'Pagamento expirado'}
            
            else:
                print(f"ℹ️ Evento não processado: {event_type}")
                return {'success': True, 'message': f'Evento {event_type} recebido'}
                
        except Exception as e:
            print(f"❌ Erro ao processar webhook: {e}")
            return {'success': False, 'error': str(e)}

# Instância global do integrador
abacatepay_sdk = None

def initialize_abacatepay_sdk(api_key: str) -> AbacatePaySDKIntegration:
    """Inicializar SDK da AbacatePay"""
    global abacatepay_sdk
    abacatepay_sdk = AbacatePaySDKIntegration(api_key)
    return abacatepay_sdk

def get_abacatepay_sdk() -> AbacatePaySDKIntegration:
    """Obter instância do SDK"""
    if abacatepay_sdk is None:
        api_key = os.getenv('ABACATEPAY_API_KEY', 'abc_dev_0Bm00HssGqag5GB30qnpQSFF')
        return initialize_abacatepay_sdk(api_key)
    return abacatepay_sdk

if __name__ == "__main__":
    # Teste do SDK
    api_key = "abc_dev_0Bm00HssGqag5GB30qnpQSFF"
    sdk = initialize_abacatepay_sdk(api_key)
    
    # Teste de criação de pagamento
    customer_data = {
        'email': 'teste.sdk@gmail.com',
        'name': 'Cliente Teste SDK',
        'document': '12345678901'
    }
    
    result = sdk.create_pix_payment(26.50, customer_data)
    
    if result['success']:
        print("🎉 TESTE SDK ABACATEPAY FUNCIONANDO!")
        print(f"Payment ID: {result['payment_id']}")
        print(f"URL: {result['payment_url']}")
    else:
        print(f"❌ Erro no teste: {result['error']}")
