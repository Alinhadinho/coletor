# 1. Imagem base
FROM python:3.11-slim
LABEL build_version="1.0.4-setup-init"

# 2. Configuração do ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLET_DISPLAY=false
ENV APP_HOME=/app
WORKDIR $APP_HOME

# 3. Instalar dependências nativas (essenciais para Slim/OpenCV)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 libxext6 libxrender-dev libgl1 \
    libfontconfig1 libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# 4. Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o código do aplicativo
COPY src/ .

# 6. Rodar o setup inicial (gera DB e template XLSX)
RUN python main.py

# 7. Expor a porta usada pelo Render
EXPOSE 8000

# 8. Comando de inicialização do app
CMD ["uvicorn", "app.main:asgi_app", "--host", "0.0.0.0", "--port", "8000"]
