#!/usr/bin/env python3
"""
🥑 PÁGINAS ABACATEPAY
====================

Páginas de retorno e conclusão para integração AbacatePay
"""

from flask import Flask, request, render_template_string
from datetime import datetime

# Importar app Flask do sistema principal
try:
    from payment_api import app
except ImportError:
    app = Flask(__name__)

@app.route('/payment-success')
def payment_success():
    """Página de sucesso do pagamento AbacatePay"""
    payment_id = request.args.get('id', 'N/A')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pagamento Realizado - AbacatePay</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #4CAF50, #8BC34A);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 600px;
                width: 100%;
            }
            .success-icon {
                font-size: 80px;
                color: #4CAF50;
                margin-bottom: 20px;
            }
            h1 {
                color: #2E7D32;
                margin-bottom: 20px;
                font-size: 28px;
            }
            .message {
                color: #666;
                font-size: 18px;
                line-height: 1.6;
                margin-bottom: 30px;
            }
            .info-box {
                background: #E8F5E8;
                border: 1px solid #C3E6C3;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .steps {
                text-align: left;
                margin: 20px 0;
            }
            .step {
                display: flex;
                align-items: center;
                margin: 10px 0;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            .step-number {
                background: #4CAF50;
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 15px;
                font-weight: bold;
            }
            .button {
                display: inline-block;
                background: linear-gradient(135deg, #4CAF50, #8BC34A);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 10px;
                margin: 10px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .button:hover {
                transform: translateY(-2px);
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>Pagamento Realizado com Sucesso!</h1>
            <p class="message">
                Seu pagamento foi processado e você receberá um email com as instruções 
                de ativação em alguns minutos.
            </p>
            
            <div class="info-box">
                <h3>📧 Próximos Passos:</h3>
                <div class="steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div>Verifique seu email (incluindo spam/lixo eletrônico)</div>
                    </div>
                    <div class="step">
                        <div class="step-number">2</div>
                        <div>Baixe o aplicativo macOS InstallAssistant Browser</div>
                    </div>
                    <div class="step">
                        <div class="step-number">3</div>
                        <div>Use o serial enviado por email para ativar</div>
                    </div>
                </div>
            </div>
            
            <div class="info-box">
                <h3>🎯 Informações Importantes:</h3>
                <p><strong>Produto:</strong> Licença macOS InstallAssistant Browser</p>
                <p><strong>Valor:</strong> R$ 26,50</p>
                <p><strong>ID do Pagamento:</strong> {{ payment_id }}</p>
                <p><strong>Status:</strong> ✅ Processado com Sucesso</p>
            </div>
            
            <a href="https://web-production-1513a.up.railway.app/api/downloads/macOS-InstallAssistant-Browser.dmg" class="button">
                📥 Baixar Aplicativo
            </a>
            
            <div class="footer">
                <p>Em caso de dúvidas, entre em contato: hackintoshandbeyond@gmail.com</p>
                <p>Processado via AbacatePay • {{ timestamp }}</p>
            </div>
        </div>
    </body>
    </html>
    """.replace('{{ payment_id }}', payment_id).replace('{{ timestamp }}', datetime.now().strftime('%d/%m/%Y às %H:%M:%S'))
    
    return html

@app.route('/payment-cancel')
def payment_cancel():
    """Página de cancelamento do pagamento AbacatePay"""
    payment_id = request.args.get('id', 'N/A')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pagamento Cancelado - AbacatePay</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #FF6B6B, #FFE66D);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 600px;
                width: 100%;
            }
            .cancel-icon {
                font-size: 80px;
                color: #FF6B6B;
                margin-bottom: 20px;
            }
            h1 {
                color: #D32F2F;
                margin-bottom: 20px;
                font-size: 28px;
            }
            .message {
                color: #666;
                font-size: 18px;
                line-height: 1.6;
                margin-bottom: 30px;
            }
            .info-box {
                background: #FFF3E0;
                border: 1px solid #FFE0B2;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .button {
                display: inline-block;
                background: linear-gradient(135deg, #4CAF50, #8BC34A);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 10px;
                margin: 10px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .button:hover {
                transform: translateY(-2px);
            }
            .button.secondary {
                background: linear-gradient(135deg, #2196F3, #21CBF3);
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="cancel-icon">⚠️</div>
            <h1>Pagamento Cancelado</h1>
            <p class="message">
                Seu pagamento foi cancelado ou não foi concluído. 
                Não se preocupe, nenhuma cobrança foi realizada.
            </p>
            
            <div class="info-box">
                <h3>💡 O que aconteceu?</h3>
                <p>O pagamento pode ter sido cancelado por você ou por algum problema técnico temporário.</p>
                <p>Você pode tentar novamente quando quiser!</p>
            </div>
            
            <div class="info-box">
                <h3>🎯 Detalhes:</h3>
                <p><strong>Produto:</strong> Licença macOS InstallAssistant Browser</p>
                <p><strong>Valor:</strong> R$ 26,50</p>
                <p><strong>ID de Referência:</strong> {{ payment_id }}</p>
                <p><strong>Status:</strong> ❌ Cancelado</p>
            </div>
            
            <a href="https://web-production-1513a.up.railway.app/" class="button">
                🔄 Tentar Novamente
            </a>
            
            <a href="mailto:hackintoshandbeyond@gmail.com" class="button secondary">
                📧 Contato Suporte
            </a>
            
            <div class="footer">
                <p>Precisa de ajuda? Entre em contato: hackintoshandbeyond@gmail.com</p>
                <p>Processado via AbacatePay • {{ timestamp }}</p>
            </div>
        </div>
    </body>
    </html>
    """.replace('{{ payment_id }}', payment_id).replace('{{ timestamp }}', datetime.now().strftime('%d/%m/%Y às %H:%M:%S'))
    
    return html

@app.route('/payment-complete')
def payment_complete():
    """Página de pagamento completo AbacatePay (webhook processado)"""
    payment_id = request.args.get('id', 'N/A')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pagamento Confirmado - AbacatePay</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea, #764ba2);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 600px;
                width: 100%;
            }
            .complete-icon {
                font-size: 80px;
                color: #667eea;
                margin-bottom: 20px;
            }
            h1 {
                color: #5a67d8;
                margin-bottom: 20px;
                font-size: 28px;
            }
            .message {
                color: #666;
                font-size: 18px;
                line-height: 1.6;
                margin-bottom: 30px;
            }
            .info-box {
                background: #EBF4FF;
                border: 1px solid #C3DAFE;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .success-box {
                background: #F0FDF4;
                border: 1px solid #BBF7D0;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .button {
                display: inline-block;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 10px;
                margin: 10px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .button:hover {
                transform: translateY(-2px);
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="complete-icon">🎉</div>
            <h1>Pagamento Confirmado!</h1>
            <p class="message">
                Seu pagamento foi confirmado e processado com sucesso! 
                Você já deve ter recebido o email com suas informações de ativação.
            </p>
            
            <div class="success-box">
                <h3>✅ Pagamento Processado</h3>
                <p>Seu pagamento foi confirmado pelo sistema AbacatePay e nosso sistema já processou sua licença.</p>
            </div>
            
            <div class="info-box">
                <h3>📧 Email Enviado</h3>
                <p>Você deve ter recebido um email com:</p>
                <ul style="text-align: left; margin: 10px 0; padding-left: 20px;">
                    <li>Seu serial de ativação único</li>
                    <li>Link para download do aplicativo</li>
                    <li>Instruções detalhadas de instalação</li>
                    <li>Informações de suporte técnico</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3>🎯 Detalhes da Compra:</h3>
                <p><strong>Produto:</strong> Licença macOS InstallAssistant Browser</p>
                <p><strong>Valor:</strong> R$ 26,50</p>
                <p><strong>ID:</strong> {{ payment_id }}</p>
                <p><strong>Status:</strong> ✅ Confirmado e Processado</p>
            </div>
            
            <a href="https://web-production-1513a.up.railway.app/api/downloads/macOS-InstallAssistant-Browser.dmg" class="button">
                📥 Baixar Aplicativo Agora
            </a>
            
            <div class="footer">
                <p>Não recebeu o email? Verifique sua caixa de spam ou entre em contato: hackintoshandbeyond@gmail.com</p>
                <p>Processado via AbacatePay • {{ timestamp }}</p>
            </div>
        </div>
    </body>
    </html>
    """.replace('{{ payment_id }}', payment_id).replace('{{ timestamp }}', datetime.now().strftime('%d/%m/%Y às %H:%M:%S'))
    
    return html

if __name__ == "__main__":
    print("🥑 Páginas AbacatePay carregadas:")
    print("- /payment-success")
    print("- /payment-cancel") 
    print("- /payment-complete")
