# -*- coding: utf-8 -*-
"""
Testes de integração para fluxo completo de comprovantes
Testa o fluxo end-to-end desde upload até notificação
"""

import os
import json
import pytest
import tempfile
import time
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from io import BytesIO

# Importar funções do projeto
try:
    from payment_api import app
except ImportError:
    pytest.skip("Módulos do projeto não disponíveis", allow_module_level=True)


class TestCompleteReceiptFlow:
    """Testes do fluxo completo de comprovantes"""
    
    @pytest.fixture
    def complete_payment_data(self):
        """Dados completos para teste de pagamento"""
        return {
            'payment_id': 'PAY_INTEGRATION_001',
            'serial_number': 'SN_INT_001',
            'user_id': 'USER_001',
            'user_email': 'usuario@example.com',
            'user_name': 'João Silva',
            'amount': 250.00,
            'currency': 'BRL',
            'payment_method': 'PIX',
            'created_at': datetime.now().isoformat()
        }
    
    @pytest.fixture
    def valid_receipt_file(self):
        """Arquivo de comprovante válido para testes"""
        # Criar imagem PNG válida simples
        png_header = b'\x89PNG\r\n\x1a\n'
        ihdr_chunk = b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        idat_chunk = b'\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c'
        iend_chunk = b'\x00\x00\x00\x00IEND\xaeB`\x82'
        
        png_content = png_header + ihdr_chunk + idat_chunk + iend_chunk
        return BytesIO(png_content)
    
    @pytest.mark.integration
    def test_successful_complete_flow(self, client, complete_payment_data, valid_receipt_file):
        """Testa fluxo completo bem-sucedido"""
        payment_data = complete_payment_data
        
        # Etapa 1: Upload do comprovante
        upload_response = client.post('/upload_receipt', data={
            'payment_id': payment_data['payment_id'],
            'serial_number': payment_data['serial_number'],
            'user_id': payment_data['user_id'],
            'file': (valid_receipt_file, 'comprovante_pix.png')
        })
        
        # Verificar upload bem-sucedido
        assert upload_response.status_code in [200, 201], "Upload deveria ser bem-sucedido"
        
        upload_data = upload_response.get_json()
        assert 'receipt_id' in upload_data, "Resposta deveria conter ID do comprovante"
        assert upload_data['status'] == 'uploaded', "Status inicial deveria ser 'uploaded'"
        
        receipt_id = upload_data['receipt_id']
        
        # Etapa 2: Verificar associação com pagamento
        payment_response = client.get(f'/payment/{payment_data["payment_id"]}')
        assert payment_response.status_code == 200, "Pagamento deveria ser encontrado"
        
        payment_info = payment_response.get_json()
        assert 'receipt' in payment_info, "Pagamento deveria ter comprovante associado"
        assert payment_info['receipt']['id'] == receipt_id, "IDs deveriam coincidir"
        
        # Etapa 3: Processar comprovante (simulação)
        process_response = client.post(f'/receipt/{receipt_id}/process', json={
            'action': 'validate',
            'processor_id': 'AUTO_VALIDATOR'
        })
        
        assert process_response.status_code in [200, 202], "Processamento deveria ser aceito"
        
        # Etapa 4: Verificar status atualizado
        status_response = client.get(f'/receipt/{receipt_id}/status')
        assert status_response.status_code == 200, "Status deveria ser acessível"
        
        status_data = status_response.get_json()
        assert status_data['status'] in ['processing', 'verified'], "Status deveria ter sido atualizado"
        
        # Etapa 5: Simular verificação manual (se necessário)
        if status_data['status'] == 'processing':
            verify_response = client.post(f'/receipt/{receipt_id}/verify', json={
                'verified_by': 'ADMIN_001',
                'verification_result': 'approved',
                'notes': 'Comprovante válido - PIX confirmado'
            })
            
            assert verify_response.status_code == 200, "Verificação deveria ser bem-sucedida"
            
            # Verificar status final
            final_status_response = client.get(f'/receipt/{receipt_id}/status')
            final_status = final_status_response.get_json()
            assert final_status['status'] == 'verified', "Status final deveria ser 'verified'"
        
        # Etapa 6: Verificar notificação enviada
        notifications_response = client.get(f'/user/{payment_data["user_id"]}/notifications')
        assert notifications_response.status_code == 200, "Notificações deveriam ser acessíveis"
        
        notifications = notifications_response.get_json()
        assert len(notifications) > 0, "Pelo menos uma notificação deveria ter sido enviada"
        
        # Verificar conteúdo da notificação
        receipt_notifications = [
            n for n in notifications 
            if n.get('type') == 'receipt_status' and receipt_id in n.get('content', '')
        ]
        assert len(receipt_notifications) > 0, "Deveria haver notificação sobre o comprovante"
        
        # Etapa 7: Verificar histórico completo
        history_response = client.get(f'/receipt/{receipt_id}/history')
        assert history_response.status_code == 200, "Histórico deveria ser acessível"
        
        history = history_response.get_json()
        assert len(history) >= 3, "Deveria haver pelo menos 3 eventos no histórico"
        
        # Verificar eventos esperados
        event_types = {event['type'] for event in history}
        expected_events = {'uploaded', 'processing', 'verified'}
        assert expected_events.issubset(event_types), "Eventos esperados deveriam estar no histórico"
    
    @pytest.mark.integration
    def test_flow_with_rejection(self, client, complete_payment_data):
        """Testa fluxo com rejeição do comprovante"""
        payment_data = complete_payment_data
        
        # Criar arquivo inválido
        invalid_file = BytesIO(b'Invalid file content')
        
        # Upload de arquivo inválido
        upload_response = client.post('/upload_receipt', data={
            'payment_id': payment_data['payment_id'],
            'serial_number': payment_data['serial_number'],
            'user_id': payment_data['user_id'],
            'file': (invalid_file, 'invalid.txt')
        })
        
        # Verificar rejeição
        assert upload_response.status_code in [400, 422], "Arquivo inválido deveria ser rejeitado"
        
        error_data = upload_response.get_json()
        assert 'error' in error_data, "Resposta deveria conter erro"
        assert 'format' in error_data['error'].lower(), "Erro deveria mencionar formato"
        
        # Verificar que pagamento não foi afetado
        payment_response = client.get(f'/payment/{payment_data["payment_id"]}')
        if payment_response.status_code == 200:
            payment_info = payment_response.get_json()
            assert 'receipt' not in payment_info or payment_info['receipt'] is None, "Pagamento não deveria ter comprovante associado"
    
    @pytest.mark.integration
    def test_flow_with_duplicate_upload(self, client, complete_payment_data, valid_receipt_file):
        """Testa fluxo com tentativa de upload duplicado"""
        payment_data = complete_payment_data
        
        # Primeiro upload
        first_upload = client.post('/upload_receipt', data={
            'payment_id': payment_data['payment_id'],
            'serial_number': payment_data['serial_number'],
            'user_id': payment_data['user_id'],
            'file': (valid_receipt_file, 'comprovante_1.png')
        })
        
        assert first_upload.status_code in [200, 201], "Primeiro upload deveria ser bem-sucedido"
        first_data = first_upload.get_json()
        first_receipt_id = first_data['receipt_id']
        
        # Segundo upload (duplicado)
        valid_receipt_file.seek(0)  # Reset file pointer
        second_upload = client.post('/upload_receipt', data={
            'payment_id': payment_data['payment_id'],
            'serial_number': payment_data['serial_number'],
            'user_id': payment_data['user_id'],
            'file': (valid_receipt_file, 'comprovante_2.png')
        })
        
        # Verificar tratamento de duplicata
        if second_upload.status_code == 409:  # Conflict
            # Sistema rejeitou duplicata
            error_data = second_upload.get_json()
            assert 'duplicate' in error_data['error'].lower() or 'exists' in error_data['error'].lower()
        elif second_upload.status_code in [200, 201]:  # Accepted
            # Sistema substituiu o anterior
            second_data = second_upload.get_json()
            second_receipt_id = second_data['receipt_id']
            
            # Verificar que apenas um comprovante está ativo
            payment_response = client.get(f'/payment/{payment_data["payment_id"]}')
            payment_info = payment_response.get_json()
            
            active_receipt_id = payment_info['receipt']['id']
            assert active_receipt_id in [first_receipt_id, second_receipt_id], "Deveria haver um comprovante ativo"
        else:
            pytest.fail(f"Status inesperado para upload duplicado: {second_upload.status_code}")
    
    @pytest.mark.integration
    def test_flow_with_processing_timeout(self, client, complete_payment_data, valid_receipt_file):
        """Testa fluxo com timeout no processamento"""
        payment_data = complete_payment_data
        
        # Upload normal
        upload_response = client.post('/upload_receipt', data={
            'payment_id': payment_data['payment_id'],
            'serial_number': payment_data['serial_number'],
            'user_id': payment_data['user_id'],
            'file': (valid_receipt_file, 'comprovante_timeout.png')
        })
        
        assert upload_response.status_code in [200, 201]
        upload_data = upload_response.get_json()
        receipt_id = upload_data['receipt_id']
        
        # Simular processamento que demora
        with patch('time.sleep') as mock_sleep:
            mock_sleep.side_effect = lambda x: time.sleep(min(x, 0.1))  # Acelerar para teste
            
            # Iniciar processamento
            process_response = client.post(f'/receipt/{receipt_id}/process', json={
                'action': 'validate',
                'timeout': 1  # 1 segundo de timeout
            })
            
            # Verificar que processamento foi iniciado
            assert process_response.status_code in [200, 202]
            
            # Aguardar um pouco
            time.sleep(0.5)
            
            # Verificar status
            status_response = client.get(f'/receipt/{receipt_id}/status')
            status_data = status_response.get_json()
            
            # Status deveria indicar processamento ou timeout
            assert status_data['status'] in ['processing', 'timeout', 'failed'], "Status deveria refletir processamento ou timeout"
            
            # Se houve timeout, verificar que foi tratado adequadamente
            if status_data['status'] == 'timeout':
                assert 'timeout' in status_data.get('message', '').lower(), "Mensagem deveria mencionar timeout"
                
                # Verificar que usuário foi notificado
                notifications_response = client.get(f'/user/{payment_data["user_id"]}/notifications')
                if notifications_response.status_code == 200:
                    notifications = notifications_response.get_json()
                    timeout_notifications = [
                        n for n in notifications 
                        if 'timeout' in n.get('content', '').lower()
                    ]
                    assert len(timeout_notifications) > 0, "Usuário deveria ser notificado sobre timeout"


