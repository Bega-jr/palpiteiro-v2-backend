# Dockerfile para Render (Flask + pandas + openpyxl)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# instalar dependências do SO necessárias para pandas/openpyxl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# copiar código
COPY . /app

# expõe porta padrão (Render define PORT env)
ENV PORT 5000

# cria diretório para logs / armazenamento local se precisar
RUN mkdir -p /data
VOLUME /data

# comando de execução (gunicorn)
CMD exec gunicorn --bind 0.0.0.0:$PORT app:app --workers 4 --threads 4 --timeout 120
