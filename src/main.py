# src/main.py (New name for the setup script)
import flet as ft 
from app.main import main
import os
from openpyxl import Workbook
from app.models import init_db 

# Caminho para o template do inventário na pasta de dados
INVENTARIO_TEMPLATE_PATH = os.path.join("data", "inventario_principal.xlsx")

def setup_initial_files():
    """Garante que as pastas, o arquivo de template e o DB existam."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    init_db() 
    
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

if __name__ == "__main__":
    setup_initial_files()
    print("Setup de pastas, template e DB concluídos.")
