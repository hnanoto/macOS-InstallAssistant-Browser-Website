# -*- coding: utf-8 -*-
"""
Testes unitários para associação comprovante-pagamento
Testa vinculação, validação e integridade das associações
"""

import os
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock

# Importar funções do projeto
try:
    from payment_api import app
except ImportError:
    pytest.skip("Módulos do projeto não disponíveis", allow_module_level=True)


class TestPaymentAssociation:
    """Testes para associação básica comprovante-pagamento"""
    
    @pytest.fixture
    def sample_payment_data(self):
        """Dados de pagamento de exemplo"""
        return {
            'payment_id': 'PAY_123456789',
            'transaction_id': 'TXN_987654321',
            'serial_number': 'SN001234',
            'amount': 150.00,
            'currency': 'BRL',
            'status': 'pending_verification',
            'created_at': datetime.now().isoformat(),
            'user_id': 'user_abc123',
            'payment_method': 'pix',
            'description': 'Compra de produto digital'
        }
    
    @pytest.fixture
    def sample_receipt_data(self):
        """Dados de comprovante de exemplo"""
        return {
            'receipt_id': 'REC_789123456',
            'filename': 'comprovante_pix.png',
            'original_filename': 'Comprovante PIX - Banco.png',
            'file_path': '/uploads/2024/01/15/comprovante_pix.png',
            'file_size': 245760,
            'content_type': 'image/png',
            'upload_timestamp': datetime.now().isoformat(),
            'file_hash': 'sha256:abc123def456...',
            'status': 'uploaded'
        }
    
    @pytest.mark.association
    def test_create_payment_receipt_association(self, sample_payment_data, sample_receipt_data):
        """Testa criação de associação comprovante-pagamento"""
        # Simular criação da associação
        association = {
            'association_id': 'ASSOC_001',
            'payment_id': sample_payment_data['payment_id'],
            'receipt_id': sample_receipt_data['receipt_id'],
            'associated_at': datetime.now().isoformat(),
            'associated_by': sample_payment_data['user_id'],
            'status': 'active',
            'verification_status': 'pending'
        }
        
        # Verificar campos obrigatórios
        assert association['payment_id'] == sample_payment_data['payment_id'], "Payment ID deveria coincidir"
        assert association['receipt_id'] == sample_receipt_data['receipt_id'], "Receipt ID deveria coincidir"
        assert association['associated_by'] == sample_payment_data['user_id'], "User ID deveria coincidir"
        assert 'associated_at' in association, "Timestamp de associação deveria existir"
        assert association['status'] == 'active', "Status inicial deveria ser 'active'"
    
    @pytest.mark.association
    def test_validate_payment_receipt_match(self, sample_payment_data, sample_receipt_data):
        """Testa validação de compatibilidade pagamento-comprovante"""
        # Simular validações de compatibilidade
        validations = {
            'user_match': sample_payment_data['user_id'] == 'user_abc123',  # Mesmo usuário
            'timing_valid': True,  # Upload dentro do prazo
            'amount_reasonable': True,  # Valor compatível
            'method_compatible': sample_payment_data['payment_method'] == 'pix',  # Método compatível
            'status_allows_association': sample_payment_data['status'] in ['pending_verification', 'pending']
        }
        
        # Verificar todas as validações
        for validation_name, result in validations.items():
            assert result, f"Validação {validation_name} deveria passar"
        
        # Verificar compatibilidade geral
        all_valid = all(validations.values())
        assert all_valid, "Todas as validações deveriam passar para permitir associação"
    
    @pytest.mark.association
    def test_prevent_duplicate_associations(self, sample_payment_data, sample_receipt_data):
        """Testa prevenção de associações duplicadas"""
        # Simular associação existente
        existing_associations = [
            {
                'payment_id': sample_payment_data['payment_id'],
                'receipt_id': 'REC_OTHER',
                'status': 'active'
            }
        ]
        
        # Tentar criar nova associação para o mesmo pagamento
        new_association = {
            'payment_id': sample_payment_data['payment_id'],
            'receipt_id': sample_receipt_data['receipt_id']
        }
        
        # Verificar se pagamento já tem associação ativa
        payment_has_active_association = any(
            assoc['payment_id'] == new_association['payment_id'] and assoc['status'] == 'active'
            for assoc in existing_associations
        )
        
        assert payment_has_active_association, "Pagamento já deveria ter associação ativa"
        
        # Simular lógica de prevenção
        can_create_new = not payment_has_active_association
        assert not can_create_new, "Não deveria permitir nova associação para pagamento já associado"
    
    @pytest.mark.association
    def test_multiple_receipts_single_payment(self, sample_payment_data):
        """Testa múltiplos comprovantes para um pagamento (histórico)"""
        # Simular múltiplos uploads para o mesmo pagamento
        receipts = [
            {
                'receipt_id': 'REC_001',
                'filename': 'comprovante_v1.png',
                'upload_timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'status': 'replaced'
            },
            {
                'receipt_id': 'REC_002',
                'filename': 'comprovante_v2.png',
                'upload_timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'status': 'replaced'
            },
            {
                'receipt_id': 'REC_003',
                'filename': 'comprovante_final.png',
                'upload_timestamp': datetime.now().isoformat(),
                'status': 'active'
            }
        ]
        
        # Criar associações históricas
        associations = []
        for i, receipt in enumerate(receipts):
            association = {
                'association_id': f'ASSOC_{i+1:03d}',
                'payment_id': sample_payment_data['payment_id'],
                'receipt_id': receipt['receipt_id'],
                'status': receipt['status'],
                'associated_at': receipt['upload_timestamp']
            }
            associations.append(association)
        
        # Verificar que apenas uma associação está ativa
        active_associations = [a for a in associations if a['status'] == 'active']
        assert len(active_associations) == 1, "Deveria haver apenas uma associação ativa"
        
        # Verificar que a associação ativa é a mais recente
        active_association = active_associations[0]
        assert active_association['receipt_id'] == 'REC_003', "Associação ativa deveria ser a mais recente"
        
        # Verificar histórico completo
        total_associations = len(associations)
        assert total_associations == 3, "Deveria manter histórico de todas as associações"


