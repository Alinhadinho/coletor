import flet as ft # Mantemos o import, mas não o usamos para iniciar o app
from app.main import main # Mantemos o import
import os
from openpyxl import Workbook
from app.models import init_db # Importar init_db para garantir a criação do DB antes do app

# Caminho para o template do inventário na pasta de dados
INVENTARIO_TEMPLATE_PATH = os.path.join("data", "inventario_principal.xlsx")

def setup_initial_files():
    """Garante que as pastas, o arquivo de template e o DB existam."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Inicializa o banco de dados (cria o arquivo projeto2.db e tabelas)
    init_db() 
    
    if not os.path.exists(INVENTARIO_TEMPLATE_PATH):
        try:
            wb = Workbook()
            # Adiciona o cabeçalho inicial
            ws = wb.active
            ws.title = "Planilha1"
            ws.append(["Datas", "", "", ""]) # Linha 1
            ws.append(["Código", "Produto", "Data", "Quantidade"]) # Linha 2
            
            wb.save(INVENTARIO_TEMPLATE_PATH)
            print(f"Arquivo '{INVENTARIO_TEMPLATE_PATH}' criado com sucesso.")
        except Exception as e:
            print(f"Erro ao criar o arquivo de inventário: {e}")

if __name__ == "__main__":
    setup_initial_files()
    # A chamada ft.app(...) FOI REMOVIDA.
    # O servidor Uvicorn a chamará separadamente via CMD do Docker.
    print("Setup de pastas e inicialização do DB concluídos.")
