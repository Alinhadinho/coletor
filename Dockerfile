# 1. Imagem base: Alpine é leve, mas para OpenCV pode ser mais seguro usar a imagem slim ou a padrão
# Usaremos uma imagem slim para compatibilidade com bibliotecas nativas como OpenCV
FROM python:3.11-slim

# 2. Configuração do ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
WORKDIR $APP_HOME

# 3. Instalar dependências nativas (necessárias para OpenCV e possivelmente outras)
# O OpenCV costuma precisar de algumas bibliotecas de imagem e outras dependências nativas.
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    # Dependências comuns para OpenCV:
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o código do aplicativo
# Copia o código para a pasta /app no contêiner
COPY . $APP_HOME

# 6. Expor a porta que o Flet usa por padrão (8550)
EXPOSE 8550

# 7. Comando de inicialização
# Este comando é executado quando o contêiner inicia. 
# Ele irá rodar o setup_initial_files() e iniciar o servidor Flet.
CMD ["flet", "run", "--host", "0.0.0.0", "run.py"]
# Nota: --host 0.0.0.0 é crucial para que o contêiner possa ser acessado externamente.