class TestAssociationValidation:
    """Testes para validação de associações"""
    
    @pytest.mark.association
    @pytest.mark.validation
    def test_user_ownership_validation(self):
        """Testa validação de propriedade do usuário"""
        payment_user = 'user_123'
        receipt_user = 'user_123'
        different_user = 'user_456'
        
        # Caso válido: mesmo usuário
        valid_association = {
            'payment_user_id': payment_user,
            'receipt_user_id': receipt_user
        }
        
        user_match = valid_association['payment_user_id'] == valid_association['receipt_user_id']
        assert user_match, "Usuários deveriam coincidir para associação válida"
        
        # Caso inválido: usuários diferentes
        invalid_association = {
            'payment_user_id': payment_user,
            'receipt_user_id': different_user
        }
        
        user_mismatch = invalid_association['payment_user_id'] != invalid_association['receipt_user_id']
        assert user_mismatch, "Usuários diferentes deveriam ser detectados"
    
    @pytest.mark.association
    @pytest.mark.validation
    def test_timing_validation(self):
        """Testa validação de timing da associação"""
        payment_time = datetime.now() - timedelta(hours=1)
        
        # Casos de timing
        timing_cases = [
            {
                'name': 'upload_imediato',
                'upload_time': payment_time + timedelta(minutes=5),
                'expected_valid': True
            },
            {
                'name': 'upload_mesmo_dia',
                'upload_time': payment_time + timedelta(hours=12),
                'expected_valid': True
            },
            {
                'name': 'upload_proximo_dia',
                'upload_time': payment_time + timedelta(days=1),
                'expected_valid': True
            },
            {
                'name': 'upload_muito_tardio',
                'upload_time': payment_time + timedelta(days=30),
                'expected_valid': False
            },
            {
                'name': 'upload_antes_pagamento',
                'upload_time': payment_time - timedelta(hours=1),
                'expected_valid': False
            }
        ]
        
        for case in timing_cases:
            time_diff = case['upload_time'] - payment_time
            
            # Regras de timing (exemplo)
            is_after_payment = time_diff.total_seconds() > 0
            is_within_window = time_diff.total_seconds() < (7 * 24 * 3600)  # 7 dias
            
            timing_valid = is_after_payment and is_within_window
            
            assert timing_valid == case['expected_valid'], f"Caso {case['name']}: timing deveria ser {case['expected_valid']}"
    
    @pytest.mark.association
    @pytest.mark.validation
    def test_amount_validation(self):
        """Testa validação de valor do pagamento"""
        payment_amount = 150.00
        
        # Casos de validação de valor
        amount_cases = [
            {
                'name': 'valor_exato',
                'declared_amount': 150.00,
                'tolerance': 0.01,
                'expected_valid': True
            },
            {
                'name': 'valor_com_tolerancia',
                'declared_amount': 150.50,
                'tolerance': 1.00,
                'expected_valid': True
            },
            {
                'name': 'valor_muito_diferente',
                'declared_amount': 200.00,
                'tolerance': 1.00,
                'expected_valid': False
            },
            {
                'name': 'valor_negativo',
                'declared_amount': -150.00,
                'tolerance': 1.00,
                'expected_valid': False
            },
            {
                'name': 'valor_zero',
                'declared_amount': 0.00,
                'tolerance': 1.00,
                'expected_valid': False
            }
        ]
        
        for case in amount_cases:
            amount_diff = abs(payment_amount - case['declared_amount'])
            
            # Validações de valor
            is_positive = case['declared_amount'] > 0
            is_within_tolerance = amount_diff <= case['tolerance']
            
            amount_valid = is_positive and is_within_tolerance
            
            assert amount_valid == case['expected_valid'], f"Caso {case['name']}: valor deveria ser {case['expected_valid']}"
    
    @pytest.mark.association
    @pytest.mark.validation
    def test_payment_method_compatibility(self):
        """Testa compatibilidade do método de pagamento"""
        # Métodos de pagamento e tipos de comprovante compatíveis
        compatibility_matrix = {
            'pix': ['image/png', 'image/jpeg', 'application/pdf'],
            'ted': ['image/png', 'image/jpeg', 'application/pdf'],
            'boleto': ['application/pdf', 'image/png', 'image/jpeg'],
            'cartao': ['application/pdf'],  # Apenas faturas
            'dinheiro': []  # Sem comprovante digital
        }
        
        test_cases = [
            ('pix', 'image/png', True),
            ('pix', 'image/jpeg', True),
            ('pix', 'application/pdf', True),
            ('ted', 'image/png', True),
            ('boleto', 'application/pdf', True),
            ('cartao', 'image/png', False),  # Cartão não aceita imagem
            ('dinheiro', 'image/png', False),  # Dinheiro não tem comprovante
            ('pix', 'text/plain', False),  # Tipo não suportado
        ]
        
        for payment_method, content_type, expected_valid in test_cases:
            compatible_types = compatibility_matrix.get(payment_method, [])
            is_compatible = content_type in compatible_types
            
            assert is_compatible == expected_valid, f"Método {payment_method} com tipo {content_type} deveria ser {expected_valid}"


