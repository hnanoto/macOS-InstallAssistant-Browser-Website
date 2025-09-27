#!/usr/bin/env python3
"""
Teste simples para verificar se o Railway consegue executar Python
"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "message": "Simple test server is running",
        "port": os.getenv('PORT', '5002')
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "Test server is working",
        "status": "ok"
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    print(f"Starting simple test server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)