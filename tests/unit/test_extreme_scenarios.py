# -*- coding: utf-8 -*-
"""
Testes para cenários extremos e casos de falha
Testa limites do sistema, condições adversas e recuperação de erros
"""

import os
import json
import pytest
import tempfile
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

# Importar funções do projeto
try:
    from payment_api import app
except ImportError:
    pytest.skip("Módulos do projeto não disponíveis", allow_module_level=True)


class TestExtremeFileScenarios:
    """Testes para cenários extremos com arquivos"""
    
    @pytest.mark.extreme
    def test_maximum_file_size_handling(self, client):
        """Testa manipulação de arquivos no limite máximo de tamanho"""
        # Configurar limite máximo (ex: 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        
        # Criar arquivo no limite exato
        def create_file_at_limit(size_bytes):
            content = b'\x89PNG\r\n\x1a\n'  # Header PNG
            content += b'\x00' * (size_bytes - len(content))  # Preencher com zeros
            return BytesIO(content)
        
        # Testar arquivo no limite exato
        file_at_limit = create_file_at_limit(max_size)
        
        response = client.post('/upload_receipt', data={
            'payment_id': 'PAY_LIMIT_TEST',
            'serial_number': 'SN_LIMIT',
            'file': (file_at_limit, 'comprovante_limite.png')
        })
        
        # Arquivo no limite deveria ser aceito
        assert response.status_code in [200, 201], "Arquivo no limite deveria ser aceito"
        
        # Testar arquivo 1 byte acima do limite
        file_over_limit = create_file_at_limit(max_size + 1)
        
        response_over = client.post('/upload_receipt', data={
            'payment_id': 'PAY_OVER_TEST',
            'serial_number': 'SN_OVER',
            'file': (file_over_limit, 'comprovante_over.png')
        })
        
        # Arquivo acima do limite deveria ser rejeitado
        assert response_over.status_code == 413, "Arquivo acima do limite deveria ser rejeitado"
    
    @pytest.mark.extreme
    def test_corrupted_file_handling(self, client):
        """Testa manipulação de arquivos corrompidos"""
        # Cenários de corrupção
        corruption_scenarios = [
            {
                'name': 'header_corrupted',
                'content': b'\x00\x00\x00\x00' + b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000,
                'description': 'Header PNG corrompido'
            },
            {
                'name': 'truncated_file',
                'content': b'\x89PNG\r\n\x1a\n\x00\x00\x00\r',  # Arquivo truncado
                'description': 'Arquivo truncado'
            },
            {
                'name': 'invalid_chunks',
                'content': b'\x89PNG\r\n\x1a\n' + b'\xFF' * 100,  # Chunks inválidos
                'description': 'Chunks PNG inválidos'
            },
            {
                'name': 'mixed_format',
                'content': b'\x89PNG\r\n\x1a\n' + b'\xFF\xD8\xFF\xE0',  # PNG + JPEG headers
                'description': 'Mistura de formatos'
            }
        ]
        
        for scenario in corruption_scenarios:
            file_data = BytesIO(scenario['content'])
            
            response = client.post('/upload_receipt', data={
                'payment_id': f"PAY_CORRUPT_{scenario['name'].upper()}",
                'serial_number': f"SN_CORRUPT_{scenario['name'].upper()}",
                'file': (file_data, f"corrupted_{scenario['name']}.png")
            })
            
            # Arquivos corrompidos deveriam ser rejeitados
            assert response.status_code in [400, 422], f"Arquivo corrompido ({scenario['description']}) deveria ser rejeitado"
            
            # Verificar mensagem de erro
            if response.content_type == 'application/json':
                data = response.get_json()
                assert 'error' in data, f"Resposta deveria conter erro para {scenario['description']}"
    
    @pytest.mark.extreme
    def test_simultaneous_uploads_same_payment(self, client):
        """Testa uploads simultâneos para o mesmo pagamento"""
        payment_id = 'PAY_CONCURRENT_TEST'
        serial_number = 'SN_CONCURRENT'
        
        # Criar múltiplos arquivos
        def create_test_file(index):
            content = b'\x89PNG\r\n\x1a\n' + f'file_{index}'.encode() * 100
            return BytesIO(content)
        
        # Função para upload
        def upload_file(index):
            file_data = create_test_file(index)
            response = client.post('/upload_receipt', data={
                'payment_id': payment_id,
                'serial_number': serial_number,
                'file': (file_data, f'comprovante_{index}.png')
            })
            return {
                'index': index,
                'status_code': response.status_code,
                'response': response.get_json() if response.content_type == 'application/json' else None
            }
        
        # Executar uploads simultâneos
        num_threads = 5
        results = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(upload_file, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # Analisar resultados
        successful_uploads = [r for r in results if r['status_code'] in [200, 201]]
        failed_uploads = [r for r in results if r['status_code'] not in [200, 201]]
        
        # Apenas um upload deveria ser bem-sucedido (ou todos falharem por conflito)
        assert len(successful_uploads) <= 1, "Apenas um upload simultâneo deveria ser bem-sucedido"
        
        # Se houver falhas, deveriam ser por conflito
        for failed in failed_uploads:
            assert failed['status_code'] in [409, 422], "Falhas deveriam ser por conflito ou validação"
    
    @pytest.mark.extreme
    def test_storage_space_exhaustion(self, client, tmp_path):
        """Testa comportamento quando espaço de armazenamento se esgota"""
        # Simular diretório com pouco espaço
        limited_storage_dir = tmp_path / "limited_storage"
        limited_storage_dir.mkdir()
        
        # Mock para simular erro de espaço em disco
        original_open = open
        
        def mock_open_with_disk_full(*args, **kwargs):
            if str(limited_storage_dir) in str(args[0]):
                raise OSError(28, "No space left on device")
            return original_open(*args, **kwargs)
        
        with patch('builtins.open', side_effect=mock_open_with_disk_full):
            # Tentar upload
            file_data = BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)
            
            response = client.post('/upload_receipt', data={
                'payment_id': 'PAY_DISK_FULL',
                'serial_number': 'SN_DISK_FULL',
                'file': (file_data, 'comprovante_disk_full.png')
            })
            
            # Deveria retornar erro de servidor
            assert response.status_code == 507, "Deveria retornar erro de espaço insuficiente"
            
            # Verificar mensagem de erro
            if response.content_type == 'application/json':
                data = response.get_json()
                assert 'storage' in data.get('error', '').lower(), "Erro deveria mencionar problema de armazenamento"


