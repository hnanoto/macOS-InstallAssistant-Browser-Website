#!/usr/bin/env python3
"""WSGI entry point for payment_api."""

import os
import sys

# Garantir que o diretório atual esteja no PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from payment_api import app

application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