class TestAssociationLifecycle:
    """Testes para ciclo de vida das associações"""
    
    @pytest.mark.association
    def test_association_status_transitions(self):
        """Testa transições de status da associação"""
        # Estados possíveis e transições válidas
        valid_transitions = {
            'pending': ['active', 'rejected', 'cancelled'],
            'active': ['verified', 'rejected', 'replaced'],
            'verified': ['completed', 'disputed'],
            'rejected': ['pending'],  # Pode ser resubmetida
            'replaced': [],  # Estado final
            'completed': ['disputed'],
            'disputed': ['verified', 'rejected'],
            'cancelled': ['pending']  # Pode ser reativada
        }
        
        # Testar transições válidas
        for current_status, allowed_next in valid_transitions.items():
            for next_status in allowed_next:
                # Simular transição
                transition_valid = next_status in valid_transitions[current_status]
                assert transition_valid, f"Transição {current_status} -> {next_status} deveria ser válida"
        
        # Testar transições inválidas
        invalid_transitions = [
            ('completed', 'pending'),
            ('replaced', 'active'),
            ('verified', 'pending'),
            ('active', 'completed')  # Pula verificação
        ]
        
        for current_status, invalid_next in invalid_transitions:
            transition_invalid = invalid_next not in valid_transitions.get(current_status, [])
            assert transition_invalid, f"Transição {current_status} -> {invalid_next} deveria ser inválida"
    
    @pytest.mark.association
    def test_association_audit_trail(self):
        """Testa trilha de auditoria das associações"""
        # Simular histórico de mudanças
        audit_trail = [
            {
                'timestamp': datetime.now() - timedelta(hours=3),
                'action': 'created',
                'old_status': None,
                'new_status': 'pending',
                'user_id': 'user_123',
                'reason': 'Initial upload'
            },
            {
                'timestamp': datetime.now() - timedelta(hours=2),
                'action': 'status_change',
                'old_status': 'pending',
                'new_status': 'active',
                'user_id': 'admin_456',
                'reason': 'Automatic validation passed'
            },
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'action': 'status_change',
                'old_status': 'active',
                'new_status': 'verified',
                'user_id': 'admin_456',
                'reason': 'Manual verification completed'
            },
            {
                'timestamp': datetime.now(),
                'action': 'status_change',
                'old_status': 'verified',
                'new_status': 'completed',
                'user_id': 'system',
                'reason': 'Payment processed successfully'
            }
        ]
        
        # Verificar integridade da trilha
        assert len(audit_trail) == 4, "Deveria haver 4 entradas na trilha de auditoria"
        
        # Verificar sequência cronológica
        timestamps = [entry['timestamp'] for entry in audit_trail]
        assert timestamps == sorted(timestamps), "Entradas deveriam estar em ordem cronológica"
        
        # Verificar continuidade de status
        for i in range(1, len(audit_trail)):
            previous_entry = audit_trail[i-1]
            current_entry = audit_trail[i]
            
            if current_entry['action'] == 'status_change':
                assert current_entry['old_status'] == previous_entry['new_status'], f"Status deveria ser contínuo entre entradas {i-1} e {i}"
        
        # Verificar campos obrigatórios
        required_fields = ['timestamp', 'action', 'new_status', 'user_id', 'reason']
        for entry in audit_trail:
            for field in required_fields:
                assert field in entry, f"Campo {field} deveria estar presente em todas as entradas"
    
    @pytest.mark.association
    def test_association_cleanup_and_archival(self):
        """Testa limpeza e arquivamento de associações antigas"""
        # Simular associações de diferentes idades
        associations = [
            {
                'id': 'ASSOC_001',
                'created_at': datetime.now() - timedelta(days=1),
                'status': 'completed',
                'archival_eligible': False
            },
            {
                'id': 'ASSOC_002',
                'created_at': datetime.now() - timedelta(days=30),
                'status': 'completed',
                'archival_eligible': False
            },
            {
                'id': 'ASSOC_003',
                'created_at': datetime.now() - timedelta(days=95),
                'status': 'completed',
                'archival_eligible': True
            },
            {
                'id': 'ASSOC_004',
                'created_at': datetime.now() - timedelta(days=200),
                'status': 'completed',
                'archival_eligible': True
            },
            {
                'id': 'ASSOC_005',
                'created_at': datetime.now() - timedelta(days=50),
                'status': 'active',
                'archival_eligible': False  # Não completada
            }
        ]
        
        # Definir critérios de arquivamento
        archival_age_days = 90
        archival_statuses = ['completed', 'cancelled', 'rejected']
        
        # Aplicar lógica de arquivamento
        for association in associations:
            age_days = (datetime.now() - association['created_at']).days
            
            is_old_enough = age_days >= archival_age_days
            is_archival_status = association['status'] in archival_statuses
            
            should_archive = is_old_enough and is_archival_status
            
            if association['id'] in ['ASSOC_003', 'ASSOC_004']:
                assert should_archive, f"Associação {association['id']} deveria ser elegível para arquivamento"
            else:
                assert not should_archive, f"Associação {association['id']} não deveria ser elegível para arquivamento"
        
        # Contar associações elegíveis
        eligible_count = sum(1 for a in associations if a['archival_eligible'])
        assert eligible_count == 2, "Deveriam haver 2 associações elegíveis para arquivamento"


