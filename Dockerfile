# Dockerfile - Passos 1 e 2 permanecem iguais

# 3. Instalar dependências nativas (Crucial para Flet/GTK e OpenCV)
# Usaremos uma lista abrangente para cobrir requisitos comuns de GUI em ambiente headless.
RUN apt-get update && apt-get install -y \
    build-essential \
    # Flet/Flutter/GTK (CORREÇÃO para libgtk-3.so.0):
    libgtk-3-0 \
    libglib2.0-0 \
    libgconf-2-4 \
    libfontconfig1 \
    libfreetype6 \
    # Dependências gráficas/X11 comuns em ambientes Headless:
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
    
# ... (O restante do Dockerfile permanece igual)
