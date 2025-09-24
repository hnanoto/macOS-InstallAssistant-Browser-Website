#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configurações SMTP
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
FROM_EMAIL = os.getenv('FROM_EMAIL')

print("🔧 Teste direto do SMTP")
print(f"📧 Servidor: {SMTP_SERVER}")
print(f"🔌 Porta: {SMTP_PORT}")
print(f"👤 Usuário: {SMTP_USERNAME}")
print(f"🔑 Senha: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'NÃO CONFIGURADA'}")
print(f"📨 From: {FROM_EMAIL}")
print()

if not SMTP_PASSWORD:
    print("❌ SMTP_PASSWORD não está configurada!")
    exit(1)

try:
    print("🔄 Conectando ao servidor SMTP...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    
    print("🔒 Iniciando TLS...")
    server.starttls()
    
    print("🔐 Fazendo login...")
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    
    print("📧 Criando mensagem de teste...")
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = SMTP_USERNAME  # Enviar para si mesmo
    msg['Subject'] = 'Teste SMTP - macOS InstallAssistant'
    
    body = """
    <html>
    <body>
        <h2>🧪 Teste SMTP Funcionando!</h2>
        <p>Este é um teste direto do SMTP do Gmail.</p>
        <p>Se você recebeu este e-mail, o SMTP está configurado corretamente.</p>
        <hr>
        <p><small>Enviado via Python SMTP Test</small></p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    print("📤 Enviando e-mail...")
    server.send_message(msg)
    
    print("🔌 Fechando conexão...")
    server.quit()
    
    print("✅ E-mail enviado com sucesso via SMTP!")
    print(f"📧 Enviado para: {SMTP_USERNAME}")
    
except Exception as e:
    print(f"❌ Erro no teste SMTP: {e}")
    print(f"🔍 Tipo do erro: {type(e).__name__}")
    
    if "Username and Password not accepted" in str(e):
        print("\n💡 Possíveis soluções:")
        print("1. Verifique se a senha de aplicativo está correta")
        print("2. Certifique-se de que a autenticação de 2 fatores está ativada")
        print("3. Gere uma nova senha de aplicativo no Google")
        print("4. Verifique se não há espaços na senha")