class TestMultiUserScenarios:
    """Testes com múltiplos usuários"""
    
    @pytest.mark.integration
    def test_concurrent_users_different_payments(self, client):
        """Testa usuários concorrentes com pagamentos diferentes"""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Dados para múltiplos usuários
        users_data = [
            {
                'user_id': f'USER_{i:03d}',
                'payment_id': f'PAY_MULTI_{i:03d}',
                'serial_number': f'SN_MULTI_{i:03d}',
                'user_email': f'user{i}@example.com'
            }
            for i in range(1, 6)  # 5 usuários
        ]
        
        # Função para upload de um usuário
        def user_upload(user_data):
            # Criar arquivo único para cada usuário
            file_content = b'\x89PNG\r\n\x1a\n' + f'user_{user_data["user_id"]}'.encode() * 50
            file_data = BytesIO(file_content)
            
            response = client.post('/upload_receipt', data={
                'payment_id': user_data['payment_id'],
                'serial_number': user_data['serial_number'],
                'user_id': user_data['user_id'],
                'file': (file_data, f'comprovante_{user_data["user_id"]}.png')
            })
            
            return {
                'user_id': user_data['user_id'],
                'status_code': response.status_code,
                'success': response.status_code in [200, 201],
                'response': response.get_json() if response.content_type == 'application/json' else None
            }
        
        # Executar uploads concorrentes
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(user_upload, user_data) for user_data in users_data]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # Verificar resultados
        successful_uploads = [r for r in results if r['success']]
        failed_uploads = [r for r in results if not r['success']]
        
        # Todos os uploads deveriam ser bem-sucedidos (pagamentos diferentes)
        assert len(successful_uploads) == len(users_data), "Todos os uploads deveriam ser bem-sucedidos"
        assert len(failed_uploads) == 0, "Não deveria haver falhas"
        
        # Verificar que cada usuário tem seu comprovante
        for user_data in users_data:
            payment_response = client.get(f'/payment/{user_data["payment_id"]}')
            assert payment_response.status_code == 200, f"Pagamento {user_data['payment_id']} deveria existir"
            
            payment_info = payment_response.get_json()
            assert 'receipt' in payment_info, f"Pagamento {user_data['payment_id']} deveria ter comprovante"
    
    @pytest.mark.integration
    def test_user_isolation(self, client):
        """Testa isolamento entre usuários"""
        # Dados de dois usuários
        user1_data = {
            'user_id': 'USER_ISOLATION_1',
            'payment_id': 'PAY_ISOLATION_1',
            'serial_number': 'SN_ISOLATION_1'
        }
        
        user2_data = {
            'user_id': 'USER_ISOLATION_2',
            'payment_id': 'PAY_ISOLATION_2',
            'serial_number': 'SN_ISOLATION_2'
        }
        
        # Upload do usuário 1
        file1 = BytesIO(b'\x89PNG\r\n\x1a\n' + b'user1_content' * 50)
        upload1 = client.post('/upload_receipt', data={
            **user1_data,
            'file': (file1, 'comprovante_user1.png')
        })
        
        assert upload1.status_code in [200, 201]
        user1_receipt_id = upload1.get_json()['receipt_id']
        
        # Upload do usuário 2
        file2 = BytesIO(b'\x89PNG\r\n\x1a\n' + b'user2_content' * 50)
        upload2 = client.post('/upload_receipt', data={
            **user2_data,
            'file': (file2, 'comprovante_user2.png')
        })
        
        assert upload2.status_code in [200, 201]
        user2_receipt_id = upload2.get_json()['receipt_id']
        
        # Verificar isolamento: usuário 1 não pode acessar dados do usuário 2
        user1_trying_user2_payment = client.get(
            f'/payment/{user2_data["payment_id"]}',
            headers={'X-User-ID': user1_data['user_id']}
        )
        
        # Deveria ser negado ou retornar apenas dados públicos
        if user1_trying_user2_payment.status_code == 200:
            # Se permitido, verificar que dados sensíveis não são expostos
            payment_info = user1_trying_user2_payment.get_json()
            assert 'receipt' not in payment_info or payment_info['receipt'] is None, "Dados do comprovante não deveriam ser expostos"
        else:
            assert user1_trying_user2_payment.status_code in [403, 404], "Acesso deveria ser negado"
        
        # Verificar que usuário 1 pode acessar seus próprios dados
        user1_own_payment = client.get(
            f'/payment/{user1_data["payment_id"]}',
            headers={'X-User-ID': user1_data['user_id']}
        )
        
        assert user1_own_payment.status_code == 200, "Usuário deveria acessar seus próprios dados"
        own_payment_info = user1_own_payment.get_json()
        assert 'receipt' in own_payment_info, "Usuário deveria ver seu próprio comprovante"
        assert own_payment_info['receipt']['id'] == user1_receipt_id, "ID do comprovante deveria coincidir"