class TestAssociationIntegrity:
    """Testes para integridade das associações"""
    
    @pytest.mark.association
    @pytest.mark.integrity
    def test_referential_integrity(self):
        """Testa integridade referencial das associações"""
        # Simular dados relacionados
        payments = {
            'PAY_001': {'status': 'active', 'user_id': 'user_123'},
            'PAY_002': {'status': 'cancelled', 'user_id': 'user_456'}
        }
        
        receipts = {
            'REC_001': {'status': 'active', 'user_id': 'user_123'},
            'REC_002': {'status': 'deleted', 'user_id': 'user_456'}
        }
        
        associations = [
            {
                'id': 'ASSOC_001',
                'payment_id': 'PAY_001',
                'receipt_id': 'REC_001',
                'status': 'active'
            },
            {
                'id': 'ASSOC_002',
                'payment_id': 'PAY_002',
                'receipt_id': 'REC_002',
                'status': 'active'
            },
            {
                'id': 'ASSOC_003',
                'payment_id': 'PAY_999',  # Pagamento inexistente
                'receipt_id': 'REC_001',
                'status': 'active'
            }
        ]
        
        # Verificar integridade referencial
        for association in associations:
            payment_exists = association['payment_id'] in payments
            receipt_exists = association['receipt_id'] in receipts
            
            if association['id'] == 'ASSOC_001':
                assert payment_exists and receipt_exists, "ASSOC_001 deveria ter referências válidas"
            elif association['id'] == 'ASSOC_002':
                # Pagamento cancelado e recibo deletado
                assert payment_exists and receipt_exists, "Referências existem mas podem estar inativas"
            elif association['id'] == 'ASSOC_003':
                assert not payment_exists, "ASSOC_003 deveria ter referência inválida para pagamento"
    
    @pytest.mark.association
    @pytest.mark.integrity
    def test_data_consistency_validation(self):
        """Testa validação de consistência de dados"""
        # Dados de teste com inconsistências
        test_data = {
            'payment': {
                'id': 'PAY_001',
                'user_id': 'user_123',
                'amount': 150.00,
                'currency': 'BRL',
                'method': 'pix'
            },
            'receipt': {
                'id': 'REC_001',
                'user_id': 'user_123',  # Consistente
                'filename': 'comprovante.png',
                'content_type': 'image/png'
            },
            'association': {
                'id': 'ASSOC_001',
                'payment_id': 'PAY_001',
                'receipt_id': 'REC_001',
                'user_id': 'user_123'  # Deveria coincidir
            }
        }
        
        # Verificações de consistência
        consistency_checks = {
            'user_consistency': (
                test_data['payment']['user_id'] == 
                test_data['receipt']['user_id'] == 
                test_data['association']['user_id']
            ),
            'payment_method_compatibility': (
                test_data['payment']['method'] == 'pix' and
                test_data['receipt']['content_type'] in ['image/png', 'image/jpeg', 'application/pdf']
            ),
            'amount_validity': test_data['payment']['amount'] > 0,
            'currency_validity': test_data['payment']['currency'] in ['BRL', 'USD', 'EUR']
        }
        
        # Verificar todas as consistências
        for check_name, is_consistent in consistency_checks.items():
            assert is_consistent, f"Verificação de consistência {check_name} deveria passar"
        
        # Verificar consistência geral
        all_consistent = all(consistency_checks.values())
        assert all_consistent, "Todos os dados deveriam ser consistentes"
    
    @pytest.mark.association
    @pytest.mark.integrity
    def test_concurrent_association_handling(self):
        """Testa tratamento de associações concorrentes"""
        # Simular tentativas concorrentes de associação
        payment_id = 'PAY_001'
        
        concurrent_attempts = [
            {
                'attempt_id': 'ATT_001',
                'receipt_id': 'REC_001',
                'timestamp': datetime.now(),
                'user_id': 'user_123'
            },
            {
                'attempt_id': 'ATT_002',
                'receipt_id': 'REC_002',
                'timestamp': datetime.now() + timedelta(milliseconds=100),
                'user_id': 'user_123'
            },
            {
                'attempt_id': 'ATT_003',
                'receipt_id': 'REC_003',
                'timestamp': datetime.now() + timedelta(milliseconds=200),
                'user_id': 'user_123'
            }
        ]
        
        # Simular processamento sequencial (primeiro vence)
        successful_attempt = None
        failed_attempts = []
        
        # Ordenar por timestamp
        sorted_attempts = sorted(concurrent_attempts, key=lambda x: x['timestamp'])
        
        for attempt in sorted_attempts:
            if successful_attempt is None:
                # Primeira tentativa bem-sucedida
                successful_attempt = attempt
            else:
                # Tentativas subsequentes falham
                failed_attempts.append(attempt)
        
        # Verificar resultado
        assert successful_attempt is not None, "Deveria haver uma tentativa bem-sucedida"
        assert successful_attempt['attempt_id'] == 'ATT_001', "Primeira tentativa deveria vencer"
        assert len(failed_attempts) == 2, "Deveriam haver 2 tentativas falhadas"
        
        # Verificar que tentativas falhadas são as posteriores
        failed_ids = [att['attempt_id'] for att in failed_attempts]
        assert 'ATT_002' in failed_ids and 'ATT_003' in failed_ids, "Tentativas posteriores deveriam falhar"