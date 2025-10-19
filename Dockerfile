
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o código do aplicativo
# CORREÇÃO CRUCIAL: Copia o CONTEÚDO da pasta local 'src/' para o WORKDIR '/app'
COPY src/ .

# 6. Expor a porta.
EXPOSE 8550

# 7. Comando de inicialização (FINAL E ESTÁVEL)
# Executa o setup (run.py) e, em seguida, inicia o servidor Uvicorn na porta dinâmica $PORT.
CMD ["/bin/bash", "-c", "python run.py && uvicorn app.main:main --host 0.0.0.0 --port $PORT"]

