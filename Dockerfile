# Dockerfile (Versão Definitiva)

# 1. Imagem base
FROM python:3.11-slim

# 2. Configuração do ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLET_DISPLAY false # CRUCIAL: Força o Flet a rodar em modo Headless
ENV APP_HOME /app
WORKDIR $APP_HOME

# 3. Instalar dependências nativas (apenas o essencial)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 libxext6 libxrender-dev libgl1 \
    libfontconfig1 libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o código do aplicativo
# CORREÇÃO: Copia o CONTEÚDO da pasta local 'src/' para o WORKDIR '/app'
COPY src/ .

# 6. Expor a porta.
EXPOSE 8550

# 7. Comando de inicialização (FINAL E ESTÁVEL)
# Executa o setup (run.py) e, em seguida, inicia o servidor Uvicorn na porta dinâmica $PORT.
CMD ["/bin/bash", "-c", "python run.py && uvicorn app.main:main --host 0.0.0.0 --port $PORT"]
