# -*- coding: utf-8 -*-
"""
Configuração compartilhada para testes automatizados
Fixtures e configurações globais para testes de comprovantes de pagamento
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.test import Client
from werkzeug.wrappers import Response

# Adicionar o diretório pai ao path para importar o módulo principal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos do projeto
try:
    from payment_api import app, payments_db, save_payments, load_payments
    from payment_api import EmailService, PaymentProcessor
except ImportError as e:
    pytest.skip(f"Não foi possível importar módulos do projeto: {e}", allow_module_level=True)


@pytest.fixture(scope="session")
def test_data_dir():
    """Diretório para dados de teste"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def test_fixtures_dir():
    """Diretório para fixtures de teste"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir():
    """Diretório temporário para testes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_uploads_dir(temp_dir):
    """Mock do diretório de uploads"""
    uploads_dir = temp_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    with patch('payment_api.UPLOAD_FOLDER', str(uploads_dir)):
        yield uploads_dir


@pytest.fixture
def flask_app():
    """Instância da aplicação Flask para testes"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    return app


@pytest.fixture
def client(flask_app):
    """Cliente de teste Flask"""
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


@pytest.fixture
def clean_payments_db():
    """Limpa o banco de dados de pagamentos antes e depois dos testes"""
    # Backup do estado atual
    original_payments = payments_db.copy()
    
    # Limpar para o teste
    payments_db.clear()
    
    yield
    
    # Restaurar estado original
    payments_db.clear()
    payments_db.update(original_payments)


@pytest.fixture
def sample_payment():
    """Pagamento de exemplo para testes"""
    return {
        'payment_id': 'pix_20250101_120000_test',
        'email': 'test@example.com',
        'name': 'Cliente Teste',
        'method': 'pix',
        'amount': 2650,  # R$ 26,50 em centavos
        'currency': 'BRL',
        'status': 'pending_proof',
        'created_at': datetime.now().isoformat(),
        'country': 'BR'
    }


@pytest.fixture
def sample_payment_in_db(clean_payments_db, sample_payment):
    """Adiciona um pagamento de exemplo no banco de dados"""
    payments_db[sample_payment['payment_id']] = sample_payment
    save_payments()
    return sample_payment


@pytest.fixture
def create_test_image():
    """Factory para criar imagens de teste"""
    def _create_image(width=800, height=600, format='PNG', color='RGB'):
        """Cria uma imagem de teste"""
        image = Image.new(color, (width, height), color=(255, 255, 255))
        return image
    
    return _create_image


@pytest.fixture
def create_test_file():
    """Factory para criar arquivos de teste"""
    def _create_file(filename, content=b'test content', content_type='image/png'):
        """Cria um FileStorage de teste"""
        from io import BytesIO
        
        file_obj = BytesIO(content)
        file_obj.seek(0)
        
        return FileStorage(
            stream=file_obj,
            filename=filename,
            content_type=content_type
        )
    
    return _create_file


@pytest.fixture
def valid_image_file(create_test_image, create_test_file):
    """Arquivo de imagem válido para testes"""
    from io import BytesIO
    
    # Criar imagem
    image = create_test_image()
    
    # Converter para bytes
    img_bytes = BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return create_test_file(
        filename='comprovante_test.png',
        content=img_bytes.getvalue(),
        content_type='image/png'
    )


@pytest.fixture
def large_image_file(create_test_image, create_test_file):
    """Arquivo de imagem muito grande para testes"""
    from io import BytesIO
    
    # Criar imagem grande (simular arquivo > 16MB)
    image = create_test_image(width=5000, height=5000)
    
    img_bytes = BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return create_test_file(
        filename='comprovante_large.png',
        content=img_bytes.getvalue(),
        content_type='image/png'
    )


@pytest.fixture
def invalid_file(create_test_file):
    """Arquivo inválido para testes"""
    return create_test_file(
        filename='documento.txt',
        content=b'Este eh um arquivo de texto invalido',
        content_type='text/plain'
    )


@pytest.fixture
def mock_email_service():
    """Mock do serviço de email"""
    with patch.object(EmailService, 'send_proof_pending_notification') as mock_notification, \
         patch.object(EmailService, 'send_serial_email') as mock_serial, \
         patch.object(EmailService, 'send_admin_notification') as mock_admin:
        
        # Configurar retornos padrão
        mock_notification.return_value = True
        mock_serial.return_value = True
        mock_admin.return_value = True
        
        yield {
            'notification': mock_notification,
            'serial': mock_serial,
            'admin': mock_admin
        }


@pytest.fixture
def mock_serial_generator():
    """Mock do gerador de serial"""
    with patch.object(PaymentProcessor, 'generate_serial') as mock_gen:
        mock_gen.return_value = 'TEST-SERIAL-1234-5678'
        yield mock_gen


@pytest.fixture
def upload_request_data(sample_payment, valid_image_file):
    """Dados de requisição para upload de comprovante"""
    return {
        'payment_id': sample_payment['payment_id'],
        'email': sample_payment['email'],
        'name': sample_payment['name'],
        'file': valid_image_file
    }


@pytest.fixture
def mock_datetime():
    """Mock para controlar datetime nos testes"""
    from freezegun import freeze_time
    
    with freeze_time("2025-01-01 12:00:00"):
        yield


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Configuração automática do ambiente de teste"""
    # Configurar variáveis de ambiente para teste
    monkeypatch.setenv('TESTING', 'True')
    monkeypatch.setenv('EMAIL_CONFIGURED', 'False')  # Desabilitar emails reais
    monkeypatch.setenv('SMTP_PASSWORD', 'test_password')
    
    # Configurar paths de teste
    test_dir = Path(__file__).parent
    monkeypatch.setenv('UPLOAD_FOLDER', str(test_dir / 'data' / 'uploads'))
    
    yield


# Utilitários para testes
class TestHelpers:
    """Classe com métodos auxiliares para testes"""
    
    @staticmethod
    def assert_payment_status(payment_id: str, expected_status: str):
        """Verifica se o status do pagamento está correto"""
        assert payment_id in payments_db
        assert payments_db[payment_id]['status'] == expected_status
    
    @staticmethod
    def assert_file_uploaded(payment_id: str, uploads_dir: Path):
        """Verifica se o arquivo foi carregado corretamente"""
        payment = payments_db.get(payment_id)
        assert payment is not None
        assert 'proof_filename' in payment
        
        file_path = uploads_dir / payment['proof_filename']
        assert file_path.exists()
        assert file_path.stat().st_size > 0
    
    @staticmethod
    def create_mock_response(status_code: int = 200, json_data: Dict[str, Any] = None):
        """Cria uma resposta mock para testes"""
        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        return response


@pytest.fixture
def test_helpers():
    """Instância dos helpers de teste"""
    return TestHelpers()


# Configuração de logging para testes
import logging
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)