# 1. Imagem base
FROM python:3.11-slim

# 2. Configuração do ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
WORKDIR $APP_HOME

# NOVO: Variável CRUCIAL para forçar o Flet a rodar em modo Headless (sem GUI)
ENV FLET_DISPLAY false

# 3. Instalar dependências nativas (GTK, Flutter, e OpenCV)
# Esta lista abrangente garante que todas as libs de renderização e OpenCV estejam presentes.
RUN apt-get update && apt-get install -y \
    build-essential \
    # Dependências do Flet/Flutter/GTK (CORREÇÃO para libgtk-3.so.0):
    libgtk-3-0 \
    libglib2.0-0 \
    libgconf-2-4 \
    libfontconfig1 \
    libfreetype6 \
    # Dependências gráficas/X11 comuns:
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm-dev \
    mesa-utils \
    # Dependências do OpenCV:
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    # Limpa o cache
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o código do aplicativo
COPY . $APP_HOME

# 6. Expor a porta que o Flet usa por padrão
EXPOSE 8550

# 7. Comando de inicialização
CMD ["flet", "run", "--host", "0.0.0.0", "run.py"]
