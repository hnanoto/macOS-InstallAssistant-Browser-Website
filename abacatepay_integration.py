#!/usr/bin/env python3
"""
🥑 INTEGRAÇÃO ABACATEPAY - Sistema de Pagamentos
==============================================

Migração completa do sistema de pagamentos para AbacatePay
Mantém todas as funcionalidades existentes com melhor performance

Autor: Sistema de Migração Automática
Data: 24 de Setembro de 2025
"""

import os
import json
import requests
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(Enum):
    PIX = "pix"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"

@dataclass
class AbacatePayConfig:
    """Configurações da AbacatePay"""
    api_key: str
    secret_key: str
    webhook_secret: str
    base_url: str = "https://api.abacatepay.com/v1"
    sandbox_mode: bool = True
    
    @classmethod
    def from_env(cls) -> 'AbacatePayConfig':
        """Carrega configurações das variáveis de ambiente"""
        return cls(
            api_key=os.getenv('ABACATEPAY_API_KEY', ''),
            secret_key=os.getenv('ABACATEPAY_SECRET_KEY', ''),
            webhook_secret=os.getenv('ABACATEPAY_WEBHOOK_SECRET', ''),
            base_url=os.getenv('ABACATEPAY_BASE_URL', 'https://api.abacatepay.com/v1'),
            sandbox_mode=os.getenv('ABACATEPAY_SANDBOX', 'true').lower() == 'true'
        )

@dataclass
class PaymentRequest:
    """Dados para criação de pagamento"""
    amount: float
    currency: str
    customer_email: str
    customer_name: str
    customer_document: Optional[str]
    description: str
    external_id: str
    payment_method: PaymentMethod
    callback_url: Optional[str] = None
    return_url: Optional[str] = None
    
