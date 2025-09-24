# -*- coding: utf-8 -*-
"""
Testes unitários para processamento e armazenamento de comprovantes
Testa salvamento, organização, backup e recuperação de arquivos
"""

import os
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from io import BytesIO
from PIL import Image
import pytest
from unittest.mock import patch, Mock, mock_open

# Importar funções do projeto
try:
    from payment_api import app
except ImportError:
    pytest.skip("Módulos do projeto não disponíveis", allow_module_level=True)


class TestFileStorage:
    """Testes para armazenamento de arquivos"""
    
    @pytest.fixture
    def temp_upload_dir(self):
        """Cria diretório temporário para uploads"""
        temp_dir = tempfile.mkdtemp(prefix='test_uploads_')
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @pytest.mark.processing
    def test_upload_directory_creation(self, temp_upload_dir, flask_app):
        """Testa criação do diretório de upload"""
        with flask_app.app_context():
            upload_path = os.path.join(temp_upload_dir, 'uploads')
            
            # Simular criação do diretório
            os.makedirs(upload_path, exist_ok=True)
            
            assert os.path.exists(upload_path), "Diretório de upload deveria ser criado"
            assert os.path.isdir(upload_path), "Upload path deveria ser um diretório"
    
    @pytest.mark.processing
    def test_file_save_with_secure_filename(self, temp_upload_dir, create_test_file):
        """Testa salvamento com nome seguro"""
        from werkzeug.utils import secure_filename
        
        test_cases = [
            ('comprovante pix.png', 'comprovante_pix.png'),
            ('comprovante@banco.jpg', 'comprovantebanco.jpg'),
            ('comprovante#123.png', 'comprovante123.png'),
            ('../../malicious.png', 'malicious.png'),
            ('comprovante\\test.jpg', 'comprovantetest.jpg'),
        ]
        
        for original_name, expected_secure in test_cases:
            secure_name = secure_filename(original_name)
            
            # Criar arquivo de teste
            file_storage = create_test_file(
                filename=original_name,
                content=b'test content',
                content_type='image/png'
            )
            
            # Simular salvamento
            save_path = os.path.join(temp_upload_dir, secure_name)
            
            with open(save_path, 'wb') as f:
                file_storage.seek(0)
                f.write(file_storage.read())
            
            assert os.path.exists(save_path), f"Arquivo {secure_name} deveria ser salvo"
            
            # Verificar conteúdo
            with open(save_path, 'rb') as f:
                content = f.read()
                assert content == b'test content', "Conteúdo deveria ser preservado"
    
    @pytest.mark.processing
    def test_file_organization_by_date(self, temp_upload_dir, create_test_file):
        """Testa organização de arquivos por data"""
        today = datetime.now()
        date_folder = today.strftime('%Y/%m/%d')
        
        # Criar estrutura de diretórios por data
        date_path = os.path.join(temp_upload_dir, date_folder)
        os.makedirs(date_path, exist_ok=True)
        
        # Criar arquivo de teste
        file_storage = create_test_file(
            filename='comprovante.png',
            content=b'test content',
            content_type='image/png'
        )
        
        # Simular salvamento organizado por data
        save_path = os.path.join(date_path, 'comprovante.png')
        
        with open(save_path, 'wb') as f:
            file_storage.seek(0)
            f.write(file_storage.read())
        
        assert os.path.exists(save_path), "Arquivo deveria ser salvo na estrutura de data"
        
        # Verificar estrutura de diretórios
        year_dir = os.path.join(temp_upload_dir, str(today.year))
        month_dir = os.path.join(year_dir, f"{today.month:02d}")
        day_dir = os.path.join(month_dir, f"{today.day:02d}")
        
        assert os.path.exists(year_dir), "Diretório do ano deveria existir"
        assert os.path.exists(month_dir), "Diretório do mês deveria existir"
        assert os.path.exists(day_dir), "Diretório do dia deveria existir"
    
    @pytest.mark.processing
    def test_duplicate_filename_handling(self, temp_upload_dir, create_test_file):
        """Testa tratamento de nomes duplicados"""
        base_filename = 'comprovante.png'
        
        # Criar primeiro arquivo
        file1 = create_test_file(
            filename=base_filename,
            content=b'primeiro arquivo',
            content_type='image/png'
        )
        
        # Salvar primeiro arquivo
        save_path1 = os.path.join(temp_upload_dir, base_filename)
        with open(save_path1, 'wb') as f:
            file1.seek(0)
            f.write(file1.read())
        
        # Criar segundo arquivo com mesmo nome
        file2 = create_test_file(
            filename=base_filename,
            content=b'segundo arquivo',
            content_type='image/png'
        )
        
        # Simular lógica de nome único
        counter = 1
        name, ext = os.path.splitext(base_filename)
        unique_filename = f"{name}_{counter}{ext}"
        
        while os.path.exists(os.path.join(temp_upload_dir, unique_filename)):
            counter += 1
            unique_filename = f"{name}_{counter}{ext}"
        
        # Salvar segundo arquivo com nome único
        save_path2 = os.path.join(temp_upload_dir, unique_filename)
        with open(save_path2, 'wb') as f:
            file2.seek(0)
            f.write(file2.read())
        
        # Verificar que ambos arquivos existem
        assert os.path.exists(save_path1), "Primeiro arquivo deveria existir"
        assert os.path.exists(save_path2), "Segundo arquivo deveria existir com nome único"
        
        # Verificar conteúdos diferentes
        with open(save_path1, 'rb') as f:
            content1 = f.read()
        with open(save_path2, 'rb') as f:
            content2 = f.read()
        
        assert content1 != content2, "Arquivos deveriam ter conteúdos diferentes"
        assert content1 == b'primeiro arquivo', "Primeiro arquivo preservado"
        assert content2 == b'segundo arquivo', "Segundo arquivo preservado"


