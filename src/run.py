# src/run.py (VERSÃO FINAL)
import flet as ft 
from app.main import main
import os
from openpyxl import Workbook
from app.models import init_db # Importado para garantir a criação do DB

# Caminho para o template do inventário na pasta de dados
INVENTARIO_TEMPLATE_PATH = os.path.join("data", "inventario_principal.xlsx")

def setup_initial_files():
    """Garante que as pastas, o arquivo de template e o DB existam."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Inicializa o banco de dados (cria o arquivo projeto2.db)
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
    # ft.app(...) FOI REMOVIDA para evitar o erro de GTK.
    print("Setup de pastas, template e DB concluídos.")
