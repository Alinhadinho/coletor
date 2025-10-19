# 1. Imagem base: usa a versão slim para estabilidade
FROM python:3.11-slim

# 2. Configuração do ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# CRUCIAL: Força o Flet a rodar em modo Headless (sem GUI)
ENV FLET_DISPLAY false 
ENV APP_HOME /app
WORKDIR $APP_HOME

# 3. Instalar dependências nativas (apenas o essencial para Slim e OpenCV)
# Reduzimos a lista para evitar conflitos de GTK, mas mantemos o necessário para Python/OpenCV.
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o código do aplicativo
# CORREÇÃO: Copia o CONTEÚDO da pasta local 'src/' para o WORKDIR '/app' no contêiner
COPY src/ .

# 6. Expor a porta. Usamos o padrão Flet, mas o Uvicorn usará a variável $PORT do Render
EXPOSE 8550

# 7. Comando de inicialização (CRUCIAL)
# Usa /bin/bash -c para executar comandos sequenciais:
# 1. 'python run.py': Executa o setup do DB (setup_initial_files).
# 2. '&& uvicorn...': Inicia o servidor de produção, usando a porta dinâmica $PORT do Render.
CMD ["/bin/bash", "-c", "python run.py && uvicorn app.main:main --host 0.0.0.0 --port $PORT"]
