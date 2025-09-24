#!/usr/bin/env python3
"""
Script para forçar o Railway a reconhecer as mudanças
"""

import os
import time
from datetime import datetime

def create_deployment_trigger():
    """Cria um arquivo que força o Railway a fazer redeploy"""
    
    print("🚀 FORÇANDO REDEPLOY DO RAILWAY")
    print("=" * 50)
    
    # Criar um arquivo de trigger
    trigger_file = "deployment_trigger.txt"
    
    with open(trigger_file, "w") as f:
        f.write(f"Deployment trigger: {datetime.now().isoformat()}\n")
        f.write("Start command: python enhanced_payment_api.py\n")
        f.write("Email provider: resend\n")
        f.write("Status: ready for deployment\n")
    
    print(f"✅ Arquivo de trigger criado: {trigger_file}")
    
    # Verificar se o arquivo railway.json existe
    if os.path.exists("railway.json"):
        print("✅ Arquivo railway.json existe")
        with open("railway.json", "r") as f:
            content = f.read()
            if "enhanced_payment_api.py" in content:
                print("✅ railway.json contém o comando correto")
            else:
                print("❌ railway.json não contém o comando correto")
    else:
        print("❌ Arquivo railway.json não existe")
    
    # Verificar se o arquivo enhanced_payment_api.py existe
    if os.path.exists("enhanced_payment_api.py"):
        print("✅ Arquivo enhanced_payment_api.py existe")
    else:
        print("❌ Arquivo enhanced_payment_api.py não existe")
    
    print(f"\n📋 PRÓXIMOS PASSOS:")
    print("1. Fazer commit do arquivo de trigger")
    print("2. Push para o repositório")
    print("3. Aguardar Railway detectar as mudanças")
    print("4. Verificar se o redeploy foi iniciado")

if __name__ == "__main__":
    create_deployment_trigger()