class TestConcurrencyAndPerformance:
    """Testes de concorrência e performance"""
    
    @pytest.mark.extreme
    @pytest.mark.slow
    def test_high_volume_concurrent_uploads(self, client):
        """Testa alto volume de uploads concorrentes"""
        num_uploads = 50
        max_workers = 10
        
        # Função para upload individual
        def perform_upload(upload_id):
            start_time = time.time()
            
            file_data = BytesIO(b'\x89PNG\r\n\x1a\n' + f'upload_{upload_id}'.encode() * 100)
            
            response = client.post('/upload_receipt', data={
                'payment_id': f'PAY_VOLUME_{upload_id}',
                'serial_number': f'SN_VOLUME_{upload_id}',
                'file': (file_data, f'comprovante_volume_{upload_id}.png')
            })
            
            end_time = time.time()
            
            return {
                'upload_id': upload_id,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code in [200, 201]
            }
        
        # Executar uploads concorrentes
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(perform_upload, i) for i in range(num_uploads)]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        total_time = time.time() - start_time
        
        # Analisar resultados
        successful_uploads = [r for r in results if r['success']]
        failed_uploads = [r for r in results if not r['success']]
        
        success_rate = len(successful_uploads) / len(results)
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        
        # Verificar métricas de performance
        assert success_rate >= 0.9, f"Taxa de sucesso deveria ser >= 90%, foi {success_rate:.2%}"
        assert avg_response_time <= 5.0, f"Tempo médio de resposta deveria ser <= 5s, foi {avg_response_time:.2f}s"
        assert total_time <= 30.0, f"Tempo total deveria ser <= 30s, foi {total_time:.2f}s"
        
        # Log de performance
        print(f"\nPerformance Results:")
        print(f"Total uploads: {num_uploads}")
        print(f"Successful: {len(successful_uploads)} ({success_rate:.2%})")
        print(f"Failed: {len(failed_uploads)}")
        print(f"Average response time: {avg_response_time:.2f}s")
        print(f"Total time: {total_time:.2f}s")
    
    @pytest.mark.extreme
    def test_memory_usage_large_files(self, client):
        """Testa uso de memória com arquivos grandes"""
        import psutil
        import gc
        
        # Obter uso inicial de memória
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Criar arquivo grande (5MB)
        large_file_size = 5 * 1024 * 1024
        large_file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * (large_file_size - 8)
        
        # Processar múltiplos arquivos grandes
        for i in range(5):
            file_data = BytesIO(large_file_content)
            
            response = client.post('/upload_receipt', data={
                'payment_id': f'PAY_LARGE_{i}',
                'serial_number': f'SN_LARGE_{i}',
                'file': (file_data, f'comprovante_large_{i}.png')
            })
            
            # Forçar garbage collection
            gc.collect()
            
            # Verificar uso de memória
            current_memory = process.memory_info().rss
            memory_increase = current_memory - initial_memory
            
            # Aumento de memória não deveria ser excessivo
            max_allowed_increase = 100 * 1024 * 1024  # 100MB
            assert memory_increase <= max_allowed_increase, f"Aumento de memória muito alto: {memory_increase / 1024 / 1024:.2f}MB"
    
    @pytest.mark.extreme
    def test_database_connection_exhaustion(self, client):
        """Testa esgotamento de conexões de banco de dados"""
        # Simular múltiplas operações simultâneas que usam BD
        def database_intensive_operation(operation_id):
            # Simular operação que mantém conexão por tempo
            time.sleep(0.1)  # Simular processamento
            
            response = client.post('/upload_receipt', data={
                'payment_id': f'PAY_DB_{operation_id}',
                'serial_number': f'SN_DB_{operation_id}',
                'file': (BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000), f'test_{operation_id}.png')
            })
            
            return {
                'operation_id': operation_id,
                'status_code': response.status_code,
                'success': response.status_code in [200, 201]
            }
        
        # Executar muitas operações simultâneas
        num_operations = 20
        max_workers = 15
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(database_intensive_operation, i) for i in range(num_operations)]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # Verificar que o sistema lidou com a carga
        successful_operations = [r for r in results if r['success']]
        
        # Pelo menos 80% das operações deveriam ser bem-sucedidas
        success_rate = len(successful_operations) / len(results)
        assert success_rate >= 0.8, f"Taxa de sucesso deveria ser >= 80%, foi {success_rate:.2%}"


