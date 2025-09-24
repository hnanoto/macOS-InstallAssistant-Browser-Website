#!/usr/bin/env python3
"""
Sistema de Confirmação de Recebimento Automático
Garante que todas as transações sejam confirmadas e notificadas adequadamente
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentConfirmationSystem:
    """Sistema de confirmação de recebimento automático"""
    
    def __init__(self):
        self.confirmation_queue = []
        self.pending_confirmations = {}
        self.confirmation_attempts = {}
        self.max_attempts = 5
        self.retry_delay = 30  # segundos
        self.confirmation_timeout = 300  # 5 minutos
        
        # Iniciar processador de confirmações em background
        self._start_confirmation_processor()
    
    def _start_confirmation_processor(self):
        """Inicia processador de confirmações em background"""
        def process_confirmations():
            while True:
                try:
                    if self.confirmation_queue:
                        confirmation = self.confirmation_queue.pop(0)
                        self._process_confirmation(confirmation)
                    
                    # Processar confirmações pendentes
                    self._process_pending_confirmations()
                    
                    # Limpar confirmações expiradas
                    self._cleanup_expired_confirmations()
                    
                    time.sleep(10)  # Verificar a cada 10 segundos
                    
                except Exception as e:
                    logger.error(f"❌ Erro no processador de confirmações: {e}")
                    time.sleep(30)
        
        # Iniciar thread em background
        processor_thread = threading.Thread(target=process_confirmations, daemon=True)
        processor_thread.start()
        logger.info("🚀 Processador de confirmações iniciado")
    
    def add_confirmation_request(self, payment_data: Dict[str, Any]) -> str:
        """
        Adiciona solicitação de confirmação à fila
        """
        try:
            confirmation_id = f"conf_{int(time.time())}_{payment_data.get('payment_id', '')[:8]}"
            
            confirmation_request = {
                'id': confirmation_id,
                'payment_id': payment_data.get('payment_id', ''),
                'email': payment_data.get('email', ''),
                'name': payment_data.get('name', 'Cliente'),
                'amount': payment_data.get('amount', 0),
                'currency': payment_data.get('currency', ''),
                'method': payment_data.get('method', ''),
                'serial': payment_data.get('serial', ''),
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'attempts': 0,
                'last_attempt': None,
                'confirmed_at': None,
                'confirmation_data': payment_data
            }
            
            # Adicionar à fila
            self.confirmation_queue.append(confirmation_request)
            
            # Armazenar como pendente
            self.pending_confirmations[confirmation_id] = confirmation_request
            
            logger.info(f"📧 Solicitação de confirmação adicionada: {confirmation_id}")
            return confirmation_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar solicitação de confirmação: {e}")
            return ""
    
    def _process_confirmation(self, confirmation: Dict[str, Any]) -> bool:
        """
        Processa uma confirmação individual
        """
        try:
            confirmation_id = confirmation.get('id', '')
            payment_id = confirmation.get('payment_id', '')
            
            logger.info(f"🔄 Processando confirmação: {confirmation_id}")
            
            # Verificar se já foi confirmada
            if confirmation.get('status') == 'confirmed':
                logger.info(f"✅ Confirmação já processada: {confirmation_id}")
                return True
            
            # Verificar tentativas
            attempts = confirmation.get('attempts', 0)
            if attempts >= self.max_attempts:
                logger.error(f"❌ Máximo de tentativas atingido: {confirmation_id}")
                confirmation['status'] = 'failed'
                return False
            
            # Incrementar tentativas
            confirmation['attempts'] = attempts + 1
            confirmation['last_attempt'] = datetime.now().isoformat()
            
            # Tentar enviar confirmações
            success = self._send_confirmations(confirmation)
            
            if success:
                confirmation['status'] = 'confirmed'
                confirmation['confirmed_at'] = datetime.now().isoformat()
                logger.info(f"✅ Confirmação enviada com sucesso: {confirmation_id}")
            else:
                logger.warning(f"⚠️ Falha ao enviar confirmação: {confirmation_id}")
                # Reagendar para nova tentativa
                self._reschedule_confirmation(confirmation)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar confirmação: {e}")
            return False
    
    def _send_confirmations(self, confirmation: Dict[str, Any]) -> bool:
        """
        Envia confirmações para cliente e admin
        """
        try:
            # Importar sistema de notificações
            from notification_system import notification_system
            
            # Enviar confirmação para cliente
            customer_success = notification_system.send_payment_confirmation({
                'email': confirmation.get('email', ''),
                'name': confirmation.get('name', 'Cliente'),
                'payment_id': confirmation.get('payment_id', ''),
                'amount': confirmation.get('amount', 0),
                'currency': confirmation.get('currency', ''),
                'serial': confirmation.get('serial', ''),
                'method': confirmation.get('method', '')
            })
            
            # Enviar confirmação para admin
            admin_success = notification_system.send_payment_confirmation({
                'email': confirmation.get('email', ''),
                'name': confirmation.get('name', 'Cliente'),
                'payment_id': confirmation.get('payment_id', ''),
                'amount': confirmation.get('amount', 0),
                'currency': confirmation.get('currency', ''),
                'serial': confirmation.get('serial', ''),
                'method': confirmation.get('method', '')
            })
            
            # Salvar log de confirmação
            self._save_confirmation_log(confirmation, customer_success, admin_success)
            
            return customer_success and admin_success
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar confirmações: {e}")
            return False
    
    def _save_confirmation_log(self, confirmation: Dict[str, Any], customer_success: bool, admin_success: bool) -> None:
        """
        Salva log de confirmação
        """
        try:
            log_data = {
                'confirmation_id': confirmation.get('id', ''),
                'payment_id': confirmation.get('payment_id', ''),
                'email': confirmation.get('email', ''),
                'customer_success': customer_success,
                'admin_success': admin_success,
                'timestamp': datetime.now().isoformat(),
                'attempts': confirmation.get('attempts', 0)
            }
            
            with open('payment_confirmations.json', 'a') as f:
                f.write(json.dumps(log_data) + '\n')
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar log de confirmação: {e}")
    
    def _reschedule_confirmation(self, confirmation: Dict[str, Any]) -> None:
        """
        Reagenda confirmação para nova tentativa
        """
        try:
            confirmation_id = confirmation.get('id', '')
            
            # Calcular delay baseado no número de tentativas
            attempts = confirmation.get('attempts', 0)
            delay = self.retry_delay * (2 ** attempts)  # Backoff exponencial
            
            # Agendar para nova tentativa
            def retry_confirmation():
                time.sleep(delay)
                if confirmation_id in self.pending_confirmations:
                    self.confirmation_queue.append(confirmation)
            
            # Iniciar thread para retry
            retry_thread = threading.Thread(target=retry_confirmation, daemon=True)
            retry_thread.start()
            
            logger.info(f"⏰ Confirmação reagendada: {confirmation_id} (tentativa {attempts + 1} em {delay}s)")
            
        except Exception as e:
            logger.error(f"❌ Erro ao reagendar confirmação: {e}")
    
    def _process_pending_confirmations(self) -> None:
        """
        Processa confirmações pendentes
        """
        try:
            current_time = datetime.now()
            
            for confirmation_id, confirmation in list(self.pending_confirmations.items()):
                # Verificar se expirou
                created_at = datetime.fromisoformat(confirmation.get('created_at', ''))
                if current_time - created_at > timedelta(seconds=self.confirmation_timeout):
                    logger.warning(f"⏰ Confirmação expirada: {confirmation_id}")
                    confirmation['status'] = 'expired'
                    del self.pending_confirmations[confirmation_id]
                    continue
                
                # Verificar se precisa de nova tentativa
                last_attempt = confirmation.get('last_attempt')
                if last_attempt:
                    last_attempt_time = datetime.fromisoformat(last_attempt)
                    if current_time - last_attempt_time > timedelta(seconds=self.retry_delay):
                        if confirmation.get('status') == 'pending':
                            self.confirmation_queue.append(confirmation)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar confirmações pendentes: {e}")
    
    def _cleanup_expired_confirmations(self) -> None:
        """
        Limpa confirmações expiradas
        """
        try:
            current_time = datetime.now()
            expired_ids = []
            
            for confirmation_id, confirmation in self.pending_confirmations.items():
                created_at = datetime.fromisoformat(confirmation.get('created_at', ''))
                if current_time - created_at > timedelta(hours=24):  # Limpar após 24 horas
                    expired_ids.append(confirmation_id)
            
            for confirmation_id in expired_ids:
                del self.pending_confirmations[confirmation_id]
                logger.info(f"🗑️ Confirmação expirada removida: {confirmation_id}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao limpar confirmações expiradas: {e}")
    
    def get_confirmation_status(self, confirmation_id: str) -> Dict[str, Any]:
        """
        Obtém status de uma confirmação
        """
        try:
            if confirmation_id in self.pending_confirmations:
                confirmation = self.pending_confirmations[confirmation_id]
                return {
                    'success': True,
                    'confirmation_id': confirmation_id,
                    'status': confirmation.get('status', 'pending'),
                    'attempts': confirmation.get('attempts', 0),
                    'created_at': confirmation.get('created_at'),
                    'last_attempt': confirmation.get('last_attempt'),
                    'confirmed_at': confirmation.get('confirmed_at')
                }
            else:
                return {
                    'success': False,
                    'error': 'Confirmação não encontrada',
                    'confirmation_id': confirmation_id
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter status de confirmação: {e}")
            return {
                'success': False,
                'error': str(e),
                'confirmation_id': confirmation_id
            }
    
    def get_all_confirmations(self) -> Dict[str, Any]:
        """
        Obtém todas as confirmações
        """
        try:
            return {
                'success': True,
                'confirmations': list(self.pending_confirmations.values()),
                'queue_size': len(self.confirmation_queue),
                'total_pending': len(self.pending_confirmations)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter confirmações: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def force_confirmation(self, confirmation_id: str) -> bool:
        """
        Força confirmação específica
        """
        try:
            if confirmation_id in self.pending_confirmations:
                confirmation = self.pending_confirmations[confirmation_id]
                confirmation['attempts'] = 0  # Reset tentativas
                self.confirmation_queue.insert(0, confirmation)  # Prioridade alta
                logger.info(f"🚀 Confirmação forçada: {confirmation_id}")
                return True
            else:
                logger.error(f"❌ Confirmação não encontrada: {confirmation_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao forçar confirmação: {e}")
            return False
    
    def cancel_confirmation(self, confirmation_id: str) -> bool:
        """
        Cancela confirmação específica
        """
        try:
            if confirmation_id in self.pending_confirmations:
                confirmation = self.pending_confirmations[confirmation_id]
                confirmation['status'] = 'cancelled'
                del self.pending_confirmations[confirmation_id]
                logger.info(f"❌ Confirmação cancelada: {confirmation_id}")
                return True
            else:
                logger.error(f"❌ Confirmação não encontrada: {confirmation_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao cancelar confirmação: {e}")
            return False
    
    def get_confirmation_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas das confirmações
        """
        try:
            total_confirmations = len(self.pending_confirmations)
            confirmed_count = sum(1 for c in self.pending_confirmations.values() if c.get('status') == 'confirmed')
            pending_count = sum(1 for c in self.pending_confirmations.values() if c.get('status') == 'pending')
            failed_count = sum(1 for c in self.pending_confirmations.values() if c.get('status') == 'failed')
            
            # Calcular taxa de sucesso
            success_rate = (confirmed_count / total_confirmations * 100) if total_confirmations > 0 else 0
            
            return {
                'success': True,
                'statistics': {
                    'total_confirmations': total_confirmations,
                    'confirmed': confirmed_count,
                    'pending': pending_count,
                    'failed': failed_count,
                    'success_rate': round(success_rate, 2),
                    'queue_size': len(self.confirmation_queue)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class PaymentReceiptSystem:
    """Sistema de comprovantes de recebimento"""
    
    def __init__(self):
        self.receipts_db = {}
        self.load_receipts()
    
    def load_receipts(self) -> None:
        """
        Carrega comprovantes do arquivo
        """
        try:
            if os.path.exists('payment_receipts.json'):
                with open('payment_receipts.json', 'r') as f:
                    self.receipts_db = json.load(f)
                logger.info(f"📋 Carregados {len(self.receipts_db)} comprovantes")
            else:
                self.receipts_db = {}
                logger.info("📋 Nenhum comprovante encontrado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar comprovantes: {e}")
            self.receipts_db = {}
    
    def save_receipts(self) -> None:
        """
        Salva comprovantes no arquivo
        """
        try:
            with open('payment_receipts.json', 'w') as f:
                json.dump(self.receipts_db, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar comprovantes: {e}")
    
    def generate_receipt(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera comprovante de recebimento
        """
        try:
            payment_id = payment_data.get('payment_id', '')
            receipt_id = f"receipt_{payment_id}_{int(time.time())}"
            
            receipt = {
                'id': receipt_id,
                'payment_id': payment_id,
                'email': payment_data.get('email', ''),
                'name': payment_data.get('name', 'Cliente'),
                'amount': payment_data.get('amount', 0),
                'currency': payment_data.get('currency', ''),
                'method': payment_data.get('method', ''),
                'serial': payment_data.get('serial', ''),
                'status': 'generated',
                'generated_at': datetime.now().isoformat(),
                'receipt_data': payment_data
            }
            
            # Armazenar comprovante
            self.receipts_db[receipt_id] = receipt
            self.save_receipts()
            
            logger.info(f"📄 Comprovante gerado: {receipt_id}")
            return receipt
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar comprovante: {e}")
            return {}
    
    def get_receipt(self, receipt_id: str) -> Dict[str, Any]:
        """
        Obtém comprovante específico
        """
        try:
            if receipt_id in self.receipts_db:
                return {
                    'success': True,
                    'receipt': self.receipts_db[receipt_id]
                }
            else:
                return {
                    'success': False,
                    'error': 'Comprovante não encontrado',
                    'receipt_id': receipt_id
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter comprovante: {e}")
            return {
                'success': False,
                'error': str(e),
                'receipt_id': receipt_id
            }
    
    def get_receipts_by_payment(self, payment_id: str) -> List[Dict[str, Any]]:
        """
        Obtém comprovantes por ID de pagamento
        """
        try:
            receipts = []
            for receipt_id, receipt in self.receipts_db.items():
                if receipt.get('payment_id') == payment_id:
                    receipts.append(receipt)
            
            return receipts
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter comprovantes por pagamento: {e}")
            return []

# Instâncias globais
payment_confirmation_system = PaymentConfirmationSystem()
payment_receipt_system = PaymentReceiptSystem()
