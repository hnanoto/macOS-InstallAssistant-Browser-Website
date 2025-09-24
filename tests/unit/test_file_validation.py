# -*- coding: utf-8 -*-
"""
Testes unitários para validação de arquivos de comprovante
Testa validações de formato, tamanho, tipo MIME e integridade
"""

import os
import pytest
from io import BytesIO
from PIL import Image
from unittest.mock import patch, Mock

# Importar funções do projeto
try:
    from payment_api import app, allowed_file
except ImportError:
    pytest.skip("Módulos do projeto não disponíveis", allow_module_level=True)


class TestFileFormatValidation:
    """Testes para validação de formato de arquivo"""
    
    @pytest.mark.validation
    def test_supported_image_formats(self):
        """Testa formatos de imagem suportados"""
        supported_formats = {
            'comprovante.png': True,
            'comprovante.jpg': True,
            'comprovante.jpeg': True,
            'comprovante.gif': True,
            'comprovante.PNG': True,
            'comprovante.JPG': True,
            'comprovante.JPEG': True,
            'comprovante.GIF': True
        }
        
        for filename, expected in supported_formats.items():
            result = allowed_file(filename)
            assert result == expected, f"Formato {filename} deveria ser {'aceito' if expected else 'rejeitado'}"
    
    @pytest.mark.validation
    def test_supported_document_formats(self):
        """Testa formatos de documento suportados"""
        document_formats = {
            'comprovante.pdf': True,
            'comprovante.PDF': True,
        }
        
        for filename, expected in document_formats.items():
            result = allowed_file(filename)
            assert result == expected, f"Formato {filename} deveria ser {'aceito' if expected else 'rejeitado'}"
    
    @pytest.mark.validation
    def test_unsupported_formats(self):
        """Testa formatos não suportados"""
        unsupported_formats = [
            'comprovante.bmp',
            'comprovante.tiff',
            'comprovante.webp',
            'comprovante.svg',
            'comprovante.ico',
            'documento.doc',
            'documento.docx',
            'planilha.xls',
            'planilha.xlsx',
            'apresentacao.ppt',
            'apresentacao.pptx',
            'arquivo.txt',
            'codigo.py',
            'script.js',
            'estilo.css',
            'dados.json',
            'config.xml',
            'arquivo.zip',
            'arquivo.rar',
            'arquivo.7z',
            'video.mp4',
            'video.avi',
            'audio.mp3',
            'audio.wav'
        ]
        
        for filename in unsupported_formats:
            result = allowed_file(filename)
            assert not result, f"Formato {filename} deveria ser rejeitado"
    
    @pytest.mark.validation
    def test_case_insensitive_validation(self):
        """Testa validação case-insensitive"""
        test_cases = [
            ('comprovante.png', 'comprovante.PNG'),
            ('comprovante.jpg', 'comprovante.JPG'),
            ('comprovante.jpeg', 'comprovante.JPEG'),
            ('comprovante.gif', 'comprovante.GIF'),
            ('comprovante.pdf', 'comprovante.PDF')
        ]
        
        for lowercase, uppercase in test_cases:
            result_lower = allowed_file(lowercase)
            result_upper = allowed_file(uppercase)
            
            assert result_lower == result_upper, f"Validação deveria ser case-insensitive para {lowercase}/{uppercase}"
            assert result_lower, f"Ambos {lowercase} e {uppercase} deveriam ser válidos"


class TestFileSizeValidation:
    """Testes para validação de tamanho de arquivo"""
    
    @pytest.mark.validation
    def test_max_file_size_configuration(self, flask_app):
        """Testa configuração de tamanho máximo"""
        with flask_app.app_context():
            max_size = flask_app.config.get('MAX_CONTENT_LENGTH')
            expected_max_size = 16 * 1024 * 1024  # 16MB
            
            assert max_size == expected_max_size, f"Tamanho máximo deveria ser {expected_max_size}, mas é {max_size}"
    
    @pytest.mark.validation
    def test_file_size_categories(self, create_test_image, create_test_file):
        """Testa diferentes categorias de tamanho de arquivo"""
        size_tests = [
            # (width, height, expected_category, description)
            (100, 100, 'small', 'Arquivo pequeno'),
            (800, 600, 'medium', 'Arquivo médio'),
            (1920, 1080, 'large', 'Arquivo grande'),
            (50, 50, 'tiny', 'Arquivo muito pequeno')
        ]
        
        for width, height, category, description in size_tests:
            # Criar imagem
            image = create_test_image(width=width, height=height, format='PNG')
            
            # Converter para bytes
            img_bytes = BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Criar FileStorage
            file_storage = create_test_file(
                filename=f'test_{category}.png',
                content=img_bytes.getvalue(),
                content_type='image/png'
            )
            
            # Verificar tamanho
            file_size = len(file_storage.read())
            file_storage.seek(0)
            
            # Definir limites esperados
            if category == 'tiny':
                assert file_size < 10 * 1024, f"{description}: {file_size} bytes deveria ser < 10KB"
            elif category == 'small':
                assert file_size < 100 * 1024, f"{description}: {file_size} bytes deveria ser < 100KB"
            elif category == 'medium':
                assert 100 * 1024 <= file_size < 2 * 1024 * 1024, f"{description}: {file_size} bytes deveria estar entre 100KB e 2MB"
            elif category == 'large':
                assert file_size >= 2 * 1024 * 1024, f"{description}: {file_size} bytes deveria ser >= 2MB"
    
    @pytest.mark.validation
    def test_empty_file_validation(self, create_test_file):
        """Testa validação de arquivo vazio"""
        empty_file = create_test_file(
            filename='empty.png',
            content=b'',
            content_type='image/png'
        )
        
        file_size = len(empty_file.read())
        assert file_size == 0, "Arquivo deveria estar vazio"
        empty_file.seek(0)
    
    @pytest.mark.validation
    def test_minimum_viable_file_size(self, create_test_file):
        """Testa tamanho mínimo viável de arquivo"""
        # Header PNG mínimo
        minimal_png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        
        minimal_file = create_test_file(
            filename='minimal.png',
            content=minimal_png_header,
            content_type='image/png'
        )
        
        file_size = len(minimal_file.read())
        assert file_size > 0, "Arquivo mínimo deveria ter conteúdo"
        assert file_size < 1024, "Arquivo mínimo deveria ser pequeno"
        minimal_file.seek(0)