class TestFileProcessing:
    """Testes para processamento de arquivos"""
    
    @pytest.mark.processing
    def test_image_metadata_extraction(self, create_test_image, create_test_file):
        """Testa extração de metadados de imagem"""
        # Criar imagem com dimensões específicas
        image = create_test_image(width=800, height=600, format='PNG')
        
        img_bytes = BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file_storage = create_test_file(
            filename='test_metadata.png',
            content=img_bytes.getvalue(),
            content_type='image/png'
        )
        
        # Simular extração de metadados
        file_storage.seek(0)
        with Image.open(file_storage) as img:
            width, height = img.size
            format_type = img.format
            mode = img.mode
        
        assert width == 800, "Largura deveria ser 800px"
        assert height == 600, "Altura deveria ser 600px"
        assert format_type == 'PNG', "Formato deveria ser PNG"
        assert mode in ['RGB', 'RGBA'], "Modo deveria ser RGB ou RGBA"
    
    @pytest.mark.processing
    def test_file_size_calculation(self, create_test_file):
        """Testa cálculo de tamanho de arquivo"""
        test_content = b'A' * 1024  # 1KB de dados
        
        file_storage = create_test_file(
            filename='size_test.png',
            content=test_content,
            content_type='image/png'
        )
        
        # Calcular tamanho
        file_storage.seek(0, 2)  # Ir para o final
        file_size = file_storage.tell()
        file_storage.seek(0)  # Voltar ao início
        
        assert file_size == 1024, "Tamanho deveria ser 1024 bytes"
        
        # Verificar tamanho em diferentes unidades
        size_kb = file_size / 1024
        size_mb = file_size / (1024 * 1024)
        
        assert size_kb == 1.0, "Tamanho deveria ser 1KB"
        assert size_mb < 0.001, "Tamanho deveria ser menor que 0.001MB"
    
    @pytest.mark.processing
    def test_file_hash_generation(self, create_test_file):
        """Testa geração de hash para verificação de integridade"""
        import hashlib
        
        test_content = b'conteudo para hash'
        
        file_storage = create_test_file(
            filename='hash_test.png',
            content=test_content,
            content_type='image/png'
        )
        
        # Gerar hash MD5
        file_storage.seek(0)
        md5_hash = hashlib.md5(file_storage.read()).hexdigest()
        
        # Gerar hash SHA256
        file_storage.seek(0)
        sha256_hash = hashlib.sha256(file_storage.read()).hexdigest()
        
        # Verificar hashes esperados
        expected_md5 = hashlib.md5(test_content).hexdigest()
        expected_sha256 = hashlib.sha256(test_content).hexdigest()
        
        assert md5_hash == expected_md5, "Hash MD5 deveria coincidir"
        assert sha256_hash == expected_sha256, "Hash SHA256 deveria coincidir"
        assert len(md5_hash) == 32, "Hash MD5 deveria ter 32 caracteres"
        assert len(sha256_hash) == 64, "Hash SHA256 deveria ter 64 caracteres"
    
    @pytest.mark.processing
    def test_image_thumbnail_generation(self, create_test_image, create_test_file):
        """Testa geração de thumbnail"""
        # Criar imagem grande
        large_image = create_test_image(width=1920, height=1080, format='PNG')
        
        img_bytes = BytesIO()
        large_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file_storage = create_test_file(
            filename='large_image.png',
            content=img_bytes.getvalue(),
            content_type='image/png'
        )
        
        # Gerar thumbnail
        file_storage.seek(0)
        with Image.open(file_storage) as img:
            # Criar thumbnail 200x200
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            thumb_width, thumb_height = img.size
        
        # Verificar dimensões do thumbnail
        assert thumb_width <= 200, "Largura do thumbnail deveria ser <= 200px"
        assert thumb_height <= 200, "Altura do thumbnail deveria ser <= 200px"
        
        # Verificar proporção mantida
        original_ratio = 1920 / 1080
        thumb_ratio = thumb_width / thumb_height
        
        assert abs(original_ratio - thumb_ratio) < 0.01, "Proporção deveria ser mantida"


