# run.py (VERSÃO FINAL PARA PRODUÇÃO - Apenas Setup)

import flet as ft # Mantido para tipagem ou para garantir que a lib seja acessível
from app.main import main # Mantido, mas não usado para iniciar o app
import os
from openpyxl import Workbook
from app.models import init_db # Importado para inicializar o banco de dados

# Caminho para o template do inventário na pasta de dados
INVENTARIO_TEMPLATE_PATH = os.path.join("data", "inventario_principal.xlsx")
# Caminho para o DB na pasta de dados
DB_PATH = os.path.join("data", "projeto2.db") 

def setup_initial_files():
    """Garante que as pastas, o arquivo de template e o DB existam."""
    print("Iniciando Setup do Ambiente...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # 1. Setup do Banco de Dados
    if not os.path.exists(DB_PATH):
        try:
            init_db() # Chama a função que cria as tabelas no models.py
            print(f"Banco de dados '{DB_PATH}' criado com sucesso.")
        except Exception as e:
            print(f"Erro ao inicializar o DB: {e}")
            
    # 2. Setup do Template Excel
    if not os.path.exists(INVENTARIO_TEMPLATE_PATH):
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Planilha1"
            ws.append(["Datas", "", "", ""]) 
            ws.append(["Código", "Produto", "Data", "Quantidade"]) 
            
            wb.save(INVENTARIO_TEMPLATE_PATH)
            print(f"Arquivo '{INVENTARIO_TEMPLATE_PATH}' criado com sucesso.")
        except Exception as e:
            print(f"Erro ao criar o arquivo de inventário: {e}")
            
    print("Setup de arquivos, template e DB concluído.")

if __name__ == "__main__":
    setup_initial_files()
    # A linha ft.app(...) FOI REMOVIDA.
    # O servidor Uvicorn agora irá iniciar o ft.app de forma limpa.
