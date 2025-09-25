FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

WORKDIR /app

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copiar dependências do backend apenas
COPY website/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar código do backend
COPY website/api/ /app/website/api/

# Garantir diretório de uploads persistente
RUN mkdir -p /app/website/uploads

EXPOSE 5000

CMD ["python", "website/api/payment_api.py"]