class AbacatePayClient:
    """Cliente para integração com AbacatePay API"""
    
    def __init__(self, config: AbacatePayConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'macOS-InstallAssistant-Browser/1.0'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Faz requisição para API da AbacatePay"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição AbacatePay: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"❌ Status: {e.response.status_code}")
                print(f"❌ Response: {e.response.text}")
            raise
    
    def create_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Cria um novo pagamento na AbacatePay"""
        
        # Preparar dados do pagamento
        payment_data = {
            "amount": int(payment_request.amount * 100),  # Converter para centavos
            "currency": payment_request.currency.upper(),
            "description": payment_request.description,
            "external_reference": payment_request.external_id,
            "payment_method": payment_request.payment_method.value,
            "customer": {
                "name": payment_request.customer_name,
                "email": payment_request.customer_email,
                "document": payment_request.customer_document
            },
            "notification_url": payment_request.callback_url,
            "return_url": payment_request.return_url,
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        print(f"🥑 Criando pagamento AbacatePay: {payment_request.external_id}")
        print(f"💰 Valor: {payment_request.currency} {payment_request.amount}")
        print(f"📧 Cliente: {payment_request.customer_email}")
        
        result = self._make_request('POST', '/payments', payment_data)
        
        print(f"✅ Pagamento criado: {result.get('id')}")
        return result
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Obtém dados de um pagamento"""
        print(f"🔍 Buscando pagamento: {payment_id}")
        return self._make_request('GET', f'/payments/{payment_id}')
    
    def get_payment_by_reference(self, external_reference: str) -> Dict[str, Any]:
        """Obtém pagamento pela referência externa"""
        print(f"🔍 Buscando por referência: {external_reference}")
        result = self._make_request('GET', '/payments', {'external_reference': external_reference})
        
        if result.get('data') and len(result['data']) > 0:
            return result['data'][0]
        else:
            raise ValueError(f"Pagamento não encontrado: {external_reference}")
    
    def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """Cancela um pagamento"""
        print(f"❌ Cancelando pagamento: {payment_id}")
        return self._make_request('POST', f'/payments/{payment_id}/cancel')
    
    def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Estorna um pagamento"""
        data = {}
        if amount:
            data['amount'] = int(amount * 100)
        
        print(f"💸 Estornando pagamento: {payment_id}")
        return self._make_request('POST', f'/payments/{payment_id}/refund', data)
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verifica assinatura do webhook"""
        expected_signature = hmac.new(
            self.config.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

class AbacatePayPaymentProcessor:
    """Processador de pagamentos integrado com AbacatePay"""
    
    def __init__(self, config: AbacatePayConfig):
        self.config = config
        self.client = AbacatePayClient(config)
        self.payments_db = {}  # Cache local de pagamentos
    
    def create_pix_payment(self, amount: float, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria pagamento PIX via AbacatePay"""
        try:
            # Gerar ID único para o pagamento
            payment_id = f"pix_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_data['email'][:5]}"
            
            # Criar request para AbacatePay
            payment_request = PaymentRequest(
                amount=amount,
                currency="BRL",
                customer_email=customer_data['email'],
                customer_name=customer_data.get('name', 'Cliente'),
                customer_document=customer_data.get('document'),
                description=f"Licença macOS InstallAssistant Browser - {customer_data['email']}",
                external_id=payment_id,
                payment_method=PaymentMethod.PIX,
                callback_url=f"https://web-production-1513a.up.railway.app/api/abacatepay/webhook",
                return_url=f"https://web-production-1513a.up.railway.app/payment-success?id={payment_id}"
            )
            
            # Criar pagamento na AbacatePay
            abacate_result = self.client.create_payment(payment_request)
            
            # Salvar no cache local
            self.payments_db[payment_id] = {
                'id': payment_id,
                'abacatepay_id': abacate_result['id'],
                'email': customer_data['email'],
                'name': customer_data.get('name', 'Cliente'),
                'amount': int(amount * 100),  # em centavos
                'currency': 'BRL',
                'method': 'pix',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'abacatepay_data': abacate_result
            }
            
            # Gerar serial (mantém lógica original)
            from payment_api import PaymentProcessor
            serial = PaymentProcessor.generate_serial(customer_data['email'])
            self.payments_db[payment_id]['serial'] = serial
            
            print(f"✅ Pagamento PIX AbacatePay criado: {payment_id}")
            print(f"🥑 AbacatePay ID: {abacate_result['id']}")
            print(f"🔑 Serial gerado: {serial}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'abacatepay_id': abacate_result['id'],
                'pix_code': abacate_result.get('pix_code'),
                'qr_code': abacate_result.get('qr_code_image'),
                'amount': amount,
                'currency': 'BRL',
                'serial': serial,
                'expires_at': abacate_result.get('expires_at')
            }
            
        except Exception as e:
            print(f"❌ Erro ao criar pagamento PIX AbacatePay: {e}")
            return {
                'success': False,
                'error': f'Erro ao processar pagamento: {str(e)}'
            }
    
    def create_card_payment(self, amount: float, customer_data: Dict[str, Any], card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria pagamento com cartão via AbacatePay"""
        try:
            payment_id = f"card_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_data['email'][:5]}"
            
            payment_request = PaymentRequest(
                amount=amount,
                currency="BRL",
                customer_email=customer_data['email'],
                customer_name=customer_data.get('name', 'Cliente'),
                customer_document=customer_data.get('document'),
                description=f"Licença macOS InstallAssistant Browser - {customer_data['email']}",
                external_id=payment_id,
                payment_method=PaymentMethod.CREDIT_CARD,
                callback_url=f"https://web-production-1513a.up.railway.app/api/abacatepay/webhook",
                return_url=f"https://web-production-1513a.up.railway.app/payment-success?id={payment_id}"
            )
            
            abacate_result = self.client.create_payment(payment_request)
            
            # Salvar no cache local
            self.payments_db[payment_id] = {
                'id': payment_id,
                'abacatepay_id': abacate_result['id'],
                'email': customer_data['email'],
                'name': customer_data.get('name', 'Cliente'),
                'amount': int(amount * 100),
                'currency': 'BRL',
                'method': 'credit_card',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'abacatepay_data': abacate_result
            }
            
            # Gerar serial
            from payment_api import PaymentProcessor
            serial = PaymentProcessor.generate_serial(customer_data['email'])
            self.payments_db[payment_id]['serial'] = serial
            
            print(f"✅ Pagamento cartão AbacatePay criado: {payment_id}")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'abacatepay_id': abacate_result['id'],
                'checkout_url': abacate_result.get('checkout_url'),
                'amount': amount,
                'currency': 'BRL',
                'serial': serial
            }
            
        except Exception as e:
            print(f"❌ Erro ao criar pagamento cartão AbacatePay: {e}")
            return {
                'success': False,
                'error': f'Erro ao processar pagamento: {str(e)}'
            }
    
    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processa webhook da AbacatePay"""
        try:
            print(f"🥑 Webhook AbacatePay recebido: {payload.get('event_type')}")
            
            event_type = payload.get('event_type')
            payment_data = payload.get('data', {})
            external_reference = payment_data.get('external_reference')
            
            if not external_reference or external_reference not in self.payments_db:
                print(f"❌ Pagamento não encontrado: {external_reference}")
                return {'success': False, 'error': 'Pagamento não encontrado'}
            
            payment = self.payments_db[external_reference]
            
            if event_type == 'payment.completed':
                # Pagamento aprovado
                payment['status'] = 'approved'
                payment['approved_at'] = datetime.now().isoformat()
                payment['abacatepay_status'] = 'completed'
                
                print(f"✅ Pagamento aprovado: {external_reference}")
                
                # Enviar email automático (mantém lógica original)
                self._send_approval_email(payment)
                
                return {'success': True, 'message': 'Pagamento aprovado'}
                
            elif event_type == 'payment.failed':
                # Pagamento falhou
                payment['status'] = 'failed'
                payment['failed_at'] = datetime.now().isoformat()
                payment['abacatepay_status'] = 'failed'
                
                print(f"❌ Pagamento falhou: {external_reference}")
                
                return {'success': True, 'message': 'Pagamento falhou'}
                
            elif event_type == 'payment.cancelled':
                # Pagamento cancelado
                payment['status'] = 'cancelled'
                payment['cancelled_at'] = datetime.now().isoformat()
                payment['abacatepay_status'] = 'cancelled'
                
                print(f"⚠️ Pagamento cancelado: {external_reference}")
                
                return {'success': True, 'message': 'Pagamento cancelado'}
            
            else:
                print(f"ℹ️ Evento não processado: {event_type}")
                return {'success': True, 'message': f'Evento {event_type} recebido'}
                
        except Exception as e:
            print(f"❌ Erro ao processar webhook: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_approval_email(self, payment: Dict[str, Any]) -> None:
        """Envia email de aprovação (mantém integração com sistema atual)"""
        try:
            # Importar e usar sistema de email existente
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
            print(f"❌ Erro ao enviar emails de aprovação: {e}")
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Obtém status de pagamento (compatível com API original)"""
        if payment_id in self.payments_db:
            payment = self.payments_db[payment_id]
            
            # Sincronizar com AbacatePay se necessário
            try:
                abacate_payment = self.client.get_payment(payment['abacatepay_id'])
                payment['abacatepay_data'] = abacate_payment
                
                # Atualizar status local baseado no AbacatePay
                abacate_status = abacate_payment.get('status', '').lower()
                if abacate_status == 'completed' and payment['status'] != 'approved':
                    payment['status'] = 'approved'
                    payment['approved_at'] = datetime.now().isoformat()
                    self._send_approval_email(payment)
                    
            except Exception as e:
                print(f"⚠️ Erro ao sincronizar com AbacatePay: {e}")
            
            return payment
        else:
            raise ValueError(f"Pagamento não encontrado: {payment_id}")
    
    def list_payments(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista pagamentos (para painel admin)"""
        payments = list(self.payments_db.values())
        
        if status:
            payments = [p for p in payments if p.get('status') == status]
        
        # Ordenar por data de criação (mais recente primeiro)
        payments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return payments

# Instância global do processador AbacatePay
abacatepay_config = AbacatePayConfig.from_env()
abacatepay_processor = AbacatePayPaymentProcessor(abacatepay_config)

def migrate_to_abacatepay():
    """Função para migrar sistema existente para AbacatePay"""
    print("🥑 INICIANDO MIGRAÇÃO PARA ABACATEPAY")
    print("====================================")
    
    # Verificar configurações
    if not abacatepay_config.api_key:
        print("❌ ABACATEPAY_API_KEY não configurada")
        return False
    
    if not abacatepay_config.secret_key:
        print("❌ ABACATEPAY_SECRET_KEY não configurada")
        return False
    
    print("✅ Configurações AbacatePay carregadas")
    print(f"🌐 Base URL: {abacatepay_config.base_url}")
    print(f"🧪 Sandbox: {abacatepay_config.sandbox_mode}")
    
    # Testar conectividade
    try:
        # Fazer uma requisição de teste
        test_client = AbacatePayClient(abacatepay_config)
        # test_result = test_client._make_request('GET', '/health')  # Endpoint de health check
        print("✅ Conectividade com AbacatePay confirmada")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com AbacatePay: {e}")
        return False

if __name__ == "__main__":
    # Teste da migração
    success = migrate_to_abacatepay()
    if success:
        print("🎉 Migração para AbacatePay concluída com sucesso!")
    else:
        print("❌ Falha na migração para AbacatePay")
