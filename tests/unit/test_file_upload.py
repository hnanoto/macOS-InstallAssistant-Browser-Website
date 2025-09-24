# -*- coding: utf-8 -*-
"""
Testes unitários para upload de arquivos de comprovante
Testa formatos, tamanhos e validações de arquivos
"""

import os
import pytest
from io import BytesIO
from PIL import Image
from werkzeug.datastructures import FileStorage
from unittest.mock import patch, Mock

# Importar funções do projeto
try:
    from payment_api import allowed_file, save_payment_proof, app, ALLOWED_EXTENSIONS
except ImportError:
    pytest.skip("Módulos do projeto não disponíveis", allow_module_level=True)


class TestFileUpload:
    """Testes para upload de arquivos de comprovante"""
    
    @pytest.mark.upload
    def test_allowed_file_valid_extensions(self):
        """Testa se extensões válidas são aceitas"""
        valid_files = [
            'comprovante.png',
            'comprovante.jpg',
            'comprovante.jpeg',
            'comprovante.gif',
            'comprovante.pdf',
            'COMPROVANTE.PNG',  # Teste case insensitive
            'comprovante_pix.JPG'
        ]
        
        for filename in valid_files:
            result = allowed_file(filename)
            assert result is True, f"Arquivo {filename} deveria ser válido"
    
    @pytest.mark.upload
    def test_allowed_file_invalid_extensions(self):
        """Testa rejeição de extensões inválidas"""
        invalid_files = [
            'document.txt', 'script.py', 'data.csv',
            'image.bmp', 'file.exe', 'archive.zip'
        ]
        
        for filename in invalid_files:
            result = allowed_file(filename)
            assert result is False, f"Arquivo {filename} deveria ser inválido"
    
    @pytest.mark.upload
    def test_allowed_file_edge_cases(self):
        """Testa casos extremos de nomes de arquivo"""
        edge_cases = [
            ('', False),  # String vazia
            (None, False),  # None
            ('arquivo.PNG.txt', False),  # Extensão dupla inválida
            ('arquivo.txt.png', True),  # Extensão dupla válida
            ('arquivo com espaços.png', True),  # Espaços no nome
            ('arquivo-com-hifens.jpg', True),  # Hífens no nome
            ('arquivo_com_underscores.jpeg', True),  # Underscores
            ('arquivo123.gif', True),  # Números no nome
            ('arquivo.PNG', True),  # Maiúscula
        ]
        
        for filename, expected in edge_cases:
            if filename is None:
                with pytest.raises((AttributeError, TypeError)):
                    allowed_file(filename)
            else:
                result = allowed_file(filename)
                assert result == expected, f"Arquivo '{filename}' deveria retornar {expected}"


class TestFileCreation:
    """Testes para criação de arquivos de teste"""
    
    @pytest.mark.upload
    def test_create_valid_png_file(self, create_test_image, create_test_file):
        """Testa criação de arquivo PNG válido"""
        # Criar imagem
        image = create_test_image(width=800, height=600, format='PNG')
        
        # Converter para bytes
        img_bytes = BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Criar FileStorage
        file_storage = create_test_file(
            filename='test.png',
            content=img_bytes.getvalue(),
            content_type='image/png'
        )
        
        assert file_storage.filename == 'test.png'
        assert file_storage.content_type == 'image/png'
        assert len(file_storage.read()) > 0
        file_storage.seek(0)  # Reset para próximos usos
    
    @pytest.mark.upload
    def test_create_valid_jpg_file(self, create_test_image, create_test_file):
        """Testa criação de arquivo JPG válido"""
        # Criar imagem
        image = create_test_image(width=1024, height=768, format='JPEG')
        
        # Converter para bytes
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Criar FileStorage
        file_storage = create_test_file(
            filename='test.jpg',
            content=img_bytes.getvalue(),
            content_type='image/jpeg'
        )
        
        assert file_storage.filename == 'test.jpg'
        assert file_storage.content_type == 'image/jpeg'
        assert len(file_storage.read()) > 0
        file_storage.seek(0)
    
    @pytest.mark.upload
    def test_create_large_file(self, temp_dir):
        """Testa criação de arquivo grande para teste de limite"""
        large_file_path = temp_dir / 'large_file.png'
        
        # Criar arquivo de 2MB
        with open(large_file_path, 'wb') as f:
            f.write(b'\x00' * (2 * 1024 * 1024))
        
        file_size = large_file_path.stat().st_size
        assert file_size > (1024 * 1024), f"Arquivo deveria ter mais de 1MB, mas tem {file_size} bytes"
    
    @pytest.mark.upload
    def test_create_small_file(self, create_test_image, create_test_file):
        """Testa criação de arquivo pequeno"""
        # Criar imagem pequena
        image = create_test_image(width=100, height=100, format='PNG')
        
        img_bytes = BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file_storage = create_test_file(
            filename='small_test.png',
            content=img_bytes.getvalue(),
            content_type='image/png'
        )
        
        # Verificar se o arquivo é pequeno
        file_size = len(file_storage.read())
        assert file_size < 100 * 1024  # Menor que 100KB
        file_storage.seek(0)