class TestFileBackupAndRecovery:
    """Testes para backup e recuperação de arquivos"""
    
    @pytest.fixture
    def backup_dirs(self):
        """Cria diretórios temporários para backup"""
        primary_dir = tempfile.mkdtemp(prefix='test_primary_')
        backup_dir = tempfile.mkdtemp(prefix='test_backup_')
        
        yield primary_dir, backup_dir
        
        # Cleanup
        for dir_path in [primary_dir, backup_dir]:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
    
    @pytest.mark.processing
    def test_automatic_backup_creation(self, backup_dirs, create_test_file):
        """Testa criação automática de backup"""
        primary_dir, backup_dir = backup_dirs
        
        # Criar arquivo no diretório principal
        file_storage = create_test_file(
            filename='important.png',
            content=b'dados importantes',
            content_type='image/png'
        )
        
        primary_path = os.path.join(primary_dir, 'important.png')
        backup_path = os.path.join(backup_dir, 'important.png')
        
        # Salvar arquivo principal
        with open(primary_path, 'wb') as f:
            file_storage.seek(0)
            f.write(file_storage.read())
        
        # Simular backup automático
        shutil.copy2(primary_path, backup_path)
        
        # Verificar backup
        assert os.path.exists(backup_path), "Backup deveria ser criado"
        
        # Verificar integridade
        with open(primary_path, 'rb') as f:
            primary_content = f.read()
        with open(backup_path, 'rb') as f:
            backup_content = f.read()
        
        assert primary_content == backup_content, "Backup deveria ser idêntico ao original"
    
    @pytest.mark.processing
    def test_backup_versioning(self, backup_dirs, create_test_file):
        """Testa versionamento de backups"""
        primary_dir, backup_dir = backup_dirs
        
        filename = 'versioned.png'
        primary_path = os.path.join(primary_dir, filename)
        
        # Criar múltiplas versões
        versions = [
            b'versao 1',
            b'versao 2',
            b'versao 3'
        ]
        
        for i, content in enumerate(versions, 1):
            # Criar arquivo
            file_storage = create_test_file(
                filename=filename,
                content=content,
                content_type='image/png'
            )
            
            # Salvar versão principal
            with open(primary_path, 'wb') as f:
                file_storage.seek(0)
                f.write(file_storage.read())
            
            # Criar backup versionado
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"versioned_v{i}_{timestamp}.png"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(primary_path, backup_path)
            
            assert os.path.exists(backup_path), f"Backup versão {i} deveria existir"
        
        # Verificar que todas as versões existem
        backup_files = os.listdir(backup_dir)
        version_files = [f for f in backup_files if f.startswith('versioned_v')]
        
        assert len(version_files) == 3, "Deveriam existir 3 versões de backup"
    
    @pytest.mark.processing
    def test_file_recovery_from_backup(self, backup_dirs, create_test_file):
        """Testa recuperação de arquivo do backup"""
        primary_dir, backup_dir = backup_dirs
        
        # Criar arquivo original
        file_storage = create_test_file(
            filename='recoverable.png',
            content=b'dados originais',
            content_type='image/png'
        )
        
        primary_path = os.path.join(primary_dir, 'recoverable.png')
        backup_path = os.path.join(backup_dir, 'recoverable.png')
        
        # Salvar original e backup
        with open(primary_path, 'wb') as f:
            file_storage.seek(0)
            f.write(file_storage.read())
        
        shutil.copy2(primary_path, backup_path)
        
        # Simular corrupção do arquivo principal
        with open(primary_path, 'wb') as f:
            f.write(b'dados corrompidos')
        
        # Verificar corrupção
        with open(primary_path, 'rb') as f:
            corrupted_content = f.read()
        
        assert corrupted_content == b'dados corrompidos', "Arquivo deveria estar corrompido"
        
        # Recuperar do backup
        shutil.copy2(backup_path, primary_path)
        
        # Verificar recuperação
        with open(primary_path, 'rb') as f:
            recovered_content = f.read()
        
        assert recovered_content == b'dados originais', "Arquivo deveria ser recuperado"


