#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Confirmação Automática de Recebimento
Monitora pagamentos e confirma automaticamente quando detecta o recebimento
"""

import time
import threading
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auto_confirmation')

# Usamos o mesmo valor padrão do payment_api.py (8080) para evitar divergências
DEFAULT_INTERNAL_PORT = os.getenv('PORT', '8080')


def _normalizar_base(url: Optional[str]) -> Optional[str]:
    if not url:
        return None

    cleaned = url.strip()
    if not cleaned:
        return None

    # Se vier apenas host:porta, prefixamos http
    if '://' not in cleaned:
        cleaned = f"http://{cleaned}"

    return cleaned.rstrip('/')


def resolver_api_base_url(preferida: Optional[str] = None) -> str:
    """Descobre a melhor URL base para consultar a API principal."""

    candidatos = [
        preferida,
        os.getenv('AUTO_CONFIRMATION_API_BASE_URL'),
        os.getenv('INTERNAL_API_BASE_URL'),
        os.getenv('APP_BASE_URL'),
        os.getenv('RENDER_EXTERNAL_URL'),
        f"127.0.0.1:{DEFAULT_INTERNAL_PORT}",
    ]

    for candidato in candidatos:
        normalizado = _normalizar_base(candidato)
        if normalizado:
            return normalizado

    return f"http://127.0.0.1:{DEFAULT_INTERNAL_PORT}"


class AutoConfirmationSystem:
    """Sistema de confirmação automática de pagamentos"""

    def __init__(self, api_base_url: Optional[str] = None):
        self.api_base_url = resolver_api_base_url(api_base_url)
        self.monitoring = False
        self.monitor_thread = None
        self.confirmation_rules = {
            'pix': {
                'auto_confirm_after_minutes': 5,  # Confirmar PIX após 5 minutos
                'max_wait_hours': 24,  # Máximo 24 horas para confirmar
                'require_proof': False  # PIX não precisa de comprovante
            },
            'stripe': {
                'auto_confirm_after_minutes': 1,  # Confirmar Stripe após 1 minuto
                'max_wait_hours': 2,  # Máximo 2 horas
                'require_proof': False  # Stripe é automático
            },
            'paypal': {
                'auto_confirm_after_minutes': 2,  # Confirmar PayPal após 2 minutos
                'max_wait_hours': 4,  # Máximo 4 horas
                'require_proof': False  # PayPal é automático
            },
            'bank_transfer': {
                'auto_confirm_after_minutes': 60,  # Confirmar transferência após 1 hora
                'max_wait_hours': 72,  # Máximo 72 horas
                'require_proof': True  # Transferência precisa de comprovante
            }
        }
        
        # Estatísticas
        self.stats = {
            'total_monitored': 0,
            'auto_confirmed': 0,
            'manual_confirmations': 0,
            'expired_payments': 0,
            'errors': 0
        }
        
        logger.info(
            "🤖 Sistema de Confirmação Automática inicializado"
            f" | API base: {self.api_base_url}"
        )
    
    def start_monitoring(self):
        """Iniciar monitoramento automático"""
        if self.monitoring:
            logger.warning("⚠️ Monitoramento já está ativo")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_payments, daemon=True)
        self.monitor_thread.start()
        logger.info("🚀 Monitoramento automático iniciado")
    
    def stop_monitoring(self):
        """Parar monitoramento automático"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("⏹️ Monitoramento automático parado")
    
    def _monitor_payments(self):
        """Loop principal de monitoramento"""
        logger.info("🔍 Iniciando loop de monitoramento")
        
        while self.monitoring:
            try:
                # Buscar pagamentos pendentes
                pending_payments = self._get_pending_payments()
                
                if pending_payments:
                    logger.info(f"📋 Encontrados {len(pending_payments)} pagamentos pendentes")
                    
                    for payment in pending_payments:
                        self._process_payment(payment)
                        self.stats['total_monitored'] += 1
                
                # Aguardar antes da próxima verificação
                time.sleep(30)  # Verificar a cada 30 segundos
                
            except Exception as e:
                logger.error(f"💥 Erro no monitoramento: {str(e)}")
                self.stats['errors'] += 1
                time.sleep(60)  # Aguardar mais tempo em caso de erro
    
    def _get_pending_payments(self) -> List[Dict]:
        """Buscar pagamentos pendentes da API"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/admin/pending-payments",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                pending_entries = (
                    data.get('pending_payments')
                    or data.get('payments')
                    or []
                )

                normalized: List[Dict] = []
                for raw in pending_entries:
                    if not isinstance(raw, dict):
                        continue

                    normalized.append({
                        **raw,
                        'id': raw.get('id') or raw.get('payment_id'),
                        'status': raw.get('status') or raw.get('payment_status') or 'pending',
                    })

                return normalized
            else:
                logger.warning(f"⚠️ Erro ao buscar pagamentos: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"💥 Erro ao buscar pagamentos pendentes: {str(e)}")
            return []
    
    def _process_payment(self, payment: Dict):
        """Processar um pagamento individual"""
        payment_id = payment.get('id')
        payment_method = payment.get('method', 'unknown')
        created_at = payment.get('created_at')
        status = payment.get('status')
        
        if not payment_id:
            return
        
        logger.info(f"🔍 Processando pagamento {payment_id} ({payment_method})")
        
        # Verificar se deve ser confirmado automaticamente
        if self._should_auto_confirm(payment):
            self._auto_confirm_payment(payment)
        
        # Verificar se expirou
        elif self._is_payment_expired(payment):
            self._handle_expired_payment(payment)
    
    def _should_auto_confirm(self, payment: Dict) -> bool:
        """Verificar se um pagamento deve ser confirmado automaticamente"""
        payment_method = payment.get('method', 'unknown')
        created_at_str = payment.get('created_at')
        status = (payment.get('status') or '').lower()

        # Só confirmar pagamentos pendentes
        if status not in {'pending', 'pending_approval'}:
            return False
        
        # Verificar se temos regras para este método
        if payment_method not in self.confirmation_rules:
            logger.warning(f"⚠️ Método de pagamento desconhecido: {payment_method}")
            return False
        
        rules = self.confirmation_rules[payment_method]
        
        # Verificar se precisa de comprovante
        if rules['require_proof']:
            proof_uploaded = payment.get('proof_uploaded', False)
            if not proof_uploaded:
                logger.info(f"📎 Pagamento {payment.get('id')} aguardando comprovante")
                return False
        
        # Verificar tempo mínimo
        try:
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                now = datetime.now()
                minutes_elapsed = (now - created_at).total_seconds() / 60
                
                min_minutes = rules['auto_confirm_after_minutes']
                
                if minutes_elapsed >= min_minutes:
                    logger.info(f"⏰ Pagamento {payment.get('id')} elegível para confirmação automática")
                    return True
                else:
                    remaining = min_minutes - minutes_elapsed
                    logger.info(f"⏳ Pagamento {payment.get('id')} aguardando {remaining:.1f} minutos")
                    return False
            
        except Exception as e:
            logger.error(f"💥 Erro ao verificar tempo: {str(e)}")
            return False
        
        return False
    
    def _is_payment_expired(self, payment: Dict) -> bool:
        """Verificar se um pagamento expirou"""
        payment_method = payment.get('method', 'unknown')
        created_at_str = payment.get('created_at')
        
        if payment_method not in self.confirmation_rules:
            return False
        
        rules = self.confirmation_rules[payment_method]
        max_hours = rules['max_wait_hours']
        
        try:
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                now = datetime.now()
                hours_elapsed = (now - created_at).total_seconds() / 3600
                
                return hours_elapsed >= max_hours
                
        except Exception as e:
            logger.error(f"💥 Erro ao verificar expiração: {str(e)}")
            return False
        
        return False
    
    def _auto_confirm_payment(self, payment: Dict):
        """Confirmar pagamento automaticamente"""
        payment_id = payment.get('id')
        
        try:
            confirmation_data = {
                'payment_id': payment_id,
                'confirmed': True,
                'confirmation_method': 'automatic_system',
                'auto_confirmed': True,
                'confirmed_at': datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/auto-confirm-payment",
                json=confirmation_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('confirmed'):
                    logger.info(f"✅ Pagamento {payment_id} confirmado automaticamente")
                    self.stats['auto_confirmed'] += 1
                    
                    # Enviar notificação automática
                    self._send_auto_confirmation_notification(payment, data)
                else:
                    logger.warning(f"⚠️ Falha na confirmação automática de {payment_id}")
            else:
                logger.error(f"💥 Erro HTTP na confirmação: {response.status_code}")
                
        except Exception as e:
            logger.error(f"💥 Erro ao confirmar pagamento {payment_id}: {str(e)}")
            self.stats['errors'] += 1
    
    def _send_auto_confirmation_notification(self, payment: Dict, confirmation_data: Dict):
        """Enviar notificação de confirmação automática"""
        try:
            notification_data = {
                'payment_id': payment.get('id'),
                'type': 'payment_approved'
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/notifications/auto-process",
                json=notification_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"📧 Notificação de confirmação enviada para {payment.get('id')}")
            else:
                logger.warning(f"⚠️ Falha ao enviar notificação para {payment.get('id')}")
                
        except Exception as e:
            logger.error(f"💥 Erro ao enviar notificação: {str(e)}")
    
    def _handle_expired_payment(self, payment: Dict):
        """Lidar com pagamento expirado"""
        payment_id = payment.get('id')
        logger.warning(f"⏰ Pagamento {payment_id} expirou")
        self.stats['expired_payments'] += 1
        
        # Aqui você pode implementar lógica adicional para pagamentos expirados
        # Por exemplo: marcar como expirado, enviar notificação, etc.
    
    def get_stats(self) -> Dict:
        """Obter estatísticas do sistema"""
        return {
            **self.stats,
            'monitoring_active': self.monitoring,
            'uptime': datetime.now().isoformat()
        }
    
    def update_confirmation_rules(self, method: str, rules: Dict):
        """Atualizar regras de confirmação para um método"""
        if method in self.confirmation_rules:
            self.confirmation_rules[method].update(rules)
            logger.info(f"📝 Regras atualizadas para {method}: {rules}")
        else:
            logger.warning(f"⚠️ Método de pagamento desconhecido: {method}")
    
    def force_check_payment(self, payment_id: str) -> Dict:
        """Forçar verificação de um pagamento específico"""
        try:
            # Buscar dados do pagamento
            response = requests.get(
                f"{self.api_base_url}/api/payment-status/{payment_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                payment = response.json()
                
                if self._should_auto_confirm(payment):
                    self._auto_confirm_payment(payment)
                    return {'success': True, 'action': 'confirmed'}
                else:
                    return {'success': True, 'action': 'no_action_needed'}
            else:
                return {'success': False, 'error': f'Payment not found: {payment_id}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Instância global do sistema
auto_confirmation_system = AutoConfirmationSystem()

def start_auto_confirmation():
    """Iniciar sistema de confirmação automática"""
    auto_confirmation_system.start_monitoring()

def stop_auto_confirmation():
    """Parar sistema de confirmação automática"""
    auto_confirmation_system.stop_monitoring()

def get_auto_confirmation_stats():
    """Obter estatísticas do sistema"""
    return auto_confirmation_system.get_stats()

if __name__ == "__main__":
    print("🤖 Sistema de Confirmação Automática")
    print("Iniciando monitoramento...")
    
    try:
        auto_confirmation_system.start_monitoring()
        
        # Manter o programa rodando
        while True:
            time.sleep(10)
            stats = auto_confirmation_system.get_stats()
            print(f"📊 Stats: {stats}")
            
    except KeyboardInterrupt:
        print("\n⏹️ Parando sistema...")
        auto_confirmation_system.stop_monitoring()
        print("✅ Sistema parado")