class TestFileSizeValidation:
    """Testes para validação de tamanho de arquivo"""
    
    @pytest.mark.upload
    def test_file_size_within_limit(self, create_test_image, create_test_file):
        """Testa arquivo dentro do limite de tamanho"""
        # Criar arquivo de tamanho médio (aproximadamente 1MB)
        image = create_test_image(width=1000, height=1000, format='PNG')
        
        img_bytes = BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file_storage = create_test_file(
            filename='medium_test.png',
            content=img_bytes.getvalue(),
            content_type='image/png'
        )
        
        file_size = len(file_storage.read())
        max_size = 16 * 1024 * 1024  # 16MB
        
        assert file_size < max_size, f"Arquivo de {file_size} bytes deveria estar dentro do limite de {max_size} bytes"
        file_storage.seek(0)
    
    @pytest.mark.upload
    def test_empty_file(self, create_test_file):
        """Testa arquivo vazio"""
        file_storage = create_test_file(
            filename='empty.png',
            content=b'',
            content_type='image/png'
        )
        
        file_size = len(file_storage.read())
        assert file_size == 0
        file_storage.seek(0)
    
    @pytest.mark.upload
    def test_minimum_file_size(self, create_test_file):
        """Testa arquivo com tamanho mínimo"""
        # Criar arquivo com conteúdo mínimo
        minimal_content = b'\x89PNG\r\n\x1a\n'  # Header PNG mínimo
        
        file_storage = create_test_file(
            filename='minimal.png',
            content=minimal_content,
            content_type='image/png'
        )
        
        file_size = len(file_storage.read())
        assert file_size > 0
        assert file_size < 1024  # Menor que 1KB
        file_storage.seek(0)


class TestFileContentValidation:
    """Testes para validação de conteúdo de arquivo"""
    
    @pytest.mark.upload
    def test_valid_image_content(self, valid_image_file):
        """Testa se o conteúdo da imagem é válido"""
        # Verificar se é um FileStorage válido
        assert hasattr(valid_image_file, 'filename')
        assert hasattr(valid_image_file, 'content_type')
        assert hasattr(valid_image_file, 'read')
        
        # Verificar conteúdo
        content = valid_image_file.read()
        assert len(content) > 0
        
        # Verificar se começa com header PNG
        assert content.startswith(b'\x89PNG')
        
        valid_image_file.seek(0)
    
    @pytest.mark.upload
    def test_invalid_image_content(self, create_test_file):
        """Testa arquivo com conteúdo inválido"""
        # Criar arquivo com conteúdo de texto mas extensão de imagem
        file_storage = create_test_file(
            filename='fake_image.png',
            content=b'Este eh um arquivo de texto fingindo ser imagem',
            content_type='image/png'
        )
        
        content = file_storage.read()
        assert len(content) > 0
        
        # Verificar que NÃO começa com header PNG
        assert not content.startswith(b'\x89PNG')
        
        file_storage.seek(0)
    
    @pytest.mark.upload
    def test_corrupted_image_content(self, create_test_file):
        """Testa arquivo com conteúdo corrompido"""
        # Criar arquivo com header PNG mas conteúdo corrompido
        corrupted_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100 + b'dados corrompidos'
        
        file_storage = create_test_file(
            filename='corrupted.png',
            content=corrupted_content,
            content_type='image/png'
        )
        
        content = file_storage.read()
        assert len(content) > 0
        assert content.startswith(b'\x89PNG')  # Header correto
        
        file_storage.seek(0)


