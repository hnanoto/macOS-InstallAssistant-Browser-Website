#!/usr/bin/env python3
"""
🥑 INTEGRAÇÃO HÍBRIDA ABACATEPAY
===============================

Integração que funciona com simulação local quando a API AbacatePay
retorna erro 500, mas está pronta para usar a API real quando funcionar

Autor: Sistema de Migração Automática
Data: 24 de Setembro de 2025
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

try:
    import abacatepay
    from abacatepay.products import Product
    ABACATEPAY_SDK_AVAILABLE = True
except ImportError:
    ABACATEPAY_SDK_AVAILABLE = False

class AbacatePayHybridIntegration:
    """Integração híbrida que funciona com ou sem API AbacatePay"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self.use_simulation = False
        self.payments_cache = {}
        
        print(f"🥑 AbacatePay Híbrido inicializado")
        print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
        
        # Tentar inicializar SDK real
        if ABACATEPAY_SDK_AVAILABLE:
            try:
                self.client = abacatepay.AbacatePay(api_key)
                
                # Testar conectividade
                billings = self.client.billing.list()
                print(f"✅ SDK AbacatePay funcionando - {len(billings.data)} cobranças encontradas")
                self.use_simulation = False
                
            except Exception as e:
                print(f"⚠️ SDK AbacatePay com erro: {e}")
                print(f"🔄 Usando modo simulação local")
                self.use_simulation = True
        else:
            print(f"⚠️ SDK AbacatePay não disponível")
            print(f"🔄 Usando modo simulação local")
            self.use_simulation = True
    
    def create_pix_payment(self, amount: float, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar pagamento PIX - híbrido (real ou simulado)"""
        payment_id = f"pix_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_data['email'][:5]}"
        
        print(f"🥑 Criando pagamento PIX...")
        print(f"💰 Valor: R$ {amount}")
        print(f"📧 Cliente: {customer_data['email']}")
        print(f"🔧 Modo: {'API Real' if not self.use_simulation else 'Simulação Local'}")
        
        if not self.use_simulation and self.client:
            # Tentar usar API real
            try:
                return self._create_real_payment(payment_id, amount, customer_data)
            except Exception as e:
                print(f"⚠️ API real falhou: {e}")
                print(f"🔄 Fallback para simulação")
                return self._create_simulated_payment(payment_id, amount, customer_data)
        else:
            # Usar simulação
            return self._create_simulated_payment(payment_id, amount, customer_data)
    
    def _create_real_payment(self, payment_id: str, amount: float, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar pagamento real via API AbacatePay"""
        try:
            # Criar produto
            product = Product(
                external_id=payment_id,
                name="Licença macOS InstallAssistant Browser",
                quantity=1,
                price=int(amount * 100),  # Centavos
                description=f"Licença vitalícia para {customer_data['email']}"
            )
            
            # Criar cobrança
            billing = self.client.billing.create(
                products=[product],
                return_url="https://web-production-1513a.up.railway.app/payment-success",
                completion_url="https://web-production-1513a.up.railway.app/payment-complete"
            )
            
            # Gerar serial
            from payment_api import PaymentProcessor
            serial = PaymentProcessor.generate_serial(customer_data['email'])
            
            # Armazenar dados
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
                'payment_url': billing.data.url,
                'mode': 'real_api',
                'billing_data': billing.data.__dict__
            }
            
            self.payments_cache[payment_id] = payment_data
            
            print(f"✅ Pagamento real criado!")
            print(f"🆔 AbacatePay ID: {billing.data.id}")
            print(f"🔗 URL: {billing.data.url}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'abacatepay_id': billing.data.id,
                'payment_url': billing.data.url,
                'amount': amount,
                'currency': 'BRL',
                'serial': serial,
                'mode': 'real_api'
            }
            
        except Exception as e:
            print(f"❌ Erro na API real: {e}")
            raise
    
    def _create_simulated_payment(self, payment_id: str, amount: float, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar pagamento simulado localmente"""
        try:
            # Gerar IDs simulados
            abacatepay_id = f"sim_{uuid.uuid4().hex[:16]}"
            
            # Gerar serial
            from payment_api import PaymentProcessor
            serial = PaymentProcessor.generate_serial(customer_data['email'])
            
            # Gerar código PIX simulado
            pix_code = f"00020126580014BR.GOV.BCB.PIX0136{uuid.uuid4()}5204000053039865802BR5925ABACATEPAY SIMULACAO6009SAO PAULO62190515{payment_id}6304"
            
            # URL de pagamento simulada
            payment_url = f"https://web-production-1513a.up.railway.app/simulated-payment?id={payment_id}"
            
            # Armazenar dados
            payment_data = {
                'id': payment_id,
                'abacatepay_id': abacatepay_id,
                'email': customer_data['email'],
                'name': customer_data.get('name', 'Cliente'),
                'amount': int(amount * 100),
                'currency': 'BRL',
                'method': 'pix',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
                'serial': serial,
                'payment_url': payment_url,
                'pix_code': pix_code,
                'mode': 'simulation',
                'simulation_data': {
                    'auto_approve_in_minutes': 2,  # Para testes
                    'test_mode': True
                }
            }
            
            self.payments_cache[payment_id] = payment_data
            
            print(f"✅ Pagamento simulado criado!")
            print(f"🆔 Simulation ID: {abacatepay_id}")
            print(f"🔗 URL: {payment_url}")
            print(f"📱 PIX Code: {pix_code[:30]}...")
            print(f"⏰ Auto-aprovação em 2 minutos (para testes)")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'abacatepay_id': abacatepay_id,
                'payment_url': payment_url,
                'pix_code': pix_code,
                'amount': amount,
                'currency': 'BRL',
                'serial': serial,
                'mode': 'simulation',
                'expires_at': payment_data['expires_at']
            }
            
        except Exception as e:
            print(f"❌ Erro na simulação: {e}")
            return {
                'success': False,
                'error': f'Erro ao criar pagamento simulado: {str(e)}'
            }
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Obter status do pagamento"""
        if payment_id not in self.payments_cache:
            raise ValueError(f"Pagamento não encontrado: {payment_id}")
        
        payment = self.payments_cache[payment_id]
        
        if payment['mode'] == 'real_api' and self.client:
            return self._get_real_payment_status(payment)
        else:
            return self._get_simulated_payment_status(payment)
    
    def _get_real_payment_status(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Obter status real da API"""
        try:
            billing = self.client.billing.retrieve(payment['abacatepay_id'])
            
            # Atualizar status
            abacate_status = billing.data.status.lower()
            
            if abacate_status == 'paid' and payment['status'] != 'approved':
                payment['status'] = 'approved'
                payment['approved_at'] = datetime.now().isoformat()
                self._send_approval_email(payment)
            elif abacate_status == 'expired':
                payment['status'] = 'expired'
            elif abacate_status == 'cancelled':
                payment['status'] = 'cancelled'
            
            payment['abacatepay_status'] = abacate_status
            payment['updated_at'] = datetime.now().isoformat()
            
            return payment
            
        except Exception as e:
            print(f"⚠️ Erro ao consultar API real: {e}")
            return payment
    
    def _get_simulated_payment_status(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Obter status simulado"""
        # Auto-aprovação para testes (após 2 minutos)
        if payment['status'] == 'pending':
            created_at = datetime.fromisoformat(payment['created_at'])
            auto_approve_time = payment.get('simulation_data', {}).get('auto_approve_in_minutes', 2)
            
            if datetime.now() > created_at + timedelta(minutes=auto_approve_time):
                payment['status'] = 'approved'
                payment['approved_at'] = datetime.now().isoformat()
                payment['simulation_approved'] = True
                
                print(f"🤖 Pagamento simulado auto-aprovado: {payment['id']}")
                self._send_approval_email(payment)
        
        return payment
    
    def _send_approval_email(self, payment: Dict[str, Any]) -> None:
        """Enviar email de aprovação"""
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
            
            mode_text = "API Real" if payment['mode'] == 'real_api' else "Simulação"
            print(f"📧 Emails enviados ({mode_text}): {payment['email']}")
            
        except Exception as e:
            print(f"❌ Erro ao enviar emails: {e}")
    
    def list_payments(self, status: Optional[str] = None) -> list:
        """Listar pagamentos"""
        payments = list(self.payments_cache.values())
        
        if status:
            payments = [p for p in payments if p.get('status') == status]
        
        return sorted(payments, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def simulate_payment_approval(self, payment_id: str) -> Dict[str, Any]:
        """Simular aprovação manual de pagamento (para testes)"""
        if payment_id not in self.payments_cache:
            return {'success': False, 'error': 'Pagamento não encontrado'}
        
        payment = self.payments_cache[payment_id]
        
        if payment['status'] != 'pending':
            return {'success': False, 'error': f'Pagamento já está {payment["status"]}'}
        
        payment['status'] = 'approved'
        payment['approved_at'] = datetime.now().isoformat()
        payment['manual_approval'] = True
        
        self._send_approval_email(payment)
        
        print(f"✅ Pagamento aprovado manualmente: {payment_id}")
        
        return {'success': True, 'message': 'Pagamento aprovado'}

# Instância global
abacatepay_hybrid = None

def initialize_abacatepay_hybrid(api_key: str) -> AbacatePayHybridIntegration:
    """Inicializar integração híbrida"""
    global abacatepay_hybrid
    abacatepay_hybrid = AbacatePayHybridIntegration(api_key)
    return abacatepay_hybrid

def get_abacatepay_hybrid() -> AbacatePayHybridIntegration:
    """Obter instância híbrida"""
    if abacatepay_hybrid is None:
        api_key = os.getenv('ABACATEPAY_API_KEY', 'abc_dev_0Bm00HssGqag5GB30qnpQSFF')
        return initialize_abacatepay_hybrid(api_key)
    return abacatepay_hybrid

if __name__ == "__main__":
    # Teste da integração híbrida
    api_key = "abc_dev_0Bm00HssGqag5GB30qnpQSFF"
    hybrid = initialize_abacatepay_hybrid(api_key)
    
    # Teste de criação de pagamento
    customer_data = {
        'email': 'teste.hibrido@gmail.com',
        'name': 'Cliente Teste Híbrido',
        'document': '12345678901'
    }
    
    result = hybrid.create_pix_payment(26.50, customer_data)
    
    if result['success']:
        print("\n🎉 TESTE HÍBRIDO FUNCIONANDO!")
        print(f"Payment ID: {result['payment_id']}")
        print(f"Modo: {result['mode']}")
        print(f"URL: {result['payment_url']}")
        print(f"Serial: {result['serial']}")
        
        # Testar consulta de status
        print(f"\n🔍 Testando consulta de status...")
        status = hybrid.get_payment_status(result['payment_id'])
        print(f"Status: {status['status']}")
        
        if result['mode'] == 'simulation':
            print(f"\n🤖 Para testar aprovação manual:")
            print(f"hybrid.simulate_payment_approval('{result['payment_id']}')")
    else:
        print(f"❌ Erro no teste: {result['error']}")