class TestSystemRecoveryScenarios:
    """Testes de recuperação do sistema"""
    
    @pytest.mark.integration
    def test_recovery_after_service_restart(self, client):
        """Testa recuperação após reinício do serviço"""
        # Simular estado antes do reinício
        pre_restart_data = {
            'payment_id': 'PAY_RESTART_TEST',
            'serial_number': 'SN_RESTART',
            'user_id': 'USER_RESTART',
            'status': 'processing'
        }
        
        # Upload inicial
        file_data = BytesIO(b'\x89PNG\r\n\x1a\n' + b'restart_test' * 50)
        upload_response = client.post('/upload_receipt', data={
            **pre_restart_data,
            'file': (file_data, 'comprovante_restart.png')
        })
        
        assert upload_response.status_code in [200, 201]
        receipt_id = upload_response.get_json()['receipt_id']
        
        # Simular processamento interrompido
        process_response = client.post(f'/receipt/{receipt_id}/process', json={
            'action': 'validate'
        })
        
        # Simular reinício: verificar estado de recuperação
        recovery_response = client.post('/system/recovery', json={
            'action': 'check_pending_operations'
        })
        
        if recovery_response.status_code == 200:
            recovery_data = recovery_response.get_json()
            
            # Verificar que operações pendentes foram identificadas
            assert 'pending_operations' in recovery_data, "Deveria identificar operações pendentes"
            
            pending_receipts = recovery_data.get('pending_receipts', [])
            receipt_ids = [r['receipt_id'] for r in pending_receipts]
            
            if receipt_id in receipt_ids:
                # Comprovante foi identificado como pendente
                assert True, "Sistema identificou comprovante pendente corretamente"
            else:
                # Verificar se foi processado automaticamente
                status_response = client.get(f'/receipt/{receipt_id}/status')
                if status_response.status_code == 200:
                    status_data = status_response.get_json()
                    assert status_data['status'] in ['verified', 'completed'], "Comprovante deveria ter sido processado"
    
    @pytest.mark.integration
    def test_data_migration_compatibility(self, client):
        """Testa compatibilidade com migração de dados"""
        # Simular dados em formato antigo
        legacy_data = {
            'payment_id': 'PAY_LEGACY_001',
            'serial_number': 'SN_LEGACY_001',
            'user_id': 'USER_LEGACY',
            'legacy_format': True,
            'version': '1.0'
        }
        
        # Tentar upload com dados legacy
        file_data = BytesIO(b'\x89PNG\r\n\x1a\n' + b'legacy_test' * 50)
        upload_response = client.post('/upload_receipt', data={
            **legacy_data,
            'file': (file_data, 'comprovante_legacy.png')
        })
        
        # Sistema deveria lidar com formato legacy ou converter
        assert upload_response.status_code in [200, 201, 202], "Sistema deveria aceitar ou converter dados legacy"
        
        if upload_response.status_code == 202:  # Accepted for processing
            # Aguardar conversão
            time.sleep(1)
            
            # Verificar se foi convertido
            payment_response = client.get(f'/payment/{legacy_data["payment_id"]}')
            assert payment_response.status_code == 200, "Pagamento deveria estar acessível após conversão"
            
            payment_info = payment_response.get_json()
            assert 'version' not in payment_info or payment_info['version'] != '1.0', "Dados deveriam ter sido atualizados"
    
    @pytest.mark.integration
    def test_backup_and_restore_flow(self, client, tmp_path):
        """Testa fluxo de backup e restauração"""
        # Criar dados para backup
        test_data = {
            'payment_id': 'PAY_BACKUP_001',
            'serial_number': 'SN_BACKUP_001',
            'user_id': 'USER_BACKUP'
        }
        
        # Upload inicial
        file_data = BytesIO(b'\x89PNG\r\n\x1a\n' + b'backup_test' * 50)
        upload_response = client.post('/upload_receipt', data={
            **test_data,
            'file': (file_data, 'comprovante_backup.png')
        })
        
        assert upload_response.status_code in [200, 201]
        receipt_id = upload_response.get_json()['receipt_id']
        
        # Simular backup
        backup_dir = tmp_path / "backup"
        backup_dir.mkdir()
        
        backup_response = client.post('/system/backup', json={
            'backup_path': str(backup_dir),
            'include_files': True,
            'include_database': True
        })
        
        if backup_response.status_code == 200:
            backup_data = backup_response.get_json()
            assert 'backup_id' in backup_data, "Backup deveria retornar ID"
            
            # Verificar arquivos de backup
            backup_files = list(backup_dir.glob("*"))
            assert len(backup_files) > 0, "Arquivos de backup deveriam ser criados"
            
            # Simular restauração
            restore_response = client.post('/system/restore', json={
                'backup_id': backup_data['backup_id'],
                'restore_path': str(backup_dir)
            })
            
            if restore_response.status_code == 200:
                # Verificar que dados foram restaurados
                restored_payment = client.get(f'/payment/{test_data["payment_id"]}')
                assert restored_payment.status_code == 200, "Pagamento deveria estar disponível após restauração"
                
                restored_info = restored_payment.get_json()
                assert 'receipt' in restored_info, "Comprovante deveria estar restaurado"
                assert restored_info['receipt']['id'] == receipt_id, "ID do comprovante deveria ser preservado"