class TestMimeTypeValidation:
    """Testes para validação de tipo MIME"""
    
    @pytest.mark.validation
    def test_valid_mime_types(self, create_test_file):
        """Testa tipos MIME válidos"""
        valid_mime_types = [
            ('comprovante.png', 'image/png'),
            ('comprovante.jpg', 'image/jpeg'),
            ('comprovante.jpeg', 'image/jpeg'),
            ('comprovante.gif', 'image/gif'),
            ('comprovante.pdf', 'application/pdf')
        ]
        
        for filename, mime_type in valid_mime_types:
            file_storage = create_test_file(
                filename=filename,
                content=b'test content',
                content_type=mime_type
            )
            
            assert file_storage.content_type == mime_type, f"MIME type deveria ser {mime_type}"
            assert allowed_file(filename), f"Arquivo {filename} com MIME {mime_type} deveria ser válido"
    
    @pytest.mark.validation
    def test_mime_type_mismatch(self, create_test_file):
        """Testa incompatibilidade entre extensão e MIME type"""
        mismatched_cases = [
            ('comprovante.png', 'text/plain'),
            ('comprovante.jpg', 'application/json'),
            ('comprovante.pdf', 'image/png'),
            ('documento.txt', 'image/png')
        ]
        
        for filename, wrong_mime_type in mismatched_cases:
            file_storage = create_test_file(
                filename=filename,
                content=b'test content',
                content_type=wrong_mime_type
            )
            
            # O arquivo pode ter MIME type incorreto, mas a validação é baseada na extensão
            extension_valid = allowed_file(filename)
            
            if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
                assert extension_valid, f"Extensão de {filename} deveria ser válida independente do MIME type"
            else:
                assert not extension_valid, f"Extensão de {filename} deveria ser inválida"
    
    @pytest.mark.validation
    def test_missing_mime_type(self, create_test_file):
        """Testa arquivo sem tipo MIME"""
        file_storage = create_test_file(
            filename='comprovante.png',
            content=b'test content',
            content_type=None
        )
        
        # Validação deveria funcionar mesmo sem MIME type
        assert allowed_file(file_storage.filename), "Validação deveria funcionar sem MIME type"