class TestFileStorageIntegration:
    """Testes de integração para armazenamento de arquivos"""
    
    @pytest.mark.upload
    @pytest.mark.integration
    def test_save_payment_proof_success(self, mock_uploads_dir, valid_image_file):
        """Testa salvamento bem-sucedido de comprovante"""
        payment_id = 'pix_20250101_120000_test'
        
        # Salvar arquivo
        with patch('payment_api.app.config', {'UPLOAD_FOLDER': str(mock_uploads_dir)}):
            result = save_payment_proof(valid_image_file, payment_id)
        
        # Verificar resultado
        assert result is not None, "save_payment_proof deveria retornar um nome de arquivo"
        assert result.endswith('.png'), "Arquivo salvo deveria ter extensão .png"
        
        # Verificar se arquivo foi salvo
        saved_file_path = mock_uploads_dir / result
        assert saved_file_path.exists(), "Arquivo deveria ter sido salvo no diretório"
        assert saved_file_path.stat().st_size > 0, "Arquivo salvo deveria ter conteúdo"
    
    @pytest.mark.upload
    @pytest.mark.integration
    def test_save_payment_proof_different_formats(self, mock_uploads_dir, create_test_image, create_test_file):
        """Testa salvamento de diferentes formatos de arquivo"""
        payment_id = 'pix_20250101_120000_test'
        formats = [
            ('test.png', 'PNG', 'image/png'),
            ('test.jpg', 'JPEG', 'image/jpeg'),
            ('test.jpeg', 'JPEG', 'image/jpeg'),
            ('test.gif', 'GIF', 'image/gif')
        ]
        
        for filename, img_format, content_type in formats:
            # Criar imagem no formato específico
            image = create_test_image(format=img_format)
            
            img_bytes = BytesIO()
            image.save(img_bytes, format=img_format)
            img_bytes.seek(0)
            
            file_storage = create_test_file(
                filename=filename,
                content=img_bytes.getvalue(),
                content_type=content_type
            )
            
            # Salvar arquivo
            with patch('payment_api.app.config', {'UPLOAD_FOLDER': str(mock_uploads_dir)}):
                result = save_payment_proof(file_storage, f"{payment_id}_{img_format.lower()}")
            
            # Verificar resultado
            assert result is not None
            
            # Verificar se arquivo foi salvo
            saved_file_path = mock_uploads_dir / result
            assert saved_file_path.exists()
            assert saved_file_path.stat().st_size > 0
    
    @pytest.mark.upload
    @pytest.mark.integration
    def test_save_payment_proof_filename_sanitization(self, mock_uploads_dir, valid_image_file):
        """Testa sanitização de nomes de arquivo"""
        payment_ids = [
            'pix_20250101_120000_test',
            'pix_20250101_120000_test_with_special_chars!@#',
            'pix/20250101\\120000\test',
            'pix 20250101 120000 test with spaces'
        ]
        
        for payment_id in payment_ids:
            # Reset file pointer
            valid_image_file.seek(0)
            
            # Salvar arquivo
            with patch('payment_api.app.config', {'UPLOAD_FOLDER': str(mock_uploads_dir)}):
                result = save_payment_proof(valid_image_file, payment_id)
            
            # Verificar que o resultado é um nome de arquivo válido
            assert result is not None
            assert '/' not in result
            assert '\\' not in result
            assert result.endswith('.png')
            
            # Verificar se arquivo foi salvo
            saved_file_path = mock_uploads_dir / result
            assert saved_file_path.exists()
    
    @pytest.mark.upload
    @pytest.mark.integration
    def test_save_payment_proof_duplicate_handling(self, mock_uploads_dir, valid_image_file):
        """Testa tratamento de arquivos duplicados"""
        payment_id = 'pix_20250101_120000_test'
        
        # Salvar primeiro arquivo
        valid_image_file.seek(0)
        with patch('payment_api.app.config', {'UPLOAD_FOLDER': str(mock_uploads_dir)}):
            result1 = save_payment_proof(valid_image_file, payment_id)
        
        # Salvar segundo arquivo com mesmo payment_id
        valid_image_file.seek(0)
        with patch('payment_api.app.config', {'UPLOAD_FOLDER': str(mock_uploads_dir)}):
            result2 = save_payment_proof(valid_image_file, payment_id)
        
        # Verificar que ambos foram salvos (podem ter nomes diferentes)
        assert result1 is not None
        assert result2 is not None
        
        # Verificar se ambos arquivos existem
        file1_path = mock_uploads_dir / result1
        file2_path = mock_uploads_dir / result2
        
        assert file1_path.exists()
        assert file2_path.exists()