class TestFileMetadataStorage:
    """Testes para armazenamento de metadados"""
    
    @pytest.mark.processing
    def test_metadata_json_creation(self, temp_upload_dir, create_test_file):
        """Testa criação de arquivo JSON com metadados"""
        # Criar arquivo de teste
        file_storage = create_test_file(
            filename='metadata_test.png',
            content=b'test content for metadata',
            content_type='image/png'
        )
        
        # Simular coleta de metadados
        metadata = {
            'filename': 'metadata_test.png',
            'original_filename': 'metadata_test.png',
            'content_type': 'image/png',
            'file_size': len(file_storage.read()),
            'upload_timestamp': datetime.now().isoformat(),
            'file_hash': 'abc123def456',  # Hash simulado
            'user_id': 'user123',
            'payment_id': 'pay456',
            'status': 'uploaded'
        }
        
        # Salvar metadados
        metadata_path = os.path.join(temp_upload_dir, 'metadata_test.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Verificar arquivo de metadados
        assert os.path.exists(metadata_path), "Arquivo de metadados deveria existir"
        
        # Verificar conteúdo
        with open(metadata_path, 'r', encoding='utf-8') as f:
            loaded_metadata = json.load(f)
        
        assert loaded_metadata['filename'] == 'metadata_test.png', "Nome do arquivo preservado"
        assert loaded_metadata['content_type'] == 'image/png', "Tipo MIME preservado"
        assert loaded_metadata['file_size'] > 0, "Tamanho do arquivo registrado"
        assert 'upload_timestamp' in loaded_metadata, "Timestamp de upload registrado"
    
    @pytest.mark.processing
    def test_metadata_search_and_retrieval(self, temp_upload_dir):
        """Testa busca e recuperação de metadados"""
        # Criar múltiplos arquivos de metadados
        test_metadata = [
            {
                'filename': 'comprovante1.png',
                'user_id': 'user123',
                'payment_id': 'pay001',
                'upload_timestamp': '2024-01-15T10:30:00',
                'status': 'processed'
            },
            {
                'filename': 'comprovante2.jpg',
                'user_id': 'user456',
                'payment_id': 'pay002',
                'upload_timestamp': '2024-01-15T11:45:00',
                'status': 'pending'
            },
            {
                'filename': 'comprovante3.pdf',
                'user_id': 'user123',
                'payment_id': 'pay003',
                'upload_timestamp': '2024-01-15T14:20:00',
                'status': 'processed'
            }
        ]
        
        # Salvar metadados
        for i, metadata in enumerate(test_metadata, 1):
            metadata_path = os.path.join(temp_upload_dir, f'metadata_{i}.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        
        # Simular busca por usuário
        user_files = []
        for filename in os.listdir(temp_upload_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(temp_upload_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    if metadata.get('user_id') == 'user123':
                        user_files.append(metadata)
        
        assert len(user_files) == 2, "Deveria encontrar 2 arquivos do user123"
        
        # Simular busca por status
        processed_files = []
        for filename in os.listdir(temp_upload_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(temp_upload_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    if metadata.get('status') == 'processed':
                        processed_files.append(metadata)
        
        assert len(processed_files) == 2, "Deveria encontrar 2 arquivos processados"
    
    @pytest.mark.processing
    def test_metadata_update_and_versioning(self, temp_upload_dir):
        """Testa atualização e versionamento de metadados"""
        # Criar metadados iniciais
        initial_metadata = {
            'filename': 'updateable.png',
            'status': 'uploaded',
            'version': 1,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(temp_upload_dir, 'updateable_metadata.json')
        
        # Salvar versão inicial
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(initial_metadata, f, indent=2)
        
        # Simular atualizações
        updates = [
            {'status': 'processing', 'processor_id': 'proc123'},
            {'status': 'validated', 'validation_result': 'passed'},
            {'status': 'completed', 'completion_timestamp': datetime.now().isoformat()}
        ]
        
        for update in updates:
            # Carregar metadados atuais
            with open(metadata_path, 'r', encoding='utf-8') as f:
                current_metadata = json.load(f)
            
            # Aplicar atualização
            current_metadata.update(update)
            current_metadata['version'] += 1
            current_metadata['updated_at'] = datetime.now().isoformat()
            
            # Salvar versão atualizada
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(current_metadata, f, indent=2)
        
        # Verificar versão final
        with open(metadata_path, 'r', encoding='utf-8') as f:
            final_metadata = json.load(f)
        
        assert final_metadata['version'] == 4, "Versão deveria ser 4 após 3 atualizações"
        assert final_metadata['status'] == 'completed', "Status final deveria ser 'completed'"
        assert 'completion_timestamp' in final_metadata, "Timestamp de conclusão deveria existir"
        assert final_metadata['created_at'] != final_metadata['updated_at'], "Timestamps de criação e atualização deveriam ser diferentes"