class TestFileIntegrityValidation:
    """Testes para validação de integridade de arquivo"""
    
    @pytest.mark.validation
    def test_valid_png_header(self, create_test_image, create_test_file):
        """Testa header PNG válido"""
        # Criar imagem PNG válida
        image = create_test_image(format='PNG')
        
        img_bytes = BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file_storage = create_test_file(
            filename='valid.png',
            content=img_bytes.getvalue(),
            content_type='image/png'
        )
        
        content = file_storage.read()
        
        # Verificar header PNG
        assert content.startswith(b'\x89PNG\r\n\x1a\n'), "Arquivo PNG deveria ter header correto"
        file_storage.seek(0)
    
    @pytest.mark.validation
    def test_valid_jpeg_header(self, create_test_image, create_test_file):
        """Testa header JPEG válido"""
        # Criar imagem JPEG válida
        image = create_test_image(format='JPEG')
        
        img_bytes = BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        file_storage = create_test_file(
            filename='valid.jpg',
            content=img_bytes.getvalue(),
            content_type='image/jpeg'
        )
        
        content = file_storage.read()
        
        # Verificar header JPEG
        assert content.startswith(b'\xff\xd8\xff'), "Arquivo JPEG deveria ter header correto"
        file_storage.seek(0)
    
    @pytest.mark.validation
    def test_corrupted_file_header(self, create_test_file):
        """Testa arquivo com header corrompido"""
        # Criar arquivo com header incorreto
        corrupted_content = b'\x00\x00\x00\x00' + b'dados corrompidos'
        
        file_storage = create_test_file(
            filename='corrupted.png',
            content=corrupted_content,
            content_type='image/png'
        )
        
        content = file_storage.read()
        
        # Verificar que NÃO tem header PNG válido
        assert not content.startswith(b'\x89PNG'), "Arquivo corrompido não deveria ter header PNG válido"
        file_storage.seek(0)
    
    @pytest.mark.validation
    def test_fake_extension_file(self, create_test_file):
        """Testa arquivo com extensão falsa"""
        # Arquivo de texto com extensão de imagem
        text_content = b'Este eh um arquivo de texto fingindo ser uma imagem PNG'
        
        fake_file = create_test_file(
            filename='fake_image.png',
            content=text_content,
            content_type='image/png'
        )
        
        content = fake_file.read()
        
        # Verificar que não tem header de imagem
        assert not content.startswith(b'\x89PNG'), "Arquivo falso não deveria ter header PNG"
        assert not content.startswith(b'\xff\xd8\xff'), "Arquivo falso não deveria ter header JPEG"
        
        # Mas a extensão ainda seria considerada válida pela função allowed_file
        assert allowed_file(fake_file.filename), "Função allowed_file valida apenas extensão"
        
        fake_file.seek(0)


class TestFileValidationEdgeCases:
    """Testes para casos extremos de validação"""
    
    @pytest.mark.validation
    @pytest.mark.edge_case
    def test_filename_with_multiple_dots(self):
        """Testa nomes de arquivo com múltiplos pontos"""
        test_cases = [
            ('arquivo.backup.png', True),
            ('arquivo.v1.2.jpg', True),
            ('arquivo.final.final.jpeg', True),
            ('arquivo.txt.png', True),  # Última extensão é válida
            ('arquivo.png.txt', False),  # Última extensão é inválida
            ('arquivo.png.backup', False),  # Última extensão é inválida
        ]
        
        for filename, expected in test_cases:
            result = allowed_file(filename)
            assert result == expected, f"Arquivo {filename} deveria retornar {expected}"
    
    @pytest.mark.validation
    @pytest.mark.edge_case
    def test_very_long_filename(self):
        """Testa nomes de arquivo muito longos"""
        # Nome muito longo
        long_name = 'a' * 200 + '.png'
        
        result = allowed_file(long_name)
        assert result, "Nome longo com extensão válida deveria ser aceito"
    
    @pytest.mark.validation
    @pytest.mark.edge_case
    def test_filename_with_special_characters(self):
        """Testa nomes com caracteres especiais"""
        special_cases = [
            ('comprovante-pix.png', True),
            ('comprovante_pix.png', True),
            ('comprovante pix.png', True),
            ('comprovante@pix.png', True),
            ('comprovante#pix.png', True),
            ('comprovante$pix.png', True),
            ('comprovante%pix.png', True),
            ('comprovante&pix.png', True),
            ('comprovante(pix).png', True),
            ('comprovante[pix].png', True),
            ('comprovante{pix}.png', True),
        ]
        
        for filename, expected in special_cases:
            result = allowed_file(filename)
            assert result == expected, f"Arquivo {filename} deveria retornar {expected}"
    
    @pytest.mark.validation
    @pytest.mark.edge_case
    def test_unicode_filename(self):
        """Testa nomes de arquivo com caracteres Unicode"""
        unicode_cases = [
            ('comprovante_píx.png', True),
            ('comprovante_ção.jpg', True),
            ('comprovante_测试.png', True),
            ('comprovante_тест.jpg', True),
            ('comprovante_🏦.png', True),  # Emoji
        ]
        
        for filename, expected in unicode_cases:
            result = allowed_file(filename)
            assert result == expected, f"Arquivo Unicode {filename} deveria retornar {expected}"
    
    @pytest.mark.validation
    @pytest.mark.edge_case
    def test_boundary_conditions(self):
        """Testa condições de fronteira"""
        boundary_cases = [
            ('', False),  # String vazia
            ('.', False),  # Só ponto
            ('.png', True),  # Só extensão
            ('a.png', True),  # Nome mínimo
            ('arquivo.', False),  # Sem extensão após ponto
        ]
        
        for filename, expected in boundary_cases:
            if filename == '':
                # String vazia pode causar erro
                try:
                    result = allowed_file(filename)
                    assert result == expected, f"Arquivo '{filename}' deveria retornar {expected}"
                except (AttributeError, IndexError):
                    # Comportamento esperado para string vazia
                    assert not expected, "String vazia deveria causar erro ou retornar False"
            else:
                result = allowed_file(filename)
                assert result == expected, f"Arquivo '{filename}' deveria retornar {expected}"