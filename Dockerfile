# 1. Imagem base: Usamos a versão slim para manter o contêiner leve,
# mas com compatibilidade para bibliotecas nativas como OpenCV.
FROM python:3.11-slim

# 2. Configuração do ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
WORKDIR $APP_HOME

# 3. Instalar dependências nativas (Crucial para Flet/GTK e OpenCV)
# O apt-get install deve ser executado antes do pip install.
RUN apt-get update && apt-get install -y \
    build-essential \
    # Dependências do Flet/Flutter/GTK (CORREÇÃO para libgtk-3.so.0):
    libgtk-3-0 \
    libglib2.0-0 \
    libgconf-2-4 \
    libfontconfig1 \
    libfreetype6 \
    # Dependências do OpenCV (para a câmera/scanner):
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    # Limpa o cache após a instalação para manter o tamanho da imagem menor
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar dependências Python
# O requirements.txt (já corrigido com 'flet-webview') é copiado e usado.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o código do aplicativo
# Copia o código da raiz do seu projeto (incluindo run.py, app/, data/) para /app
COPY . $APP_HOME

# 6. Expor a porta que o Flet usa por padrão
EXPOSE 8550

# 7. Comando de inicialização
# Inicia o app Flet, escutando em todas as interfaces de rede (0.0.0.0)
CMD ["flet", "run", "--host", "0.0.0.0", "run.py"]
