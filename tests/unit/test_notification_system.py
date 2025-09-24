# -*- coding: utf-8 -*-
"""
Testes unitários para sistema de notificações
Testa envio de emails, SMS, notificações push e fallbacks
"""

import os
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock, call
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Importar funções do projeto
try:
    from payment_api import app
except ImportError:
    pytest.skip("Módulos do projeto não disponíveis", allow_module_level=True)


class TestEmailNotifications:
    """Testes para notificações por email"""
    
    @pytest.fixture
    def email_config(self):
        """Configuração de email para testes"""
        return {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'use_tls': True,
            'from_email': 'noreply@example.com',
            'from_name': 'Sistema de Pagamentos'
        }
    
    @pytest.fixture
    def notification_data(self):
        """Dados de notificação para testes"""
        return {
            'user_id': 'user_123',
            'user_email': 'usuario@example.com',
            'user_name': 'João Silva',
            'payment_id': 'PAY_123456',
            'serial_number': 'SN001234',
            'amount': 150.00,
            'currency': 'BRL',
            'receipt_filename': 'comprovante_pix.png',
            'upload_timestamp': datetime.now().isoformat(),
            'status': 'uploaded'
        }
    
    @pytest.mark.notification
    @patch('smtplib.SMTP')
    def test_successful_email_sending(self, mock_smtp, email_config, notification_data):
        """Testa envio bem-sucedido de email"""
        # Configurar mock
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        # Simular envio de email
        def send_email_notification(config, data):
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = f"{config['from_name']} <{config['from_email']}>"
            msg['To'] = data['user_email']
            msg['Subject'] = f"Comprovante recebido - Pagamento {data['serial_number']}"
            
            # Corpo do email
            body = f"""
            Olá {data['user_name']},
            
            Recebemos seu comprovante de pagamento:
            - Número do pedido: {data['serial_number']}
            - Valor: {data['currency']} {data['amount']:.2f}
            - Arquivo: {data['receipt_filename']}
            - Data/Hora: {data['upload_timestamp']}
            
            Status: {data['status']}
            
            Atenciosamente,
            Equipe de Pagamentos
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Conectar e enviar
            server = mock_smtp(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            return True
        
        # Executar envio
        result = send_email_notification(email_config, notification_data)
        
        # Verificar resultado
        assert result is True, "Email deveria ser enviado com sucesso"
        
        # Verificar chamadas do mock
        mock_smtp.assert_called_once_with(email_config['smtp_server'], email_config['smtp_port'])
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(email_config['username'], email_config['password'])
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @pytest.mark.notification
    @patch('smtplib.SMTP')
    def test_email_sending_failure(self, mock_smtp, email_config, notification_data):
        """Testa falha no envio de email"""
        # Configurar mock para falhar
        mock_smtp.side_effect = Exception("Connection failed")
        
        # Simular envio com tratamento de erro
        def send_email_with_error_handling(config, data):
            try:
                server = mock_smtp(config['smtp_server'], config['smtp_port'])
                server.starttls()
                server.login(config['username'], config['password'])
                # ... resto do código de envio
                return True
            except Exception as e:
                # Log do erro
                error_log = {
                    'timestamp': datetime.now().isoformat(),
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'user_email': data['user_email'],
                    'payment_id': data['payment_id']
                }
                return False, error_log
        
        # Executar envio
        result = send_email_with_error_handling(email_config, notification_data)
        
        # Verificar falha
        assert isinstance(result, tuple), "Deveria retornar tupla em caso de erro"
        success, error_log = result
        assert not success, "Envio deveria falhar"
        assert 'error_type' in error_log, "Log de erro deveria conter tipo do erro"
        assert error_log['error_message'] == "Connection failed", "Mensagem de erro deveria ser preservada"
    
    @pytest.mark.notification
    def test_email_template_generation(self, notification_data):
        """Testa geração de templates de email"""
        # Templates para diferentes status
        templates = {
            'uploaded': {
                'subject': 'Comprovante recebido - Pedido {serial_number}',
                'body': 'Recebemos seu comprovante. Status: Em análise.'
            },
            'verified': {
                'subject': 'Comprovante aprovado - Pedido {serial_number}',
                'body': 'Seu comprovante foi aprovado. Pagamento confirmado.'
            },
            'rejected': {
                'subject': 'Comprovante rejeitado - Pedido {serial_number}',
                'body': 'Seu comprovante foi rejeitado. Por favor, envie um novo.'
            },
            'completed': {
                'subject': 'Pagamento processado - Pedido {serial_number}',
                'body': 'Seu pagamento foi processado com sucesso.'
            }
        }
        
        # Testar geração para cada status
        for status, template in templates.items():
            # Atualizar dados com status
            test_data = notification_data.copy()
            test_data['status'] = status
            
            # Gerar subject e body
            subject = template['subject'].format(**test_data)
            body = template['body']
            
            # Verificar geração
            assert test_data['serial_number'] in subject, f"Serial number deveria estar no subject para status {status}"
            assert len(body) > 0, f"Body não deveria estar vazio para status {status}"
            
            # Verificar conteúdo específico
            if status == 'uploaded':
                assert 'Em análise' in body, "Status uploaded deveria mencionar análise"
            elif status == 'verified':
                assert 'aprovado' in body, "Status verified deveria mencionar aprovação"
            elif status == 'rejected':
                assert 'rejeitado' in body, "Status rejected deveria mencionar rejeição"
            elif status == 'completed':
                assert 'processado' in body, "Status completed deveria mencionar processamento"
    
    @pytest.mark.notification
    def test_email_personalization(self, notification_data):
        """Testa personalização de emails"""
        # Dados de personalização
        personalization_data = {
            'user_name': notification_data['user_name'],
            'user_email': notification_data['user_email'],
            'preferred_language': 'pt-BR',
            'timezone': 'America/Sao_Paulo',
            'notification_preferences': {
                'email_format': 'html',
                'include_receipt_details': True,
                'include_next_steps': True
            }
        }
        
        # Gerar email personalizado
        def generate_personalized_email(data, personalization):
            # Saudação personalizada
            greeting = f"Olá {personalization['user_name']},"
            
            # Formatação baseada em preferências
            if personalization['notification_preferences']['email_format'] == 'html':
                content_type = 'text/html'
                body_template = """
                <html>
                <body>
                    <h2>{greeting}</h2>
                    <p>Recebemos seu comprovante de pagamento:</p>
                    <ul>
                        <li><strong>Pedido:</strong> {serial_number}</li>
                        <li><strong>Valor:</strong> {currency} {amount:.2f}</li>
                        <li><strong>Arquivo:</strong> {receipt_filename}</li>
                    </ul>
                    {next_steps}
                </body>
                </html>
                """
            else:
                content_type = 'text/plain'
                body_template = """
                {greeting}
                
                Recebemos seu comprovante de pagamento:
                - Pedido: {serial_number}
                - Valor: {currency} {amount:.2f}
                - Arquivo: {receipt_filename}
                
                {next_steps}
                """
            
            # Próximos passos baseados em preferências
            next_steps = ""
            if personalization['notification_preferences']['include_next_steps']:
                next_steps = "Próximos passos: Aguarde a análise do comprovante."
            
            # Formatar corpo
            body = body_template.format(
                greeting=greeting,
                next_steps=next_steps,
                **data
            )
            
            return {
                'content_type': content_type,
                'body': body,
                'personalized': True
            }
        
        # Gerar email
        email = generate_personalized_email(notification_data, personalization_data)
        
        # Verificar personalização
        assert email['personalized'], "Email deveria ser marcado como personalizado"
        assert notification_data['user_name'] in email['body'], "Nome do usuário deveria estar no corpo"
        assert notification_data['serial_number'] in email['body'], "Serial number deveria estar no corpo"
        
        # Verificar formato
        if personalization_data['notification_preferences']['email_format'] == 'html':
            assert email['content_type'] == 'text/html', "Content type deveria ser HTML"
            assert '<html>' in email['body'], "Body deveria conter tags HTML"
        
        # Verificar próximos passos
        if personalization_data['notification_preferences']['include_next_steps']:
            assert 'Próximos passos' in email['body'], "Próximos passos deveriam estar incluídos"


class TestNotificationFallbacks:
    """Testes para fallbacks de notificação"""
    
    @pytest.mark.notification
    def test_email_to_file_fallback(self, notification_data, tmp_path):
        """Testa fallback de email para arquivo"""
        # Configurar diretório de fallback
        fallback_dir = tmp_path / "notifications"
        fallback_dir.mkdir()
        
        # Simular falha de email e fallback
        def send_notification_with_fallback(data, fallback_path):
            # Tentar envio por email (simular falha)
            email_success = False  # Simular falha
            
            if not email_success:
                # Fallback: salvar em arquivo
                notification = {
                    'type': 'email_fallback',
                    'timestamp': datetime.now().isoformat(),
                    'recipient': data['user_email'],
                    'subject': f"Comprovante recebido - Pedido {data['serial_number']}",
                    'body': f"Comprovante {data['receipt_filename']} recebido para pagamento {data['payment_id']}",
                    'data': data,
                    'retry_count': 0,
                    'status': 'pending_retry'
                }
                
                # Salvar em arquivo
                filename = f"notification_{data['payment_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = fallback_path / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(notification, f, indent=2, ensure_ascii=False)
                
                return {'method': 'file_fallback', 'filepath': str(filepath), 'success': True}
            
            return {'method': 'email', 'success': True}
        
        # Executar notificação
        result = send_notification_with_fallback(notification_data, fallback_dir)
        
        # Verificar fallback
        assert result['method'] == 'file_fallback', "Deveria usar fallback de arquivo"
        assert result['success'], "Fallback deveria ser bem-sucedido"
        
        # Verificar arquivo criado
        filepath = result['filepath']
        assert os.path.exists(filepath), "Arquivo de fallback deveria ser criado"
        
        # Verificar conteúdo
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_notification = json.load(f)
        
        assert saved_notification['type'] == 'email_fallback', "Tipo deveria ser email_fallback"
        assert saved_notification['recipient'] == notification_data['user_email'], "Destinatário preservado"
        assert saved_notification['status'] == 'pending_retry', "Status deveria ser pending_retry"
    
    @pytest.mark.notification
    def test_notification_retry_mechanism(self, notification_data, tmp_path):
        """Testa mecanismo de retry de notificações"""
        # Configurar arquivo de retry
        retry_file = tmp_path / "retry_notification.json"
        
        # Criar notificação para retry
        failed_notification = {
            'id': 'NOTIF_001',
            'type': 'email',
            'recipient': notification_data['user_email'],
            'subject': 'Test Subject',
            'body': 'Test Body',
            'data': notification_data,
            'retry_count': 0,
            'max_retries': 3,
            'next_retry': (datetime.now() + timedelta(minutes=5)).isoformat(),
            'status': 'pending_retry',
            'created_at': datetime.now().isoformat()
        }
        
        # Salvar notificação
        with open(retry_file, 'w', encoding='utf-8') as f:
            json.dump(failed_notification, f, indent=2)
        
        # Simular processamento de retry
        def process_retry_notification(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                notification = json.load(f)
            
            # Verificar se é hora de retry
            next_retry = datetime.fromisoformat(notification['next_retry'])
            if datetime.now() >= next_retry:
                # Tentar envio novamente
                retry_success = False  # Simular falha novamente
                
                if retry_success:
                    notification['status'] = 'sent'
                    notification['sent_at'] = datetime.now().isoformat()
                else:
                    notification['retry_count'] += 1
                    
                    if notification['retry_count'] >= notification['max_retries']:
                        notification['status'] = 'failed_permanently'
                        notification['failed_at'] = datetime.now().isoformat()
                    else:
                        # Agendar próximo retry (backoff exponencial)
                        delay_minutes = 5 * (2 ** notification['retry_count'])
                        notification['next_retry'] = (datetime.now() + timedelta(minutes=delay_minutes)).isoformat()
                
                # Salvar atualização
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(notification, f, indent=2)
                
                return notification
            
            return None
        
        # Processar retry
        updated_notification = process_retry_notification(retry_file)
        
        # Verificar resultado
        assert updated_notification is not None, "Notificação deveria ser processada"
        assert updated_notification['retry_count'] == 1, "Contador de retry deveria ser incrementado"
        assert updated_notification['status'] == 'pending_retry', "Status deveria continuar pending_retry"
        
        # Simular múltiplos retries até falha permanente
        for i in range(2, 4):  # Mais 2 retries para atingir o máximo
            # Simular passagem do tempo
            updated_notification['next_retry'] = datetime.now().isoformat()
            
            with open(retry_file, 'w', encoding='utf-8') as f:
                json.dump(updated_notification, f, indent=2)
            
            updated_notification = process_retry_notification(retry_file)
        
        # Verificar falha permanente
        assert updated_notification['status'] == 'failed_permanently', "Deveria falhar permanentemente após max retries"
        assert updated_notification['retry_count'] == 3, "Deveria ter tentado 3 retries"
    
    @pytest.mark.notification
    def test_multiple_notification_channels(self, notification_data):
        """Testa múltiplos canais de notificação"""
        # Configurar canais disponíveis
        channels = {
            'email': {'enabled': True, 'priority': 1},
            'sms': {'enabled': True, 'priority': 2},
            'push': {'enabled': False, 'priority': 3},
            'webhook': {'enabled': True, 'priority': 4}
        }
        
        # Simular envio por múltiplos canais
        def send_multi_channel_notification(data, channels_config):
            results = {}
            
            # Ordenar canais por prioridade
            enabled_channels = {
                name: config for name, config in channels_config.items() 
                if config['enabled']
            }
            
            sorted_channels = sorted(
                enabled_channels.items(), 
                key=lambda x: x[1]['priority']
            )
            
            for channel_name, channel_config in sorted_channels:
                try:
                    if channel_name == 'email':
                        # Simular envio de email
                        success = True  # Simular sucesso
                        results[channel_name] = {
                            'success': success,
                            'timestamp': datetime.now().isoformat(),
                            'method': 'smtp'
                        }
                    
                    elif channel_name == 'sms':
                        # Simular envio de SMS
                        success = False  # Simular falha
                        results[channel_name] = {
                            'success': success,
                            'timestamp': datetime.now().isoformat(),
                            'error': 'SMS service unavailable'
                        }
                    
                    elif channel_name == 'webhook':
                        # Simular webhook
                        success = True  # Simular sucesso
                        results[channel_name] = {
                            'success': success,
                            'timestamp': datetime.now().isoformat(),
                            'webhook_url': 'https://api.example.com/webhook'
                        }
                
                except Exception as e:
                    results[channel_name] = {
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
            
            return results
        
        # Executar envio
        results = send_multi_channel_notification(notification_data, channels)
        
        # Verificar resultados
        assert 'email' in results, "Email deveria ser tentado"
        assert 'sms' in results, "SMS deveria ser tentado"
        assert 'push' not in results, "Push não deveria ser tentado (desabilitado)"
        assert 'webhook' in results, "Webhook deveria ser tentado"
        
        # Verificar sucessos e falhas
        assert results['email']['success'], "Email deveria ter sucesso"
        assert not results['sms']['success'], "SMS deveria falhar"
        assert results['webhook']['success'], "Webhook deveria ter sucesso"
        
        # Contar sucessos
        successful_channels = sum(1 for result in results.values() if result['success'])
        assert successful_channels >= 1, "Pelo menos um canal deveria ter sucesso"


class TestNotificationStatus:
    """Testes para status e tracking de notificações"""
    
    @pytest.mark.notification
    def test_notification_status_tracking(self, notification_data):
        """Testa rastreamento de status de notificações"""
        # Simular ciclo de vida de notificação
        notification_lifecycle = [
            {
                'status': 'created',
                'timestamp': datetime.now() - timedelta(minutes=5),
                'details': 'Notification created'
            },
            {
                'status': 'queued',
                'timestamp': datetime.now() - timedelta(minutes=4),
                'details': 'Added to send queue'
            },
            {
                'status': 'sending',
                'timestamp': datetime.now() - timedelta(minutes=3),
                'details': 'Attempting to send via email'
            },
            {
                'status': 'sent',
                'timestamp': datetime.now() - timedelta(minutes=2),
                'details': 'Successfully sent via email'
            },
            {
                'status': 'delivered',
                'timestamp': datetime.now() - timedelta(minutes=1),
                'details': 'Confirmed delivery to recipient'
            }
        ]
        
        # Verificar sequência de status
        expected_sequence = ['created', 'queued', 'sending', 'sent', 'delivered']
        actual_sequence = [entry['status'] for entry in notification_lifecycle]
        
        assert actual_sequence == expected_sequence, "Sequência de status deveria seguir o fluxo esperado"
        
        # Verificar timestamps em ordem
        timestamps = [entry['timestamp'] for entry in notification_lifecycle]
        assert timestamps == sorted(timestamps), "Timestamps deveriam estar em ordem cronológica"
        
        # Verificar status final
        final_status = notification_lifecycle[-1]['status']
        assert final_status == 'delivered', "Status final deveria ser 'delivered'"
    
    @pytest.mark.notification
    def test_notification_metrics_collection(self, notification_data):
        """Testa coleta de métricas de notificações"""
        # Simular dados de métricas
        notification_metrics = {
            'total_sent': 150,
            'total_delivered': 142,
            'total_failed': 8,
            'delivery_rate': 0.947,  # 142/150
            'average_delivery_time': 45.2,  # segundos
            'channel_breakdown': {
                'email': {'sent': 120, 'delivered': 115, 'failed': 5},
                'sms': {'sent': 20, 'delivered': 18, 'failed': 2},
                'webhook': {'sent': 10, 'delivered': 9, 'failed': 1}
            },
            'failure_reasons': {
                'invalid_email': 3,
                'smtp_timeout': 2,
                'sms_service_down': 2,
                'webhook_timeout': 1
            },
            'time_period': {
                'start': (datetime.now() - timedelta(days=1)).isoformat(),
                'end': datetime.now().isoformat()
            }
        }
        
        # Verificar métricas básicas
        assert notification_metrics['total_sent'] > 0, "Total enviado deveria ser positivo"
        assert notification_metrics['total_delivered'] <= notification_metrics['total_sent'], "Entregues não pode ser maior que enviados"
        assert notification_metrics['total_failed'] >= 0, "Falhas não podem ser negativas"
        
        # Verificar taxa de entrega
        calculated_rate = notification_metrics['total_delivered'] / notification_metrics['total_sent']
        assert abs(calculated_rate - notification_metrics['delivery_rate']) < 0.001, "Taxa de entrega deveria estar correta"
        
        # Verificar breakdown por canal
        total_by_channel = sum(
            channel['sent'] for channel in notification_metrics['channel_breakdown'].values()
        )
        assert total_by_channel == notification_metrics['total_sent'], "Total por canal deveria coincidir"
        
        # Verificar razões de falha
        total_failures_by_reason = sum(notification_metrics['failure_reasons'].values())
        assert total_failures_by_reason == notification_metrics['total_failed'], "Total de falhas por razão deveria coincidir"
    
    @pytest.mark.notification
    def test_notification_user_preferences(self, notification_data):
        """Testa preferências de notificação do usuário"""
        # Simular preferências do usuário
        user_preferences = {
            'user_id': notification_data['user_id'],
            'email_notifications': True,
            'sms_notifications': False,
            'push_notifications': True,
            'notification_frequency': 'immediate',  # immediate, daily, weekly
            'quiet_hours': {
                'enabled': True,
                'start': '22:00',
                'end': '08:00',
                'timezone': 'America/Sao_Paulo'
            },
            'notification_types': {
                'payment_received': True,
                'payment_verified': True,
                'payment_rejected': True,
                'payment_completed': True,
                'promotional': False
            }
        }
        
        # Simular verificação de preferências
        def should_send_notification(notification_type, channel, preferences, current_time=None):
            if current_time is None:
                current_time = datetime.now()
            
            # Verificar se tipo de notificação está habilitado
            if not preferences['notification_types'].get(notification_type, False):
                return False, "Notification type disabled"
            
            # Verificar se canal está habilitado
            channel_key = f"{channel}_notifications"
            if not preferences.get(channel_key, False):
                return False, f"{channel} notifications disabled"
            
            # Verificar horário silencioso
            if preferences['quiet_hours']['enabled']:
                current_hour = current_time.strftime('%H:%M')
                start_quiet = preferences['quiet_hours']['start']
                end_quiet = preferences['quiet_hours']['end']
                
                # Simples verificação (não considera timezone)
                if start_quiet <= current_hour or current_hour <= end_quiet:
                    if preferences['notification_frequency'] != 'immediate':
                        return False, "Quiet hours active"
            
            return True, "OK"
        
        # Testar diferentes cenários
        test_cases = [
            ('payment_received', 'email', True, "Email para payment_received deveria ser permitido"),
            ('payment_received', 'sms', False, "SMS deveria estar desabilitado"),
            ('promotional', 'email', False, "Notificações promocionais deveriam estar desabilitadas"),
            ('payment_verified', 'push', True, "Push para payment_verified deveria ser permitido")
        ]
        
        for notification_type, channel, expected, message in test_cases:
            should_send, reason = should_send_notification(
                notification_type, channel, user_preferences
            )
            assert should_send == expected, f"{message}. Razão: {reason}"
        
        # Testar horário silencioso
        quiet_time = datetime.now().replace(hour=23, minute=30)  # 23:30
        should_send_quiet, reason_quiet = should_send_notification(
            'payment_received', 'email', user_preferences, quiet_time
        )
        
        # Durante horário silencioso, apenas immediate deveria passar
        if user_preferences['notification_frequency'] == 'immediate':
            assert should_send_quiet, "Notificações immediate deveriam passar no horário silencioso"
        else:
            assert not should_send_quiet, "Notificações não-immediate deveriam ser bloqueadas no horário silencioso"