class TestErrorRecoveryScenarios:
    """Testes de recuperação de erros"""
    
    @pytest.mark.extreme
    def test_partial_file_upload_recovery(self, client, tmp_path):
        """Testa recuperação de uploads parciais"""
        # Simular upload interrompido
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        
        # Criar arquivo parcial
        partial_file = upload_dir / "partial_upload_PAY123.tmp"
        partial_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 500
        
        with open(partial_file, 'wb') as f:
            f.write(partial_content)
        
        # Simular detecção e limpeza de arquivos parciais
        def cleanup_partial_uploads(upload_directory, max_age_hours=1):
            cleaned_files = []
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for file_path in upload_directory.glob("*.tmp"):
                file_stat = file_path.stat()
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_time < cutoff_time:
                    file_path.unlink()
                    cleaned_files.append(str(file_path))
            
            return cleaned_files
        
        # Simular arquivo antigo (modificar timestamp)
        old_time = time.time() - (2 * 3600)  # 2 horas atrás
        os.utime(partial_file, (old_time, old_time))
        
        # Executar limpeza
        cleaned = cleanup_partial_uploads(upload_dir)
        
        # Verificar limpeza
        assert len(cleaned) == 1, "Arquivo parcial antigo deveria ser limpo"
        assert not partial_file.exists(), "Arquivo parcial não deveria mais existir"
    
    @pytest.mark.extreme
    def test_database_rollback_on_failure(self, client):
        """Testa rollback de transações em caso de falha"""
        # Mock para simular falha durante processamento
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("Disk write failed")):
            
            file_data = BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)
            
            response = client.post('/upload_receipt', data={
                'payment_id': 'PAY_ROLLBACK_TEST',
                'serial_number': 'SN_ROLLBACK',
                'file': (file_data, 'comprovante_rollback.png')
            })
            
            # Upload deveria falhar
            assert response.status_code >= 400, "Upload deveria falhar devido ao erro de disco"
            
            # Verificar que não há registros órfãos no banco
            # (Isso dependeria da implementação específica do banco)
            # Por enquanto, apenas verificamos que o erro foi tratado adequadamente
            if response.content_type == 'application/json':
                data = response.get_json()
                assert 'error' in data, "Resposta deveria conter informação de erro"
    
    @pytest.mark.extreme
    def test_service_degradation_handling(self, client):
        """Testa comportamento durante degradação de serviços"""
        # Simular diferentes níveis de degradação
        degradation_scenarios = [
            {
                'name': 'slow_database',
                'delay': 2.0,
                'expected_behavior': 'timeout_or_success'
            },
            {
                'name': 'intermittent_storage',
                'failure_rate': 0.5,
                'expected_behavior': 'retry_or_fail'
            },
            {
                'name': 'email_service_down',
                'service': 'email',
                'expected_behavior': 'fallback_notification'
            }
        ]
        
        for scenario in degradation_scenarios:
            if scenario['name'] == 'slow_database':
                # Simular banco lento
                with patch('time.sleep') as mock_sleep:
                    mock_sleep.side_effect = lambda x: time.sleep(min(x, 0.1))  # Acelerar para teste
                    
                    start_time = time.time()
                    
                    file_data = BytesIO(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)
                    response = client.post('/upload_receipt', data={
                        'payment_id': f'PAY_SLOW_{scenario["name"].upper()}',
                        'serial_number': f'SN_SLOW_{scenario["name"].upper()}',
                        'file': (file_data, f'test_{scenario["name"]}.png')
                    })
                    
                    response_time = time.time() - start_time
                    
                    # Sistema deveria ter timeout ou sucesso, mas não travar
                    assert response_time <= 10.0, "Resposta não deveria demorar mais que 10s"
                    assert response.status_code in [200, 201, 408, 500], "Status deveria indicar sucesso ou timeout"
    
    @pytest.mark.extreme
    def test_cascading_failure_prevention(self, client):
        """Testa prevenção de falhas em cascata"""
        # Simular falha em um componente
        failure_count = 0
        max_failures = 3
        
        def failing_service_mock(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= max_failures:
                raise Exception(f"Service failure #{failure_count}")
            
            # Após max_failures, simular recuperação
            return True
        
        # Testar circuit breaker pattern
        circuit_breaker_state = {
            'failures': 0,
            'last_failure': None,
            'state': 'closed'  # closed, open, half_open
        }
        
        def circuit_breaker_call(service_func, *args, **kwargs):
            current_time = datetime.now()
            
            # Verificar estado do circuit breaker
            if circuit_breaker_state['state'] == 'open':
                # Verificar se é hora de tentar novamente
                if (circuit_breaker_state['last_failure'] and 
                    current_time - circuit_breaker_state['last_failure'] > timedelta(seconds=30)):
                    circuit_breaker_state['state'] = 'half_open'
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                result = service_func(*args, **kwargs)
                
                # Sucesso - resetar circuit breaker
                if circuit_breaker_state['state'] == 'half_open':
                    circuit_breaker_state['state'] = 'closed'
                    circuit_breaker_state['failures'] = 0
                
                return result
                
            except Exception as e:
                circuit_breaker_state['failures'] += 1
                circuit_breaker_state['last_failure'] = current_time
                
                # Abrir circuit breaker após muitas falhas
                if circuit_breaker_state['failures'] >= 3:
                    circuit_breaker_state['state'] = 'open'
                
                raise e
        
        # Testar múltiplas chamadas
        results = []
        
        for i in range(10):
            try:
                result = circuit_breaker_call(failing_service_mock)
                results.append({'attempt': i, 'success': True, 'result': result})
            except Exception as e:
                results.append({'attempt': i, 'success': False, 'error': str(e)})
        
        # Verificar que circuit breaker funcionou
        failures = [r for r in results if not r['success']]
        circuit_breaker_activations = [r for r in failures if 'circuit breaker' in r['error']]
        
        assert len(circuit_breaker_activations) > 0, "Circuit breaker deveria ter sido ativado"
        
        # Verificar que sistema eventualmente se recuperou
        later_successes = [r for r in results[5:] if r['success']]
        assert len(later_successes) > 0, "Sistema deveria ter se recuperado eventualmente"


class TestDataIntegrityUnderStress:
    """Testes de integridade de dados sob stress"""
    
    @pytest.mark.extreme
    def test_concurrent_payment_modifications(self, client):
        """Testa modificações concorrentes do mesmo pagamento"""
        payment_id = 'PAY_CONCURRENT_MOD'
        
        # Função para modificar pagamento
        def modify_payment(modification_id, action):
            if action == 'upload':
                file_data = BytesIO(b'\x89PNG\r\n\x1a\n' + f'mod_{modification_id}'.encode() * 100)
                response = client.post('/upload_receipt', data={
                    'payment_id': payment_id,
                    'serial_number': f'SN_MOD_{modification_id}',
                    'file': (file_data, f'mod_{modification_id}.png')
                })
            elif action == 'status_update':
                response = client.put(f'/payment/{payment_id}/status', 
                                    json={'status': f'updated_by_{modification_id}'})
            elif action == 'verification':
                response = client.post(f'/payment/{payment_id}/verify',
                                     json={'verified_by': f'user_{modification_id}'})
            
            return {
                'modification_id': modification_id,
                'action': action,
                'status_code': response.status_code,
                'success': response.status_code in [200, 201, 202]
            }
        
        # Executar modificações concorrentes
        modifications = [
            ('upload', 1), ('status_update', 2), ('verification', 3),
            ('upload', 4), ('status_update', 5)
        ]
        
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(modify_payment, mod_id, action) 
                      for action, mod_id in modifications]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # Verificar que pelo menos algumas operações foram bem-sucedidas
        successful_mods = [r for r in results if r['success']]
        assert len(successful_mods) >= 1, "Pelo menos uma modificação deveria ser bem-sucedida"
        
        # Verificar que conflitos foram tratados adequadamente
        failed_mods = [r for r in results if not r['success']]
        for failed in failed_mods:
            assert failed['status_code'] in [409, 422, 423], "Falhas deveriam ser por conflito ou lock"
    
    @pytest.mark.extreme
    def test_data_consistency_after_interruption(self, client, tmp_path):
        """Testa consistência de dados após interrupção"""
        # Simular interrupção durante processamento
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        
        # Criar estado inconsistente
        inconsistent_files = [
            upload_dir / "orphan_file_1.png",  # Arquivo sem registro no BD
            upload_dir / "partial_file_2.tmp",  # Upload parcial
        ]
        
        for file_path in inconsistent_files:
            with open(file_path, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)
        
        # Simular registros órfãos no banco
        orphan_records = [
            {
                'payment_id': 'PAY_ORPHAN_1',
                'filename': 'missing_file.png',
                'status': 'uploaded'
            },
            {
                'payment_id': 'PAY_ORPHAN_2', 
                'filename': 'another_missing.png',
                'status': 'processing'
            }
        ]
        
        # Função de verificação de consistência
        def check_data_consistency(upload_directory, database_records):
            issues = []
            
            # Verificar arquivos órfãos
            for file_path in upload_directory.glob("*.png"):
                filename = file_path.name
                if not any(record['filename'] == filename for record in database_records):
                    issues.append({
                        'type': 'orphan_file',
                        'file': filename,
                        'action': 'delete_file'
                    })
            
            # Verificar registros órfãos
            for record in database_records:
                file_path = upload_directory / record['filename']
                if not file_path.exists():
                    issues.append({
                        'type': 'orphan_record',
                        'record': record,
                        'action': 'delete_record'
                    })
            
            # Verificar arquivos temporários antigos
            for tmp_file in upload_directory.glob("*.tmp"):
                file_stat = tmp_file.stat()
                if time.time() - file_stat.st_mtime > 3600:  # 1 hora
                    issues.append({
                        'type': 'old_temp_file',
                        'file': tmp_file.name,
                        'action': 'delete_temp_file'
                    })
            
            return issues
        
        # Simular registros do banco
        mock_db_records = [
            {'payment_id': 'PAY_VALID', 'filename': 'valid_file.png', 'status': 'uploaded'}
        ]
        
        # Verificar consistência
        issues = check_data_consistency(upload_dir, mock_db_records + orphan_records)
        
        # Verificar que problemas foram detectados
        assert len(issues) > 0, "Problemas de consistência deveriam ser detectados"
        
        # Verificar tipos de problemas
        issue_types = {issue['type'] for issue in issues}
        expected_types = {'orphan_file', 'orphan_record', 'old_temp_file'}
        assert issue_types.intersection(expected_types), "Tipos esperados de problemas deveriam ser detectados"
        
        # Simular correção dos problemas
        for issue in issues:
            if issue['action'] == 'delete_file':
                file_path = upload_dir / issue['file']
                if file_path.exists():
                    file_path.unlink()
            elif issue['action'] == 'delete_temp_file':
                file_path = upload_dir / issue['file']
                if file_path.exists():
                    file_path.unlink()
        
        # Verificar que limpeza foi efetiva
        remaining_issues = check_data_consistency(upload_dir, mock_db_records)
        file_issues = [i for i in remaining_issues if i['type'] in ['orphan_file', 'old_temp_file']]
        assert len(file_issues) == 0, "Problemas de arquivo deveriam ter sido corrigidos"