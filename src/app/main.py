import flet as ft
import datetime
import os
from sqlalchemy.orm import joinedload
from .models import Produto, Pasta, SessionLocal, init_db
from .ExcelScript import adicionar_e_formatar_produtos
import cv2
from flet_webview import WebView

# --- Constantes e Configurações ---
CORES = { "background": "#F1F0FB", "primary": "#0A2E73", "danger": "#E2002E", "success": "#28A745", "title": "#1A2E73", "subtitle": "#444444" }
DADOS_API_SIMULADOS = { "7891000000001": {"nome": "Leite Integral UHT"}, "7891000000002": {"nome": "Pão de Forma Tradicional"}, "7891000000003": {"nome": "Queijo Mussarela Fatiado"}, "7891000000004": {"nome": "Refrigerante Cola 2L"}, "7891000000005": {"nome": "Biscoito Cream Cracker"} }
REPORTS_DIR = "reports"
TEMPLATE_PATH = os.path.join("data", "inventario_principal.xlsx")

def buscar_produto_na_api(tipo: str, valor: str):
    if tipo == "EAN" and valor in DADOS_API_SIMULADOS: return DADOS_API_SIMULADOS[valor]
    return None

# ESTA É A FUNÇÃO PRINCIPAL QUE RECEBE O OBJETO ft.Page
# O Uvicorn a chama indiretamente via o wrapper asgi_app abaixo.
def main(page: ft.Page): 
    page.title = "Coletor de Conferência"
    page.window.height = 800
    page.window.width = 400
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = CORES["background"]

    # init_db() # REMOVIDO: A chamada agora está no src/main.py (antigo run.py) para o setup.

    # (Variáveis de estado)
    selected_products = {}
    selected_folders = {}
    current_view_context = {'value': 'meus_produtos'}
    active_folder_id = {'value': None}
    filtro_selecionado = {"value": "Todos"}
    busca_valor = {"value": ""}
    busca_pasta_valor = {"value": ""}
    sort_order = {'value': 'default'}
    quick_count_mode = {'value': False}

    prodList = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)
    pastaList = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)
    header_text = ft.Text(size=22, weight=ft.FontWeight.BOLD)

    hoje_date = datetime.date.today()
    hoje_str = datetime.date.today().strftime("%d/%m/%Y")

    # --- LÓGICA DO SCANNER MULTIPLATAFORMA ---

    # Função para o scanner WebView (Mobile)
    def show_webview_scanner():
        """Exibe o leitor de código usando scanner.html dentro de um WebView."""

        def handle_message(e):
            code = e.data
            if code == "CAMERA_ERROR":
                page.snack_bar = ft.SnackBar(ft.Text("Erro ao acessar a câmera. Verifique as permissões."), bgcolor=ft.Colors.RED_400)
            elif code:
                page.snack_bar = ft.SnackBar(ft.Text(f"Código lido: {code}"), bgcolor=ft.Colors.GREEN_400)
                # You can now automatically process the code
                # For example, find the product and open the edit screen.
            
            page.snack_bar.open = True
            voltar_para_meus_produtos()
            page.update()

        # 🔹 CORREÇÃO APLICADA AQUI 🔹
        # Flet's asset server makes the file available at the root URL.
        # No complex path calculation is needed.
        webview_control = WebView(url="/scanner.html") # The URL is now simple and reliable
        webview_control.on_message = handle_message

        # Monta o layout
        scanner_view = ft.Container(
            expand=True,
            content=ft.Column([
                ft.Container(
                    bgcolor=CORES["primary"],
                    height=50,
                    content=ft.Row([
                        ft.IconButton(
                            ft.Icons.ARROW_BACK,
                            icon_color=ft.Colors.WHITE,
                            on_click=lambda e: voltar_para_meus_produtos()
                        ),
                        ft.Text("Aponte para o Código", color=ft.Colors.WHITE, size=20)
                    ], alignment=ft.MainAxisAlignment.START),
                ),
                webview_control
            ], spacing=0)
        )

        # Ajusta a interface do app
        page.appbar.visible = False
        page.bottom_appbar.visible = False
        page.floating_action_button.visible = False
        main_content.content = scanner_view
        page.update()


    # Função para o scanner OpenCV (Desktop) - Restaurada do seu código original
    def show_opencv_scanner(pasta_id_forced=None):
        def run_scanner_and_get_code():
            # AVISO: cv2.VideoCapture(0) e cv2.imshow não funcionam no Render/Nuvem!
            print("AVISO: OpenCV Scanner iniciado (Modo placeholder no Render)")
            return None 

        def handle_capture(e):
            codigo_lido = run_scanner_and_get_code()
            if codigo_lido:
                codigo_field.value = codigo_lido
                page.snack_bar = ft.SnackBar(ft.Text(f"Código capturado: {codigo_lido}"))
                page.snack_bar.open = True
                page.update()

        def confirmar_codigo_manual(ev):
            valor = codigo_field.value.strip() if codigo_field.value else ""
            if not valor:
                page.snack_bar = ft.SnackBar(ft.Text("Digite ou capture um código primeiro."), bgcolor=CORES["danger"])
                page.snack_bar.open = True
                page.update()
                return
            tipo = "EAN" if valor.isdigit() and len(valor) == 13 else "PLU" if valor.isdigit() and len(valor) == 5 else None
            if not tipo:
                page.snack_bar = ft.SnackBar(ft.Text("Código inválido."), bgcolor=CORES["danger"])
                page.snack_bar.open = True
                page.update()
                return
            criar_novo_registro(tipo, valor, pasta_id_forced)

        camera_overlay = ft.Container(
            expand=True, alignment=ft.alignment.center, bgcolor=ft.Colors.BLACK54,
            content=ft.Stack([
                ft.Column([
                    ft.Container(width=250, height=150, border=ft.border.all(2, ft.Colors.WHITE54), border_radius=10),
                    ft.Text("Aponte para o código", color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.ElevatedButton(
                    "📸 Capturar Código", icon=ft.Icons.CAMERA_ALT, on_click=handle_capture,
                    style=ft.ButtonStyle(shape=ft.CircleBorder(), padding=25)
                )
            ]),
        )
        codigo_field = ft.TextField(
            hint_text="Ou digite o código manualmente...", width=280, text_align=ft.TextAlign.CENTER,
            on_change=lambda e: only_digits_max(e, 13)
        )
        confirmar_button = ft.ElevatedButton("Confirmar", icon=ft.Icons.CHECK, on_click=confirmar_codigo_manual)
        
        camera_ui = ft.Container(
            expand=True,
            content=ft.Column(
                [
                    ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: voltar_para_meus_produtos()), ft.Text("Leitor de Código", size=22, weight=ft.FontWeight.BOLD)]),
                    ft.Divider(), camera_overlay, ft.Container(height=20),
                    codigo_field, ft.Container(height=10),
                    ft.Row([ft.TextButton("Cancelar", on_click=lambda e: voltar_para_meus_produtos()), confirmar_button], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=15,
        )
        
        page.appbar.visible = False
        page.bottom_appbar.visible = False
        page.floating_action_button.visible = False
        main_content.content = camera_ui
        page.update()

    # --- ESCOLHA DA FUNÇÃO DO SCANNER BASEADA NA PLATAFORMA ---
    is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
    scanner_function = show_webview_scanner if is_mobile else show_opencv_scanner

    # (Funções de UI, CRUD, etc. continuam aqui)
    def handle_date_change(e):
        if e.control.value:
            selected_date_str = e.control.value.strftime("%d/%m/%Y")
            validade_field.value = selected_date_str
        page.update()

    date_picker = ft.DatePicker(on_change=handle_date_change, first_date=datetime.datetime(2023, 1, 1), last_date=datetime.datetime.now() + datetime.timedelta(days=365 * 5))
    page.overlay.append(date_picker)

    def only_digits_max(e, max_len):
        v = "".join(filter(str.isdigit, e.control.value)); e.control.value = v[:max_len]; page.update()
        
    def cor_validade(data_str: str):
        try:
            data = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            delta = (data - hoje_date).days
            if delta < 0: return CORES["danger"]
            elif delta <= 7: return "#FFC107"
            else: return CORES["success"]
        except: return CORES["subtitle"]

    def periodo_validade_boolean(data_str: str):
        try:
            data = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            delta = (data - hoje_date).days
            if filtro_selecionado["value"] == "Próximos 7 dias": return 0 <= delta <= 7
            elif filtro_selecionado["value"] == "Vencem este Mês": return data.year == hoje_date.year and data.month == hoje_date.month and delta >= 0
            elif filtro_selecionado["value"] == "Vencem este Ano": return data.year == hoje_date.year and delta >= 0
            elif filtro_selecionado["value"] == "Vencidos": return delta < 0
            else: return True
        except: return filtro_selecionado["value"] == "Todos"

    def update_product_bottom_bar_visibility():
        if selected_products:
            page.bottom_appbar.visible = False; action_bar_products.visible = True
            action_bar_products.content.controls[0].value = f"Selecionados: {len(selected_products)}"
            action_bar_folders.visible = False
        else:
            page.bottom_appbar.visible = True; action_bar_products.visible = False
            if current_view_context['value'] == 'pastas':
                 action_bar_folders.visible = bool(selected_folders)
            else:
                 action_bar_folders.visible = False
        page.update()

    def toggle_product_selection(e, produto: Produto):
        is_selected_now = e.control.value if hasattr(e.control, 'value') else produto.id not in selected_products
        if is_selected_now: selected_products[produto.id] = produto
        elif produto.id in selected_products: del selected_products[produto.id]
        update_product_bottom_bar_visibility(); atualizar_lista()

    def clear_selection(e=None):
        selected_products.clear(); selected_folders.clear()
        if current_view_context['value'] == 'pastas': atualizar_pastas()
        else: atualizar_lista()
        update_product_bottom_bar_visibility(); update_folder_bottom_bar_visibility()
    
    def update_folder_bottom_bar_visibility():
        if selected_folders and current_view_context['value'] == 'pastas':
            page.bottom_appbar.visible = False; action_bar_folders.visible = True
            action_bar_folders.content.controls[0].value = f"Pastas Selecionadas: {len(selected_folders)}"
            action_bar_products.visible = False
        else:
            page.bottom_appbar.visible = True; action_bar_folders.visible = False
        page.update()
        
    def toggle_folder_selection(e, pasta: Pasta):
        is_selected_now = e.control.value if hasattr(e.control, 'value') else pasta.id not in selected_folders
        if is_selected_now: selected_folders[pasta.id] = pasta
        elif pasta.id in selected_folders: del selected_folders[pasta.id]
        update_folder_bottom_bar_visibility()

    def criar_card(produto: Produto):
        cor = cor_validade(produto.data_validade or "")
        is_selected = produto.id in selected_products
        is_checkbox_visible = bool(selected_products)

        def handle_card_click(e):
            if is_checkbox_visible: e.control.content.controls[0].value = not e.control.content.controls[0].value; toggle_product_selection(e, produto) 
            else: abrir_edicao_registro(produto.id)
                
        def handle_long_press(e):
            if not is_checkbox_visible:
                clear_selection(); e.control.content.controls[0].value = True
                toggle_product_selection(type('FakeEvent', (object,), {'control': e.control.content.controls[0]})(), produto)
        
        menu_items = [ft.PopupMenuItem(text="Editar", icon=ft.Icons.EDIT, on_click=lambda _, p_id=produto.id: abrir_edicao_registro(p_id))]
        if current_view_context['value'] == 'compartilhados':
            menu_items.append(ft.PopupMenuItem(text="Parar de Compartilhar", icon=ft.Icons.STOP_CIRCLE_OUTLINED, on_click=lambda _, p_id=produto.id: unshare_product(p_id)))
        else:
            menu_items.append(ft.PopupMenuItem(text="Compartilhar", icon=ft.Icons.IOS_SHARE, on_click=lambda _, p_id=produto.id: share_single_product(p_id)))
            menu_items.append(ft.PopupMenuItem(text="Mover para Pasta", icon=ft.Icons.FOLDER_SHARED, on_click=lambda _, p_id=produto.id: open_move_dialog_single(p_id)))
        menu_items.append(ft.PopupMenuItem(text="Deletar Produto", content=ft.Row([ft.Icon(ft.Icons.DELETE, color=CORES["danger"]), ft.Text("Deletar Produto")]), on_click=lambda _, p_id=produto.id: deletar_produto(p_id)))

        title_row = ft.Row(spacing=6, alignment=ft.MainAxisAlignment.START, controls=[ft.Text(produto.nome, weight=ft.FontWeight.BOLD, size=14, color=CORES["title"])])
        if produto.is_shared and current_view_context['value'] != 'compartilhados':
            title_row.controls.append(ft.Icon(ft.Icons.GROUP, size=14, color=CORES["subtitle"], tooltip="Este item é compartilhado"))

        card_content = ft.Row(controls=[
            ft.Checkbox(value=is_selected, visible=is_checkbox_visible, on_change=lambda e, p=produto: toggle_product_selection(e, p)),
            ft.Icon(ft.Icons.SHOPPING_BASKET, size=40, color=CORES["primary"]),
            ft.Column(controls=[title_row, ft.Text(f"Validade: {produto.data_validade or 'N/A'}", size=12, color=cor), ft.Text(f"Qtd: {produto.quantidade}", size=12, color=CORES["subtitle"]), ft.Text(f"Pasta: {produto.pasta.nome if produto.pasta else 'N/A'}", size=10, color=CORES["primary"] if produto.pasta else ft.Colors.GREY_500)], expand=True),
            ft.PopupMenuButton(visible=not is_checkbox_visible, items=menu_items, icon=ft.Icons.MORE_VERT),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        return ft.Card(elevation=2, color=ft.Colors.WHITE, content=ft.Container(padding=10, on_click=handle_card_click, on_long_press=handle_long_press, content=card_content, bgcolor=ft.Colors.BLUE_GREY_50 if is_selected else None))

    def criar_card_pasta(pasta_obj, count):
        is_selected, is_checkbox_visible = pasta_obj.id in selected_folders, bool(selected_folders)
        def deletar_pasta(pasta_id):
            local_db = SessionLocal(); p = local_db.get(Pasta, pasta_id); cnt = local_db.query(Produto).filter(Produto.pasta_id == p.id).count() if p else 0
            if p and cnt == 0:
                local_db.delete(p); local_db.commit(); atualizar_pastas()
                page.snack_bar = ft.SnackBar(ft.Text("Pasta excluída")); page.snack_bar.open = True
            else: page.open(ft.AlertDialog(title=ft.Text("Erro"), content=ft.Text("Não é possível excluir pasta com produtos.")))
            local_db.close(); page.update()
        def handle_folder_click(e):
            if is_checkbox_visible: e.control.content.controls[0].value = not e.control.content.controls[0].value; toggle_folder_selection(e, pasta_obj)
            else: abrir_pasta(pasta_obj)
        def handle_folder_long_press(e):
            if not is_checkbox_visible:
                clear_selection(); e.control.content.controls[0].value = True
                toggle_folder_selection(type('FakeEvent', (object,), {'control': e.control.content.controls[0]})(), pasta_obj)
        return ft.Card(elevation=1, color=ft.Colors.WHITE, content=ft.Container(padding=8, on_click=handle_folder_click, on_long_press=handle_folder_long_press, bgcolor=ft.Colors.BLUE_GREY_50 if is_selected else None, content=ft.Row([ft.Checkbox(value=is_selected, visible=is_checkbox_visible, on_change=lambda e, p=pasta_obj: toggle_folder_selection(e, p)), ft.Icon(ft.Icons.FOLDER, size=36, color=CORES["primary"]), ft.Column([ft.Text(pasta_obj.nome, weight=ft.FontWeight.BOLD), ft.Text(f"{count} produtos", size=11)], expand=True), ft.IconButton(icon=ft.Icons.DELETE, icon_color=CORES["danger"], visible=not is_checkbox_visible, on_click=lambda _, pid=pasta_obj.id: deletar_pasta(pid))])))

    def atualizar_lista():
        prodList.controls.clear()
        produtos = get_visible_products()
        if not produtos: prodList.controls.append(ft.Text("Nenhum produto encontrado.", text_align=ft.TextAlign.CENTER, color=CORES["subtitle"]))
        else:
            for p in produtos: prodList.controls.append(criar_card(p))
        page.update()

    def atualizar_pastas():
        local_db = SessionLocal(); pastaList.controls.clear()
        pastas = local_db.query(Pasta).all(); term = busca_pasta_valor["value"].strip().lower()
        for p in pastas:
            if not term or term in p.nome.lower():
                cnt = local_db.query(Produto).filter(Produto.pasta_id == p.id).count()
                pastaList.controls.append(criar_card_pasta(p, cnt))
        local_db.close(); page.update()

    def share_single_product(produto_id: int):
        local_db = SessionLocal(); produto = local_db.get(Produto, produto_id)
        if produto:
            produto.is_shared = True; local_db.commit()
            page.snack_bar = ft.SnackBar(ft.Text(f"'{produto.nome}' agora está compartilhado."))
        else: page.snack_bar = ft.SnackBar(ft.Text("Produto não encontrado."), bgcolor=CORES["danger"])
        local_db.close(); page.snack_bar.open = True; page.update()

    def share_selected_products(e):
        if not selected_products: return
        local_db = SessionLocal(); count = 0
        for prod_id in selected_products.keys():
            produto = local_db.get(Produto, prod_id)
            if produto: produto.is_shared = True; count += 1
        local_db.commit(); local_db.close()
        clear_selection()
        page.snack_bar = ft.SnackBar(ft.Text(f"{count} produtos compartilhados.")); page.snack_bar.open = True; page.update()

    def unshare_product(produto_id: int):
        local_db = SessionLocal(); produto = local_db.get(Produto, produto_id)
        if produto:
            produto.is_shared = False; local_db.commit()
            page.snack_bar = ft.SnackBar(ft.Text(f"'{produto.nome}' não está mais compartilhado."))
        local_db.close(); page.snack_bar.open = True; atualizar_lista()

    def deletar_produto(produto_id: int):
        local_db = SessionLocal(); produto_a_deletar = local_db.get(Produto, produto_id)
        if produto_a_deletar:
            nome_prod = produto_a_deletar.nome
            local_db.delete(produto_a_deletar); local_db.commit()
            page.snack_bar = ft.SnackBar(ft.Text(f"Produto {nome_prod} deletado."))
            atualizar_lista()
        else: page.snack_bar = ft.SnackBar(ft.Text("Produto não encontrado."), bgcolor=CORES["danger"])
        local_db.close(); page.snack_bar.open = True; page.update()

    def delete_selected_products(e):
        if not selected_products: return
        def confirmar_delecao(ev):
            local_db = SessionLocal(); count = 0
            for prod_id in selected_products.keys():
                produto = local_db.get(Produto, prod_id) 
                if produto: local_db.delete(produto); count += 1
            local_db.commit(); local_db.close()
            page.close(dlg); clear_selection()
            page.snack_bar = ft.SnackBar(ft.Text(f"{count} produtos deletados.")); page.snack_bar.open = True; atualizar_lista()
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Confirmar Deleção"), content=ft.Text(f"Deletar {len(selected_products)} produtos?"), actions=[ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg)), ft.TextButton("Deletar", on_click=confirmar_delecao, style=ft.ButtonStyle(color=CORES["danger"]))])
        page.open(dlg)
    
    def exportar_xlsx(ev):
        items = get_products_from_selection()
        if not items: 
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum produto para exportar")); page.snack_bar.open = True; page.update(); return
        
        try:
            os.makedirs(REPORTS_DIR, exist_ok=True)
            produtos_lista = [{"nome": p.nome or "", "EAN": p.ean or "N/A", "PLU": p.plu or "N/A", "quantidade": p.quantidade or 0, "validade": p.data_validade or "01/01/1900"} for p in items]
            caminho_salvo = adicionar_e_formatar_produtos(TEMPLATE_PATH, produtos_lista, "Planilha1", REPORTS_DIR) 
            
            if selected_products or selected_folders: 
                clear_selection()
            
            page.snack_bar = ft.SnackBar(ft.Text(f"Exportação concluída! Salvo em: {os.path.basename(caminho_salvo)}")); page.snack_bar.open = True; page.update()
        except Exception as e: 
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao exportar: {e}"), bgcolor=ft.Colors.RED_400); page.snack_bar.open = True; page.update()
    
    def voltar_para_meus_produtos():
        page.appbar.visible = True
        page.bottom_appbar.visible = True
        page.floating_action_button.visible = True
        
        # Simplesmente volta para a view correta, a navegação principal cuida do resto
        if current_view_context['value'] == 'pastas':
            show_pastas(None)
        elif current_view_context['value'] == 'compartilhados':
            show_compartilhados(None)
        else:
            show_meus_produtos(None)
        
        page.update()

    filtro_dropdown = ft.Dropdown(options=[ft.dropdown.Option(text) for text in ["Todos", "Próximos 7 dias", "Vencem este Mês", "Vencem este Ano", "Vencidos"]], value=filtro_selecionado["value"], label="Filtro de Validade", width=300)
    busca_field = ft.TextField(hint_text="Buscar produto...", prefix_icon=ft.Icons.SEARCH, value=busca_valor["value"], on_change=lambda e: (busca_valor.update({"value": e.control.value}), atualizar_lista()), expand=True)
    busca_pasta_field = ft.TextField(hint_text="Buscar pasta...", prefix_icon=ft.Icons.SEARCH, on_change=lambda e: (busca_pasta_valor.update({"value": e.control.value}), atualizar_pastas()), expand=True)
    ean_field = ft.TextField(label="EAN (13 dígitos)", width=300, on_change=lambda e: only_digits_max(e, 13))
    plu_field = ft.TextField(label="PLU (5 dígitos)", width=300, on_change=lambda e: only_digits_max(e, 5))
    nome_field = ft.TextField(label="Nome do Produto", width=300)
    qtd_field = ft.TextField(label="Quantidade", width=300, on_change=lambda e: only_digits_max(e, 6))
    pasta_dropdown = ft.Dropdown(label="Pasta (opcional)", options=[], width=300)
    validade_field = ft.TextField(label="Data de Validade", width=300, value=hoje_str, read_only=True, suffix_icon=ft.Icons.CALENDAR_MONTH, on_click=lambda _: page.open(date_picker))
    share_checkbox = ft.Checkbox(label="Compartilhar este item", value=False)

    def salvar_produto(e):
        local_db = SessionLocal()
        produto_id = getattr(ean_field, "data", None) 
        ean, plu, nome, qtd, validade, pasta_id, is_shared_val = ean_field.value.strip(), plu_field.value.strip(), nome_field.value.strip(), int(qtd_field.value.strip() or "0"), validade_field.value.strip(), (int(pasta_dropdown.value) if pasta_dropdown.value else None), share_checkbox.value
        if not (ean or plu) or not nome:
            dlg = ft.AlertDialog(title=ft.Text("Erro"), content=ft.Text("EAN/PLU e Nome são obrigatórios."), actions=[ft.TextButton("OK", on_click=lambda _: page.close(dlg))]); page.open(dlg); local_db.close(); return
        if produto_id:
            produto = local_db.get(Produto, produto_id) 
            if produto:
                produto.ean, produto.plu, produto.nome, produto.quantidade, produto.data_validade, produto.pasta_id, produto.is_shared = ean or None, plu or None, nome, qtd, validade, pasta_id, is_shared_val
                msg = "Produto atualizado!"
        else:
            local_db.add(Produto(ean=ean or None, plu=plu or None, nome=nome, quantidade=qtd, data_validade=validade, pasta_id=pasta_id, is_shared=is_shared_val))
            msg = "Produto salvo!"
        local_db.commit(); local_db.close()
        page.snack_bar = ft.SnackBar(ft.Text(msg)); page.snack_bar.open = True
        voltar_para_meus_produtos()
        
    form_title = ft.Text("Adicionar Produto", size=20, weight=ft.FontWeight.BOLD)
    form_container = ft.Container(content=ft.Column([ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: voltar_para_meus_produtos()), form_title]), ean_field, plu_field, nome_field, qtd_field, validade_field, pasta_dropdown, share_checkbox, ft.Row([ft.ElevatedButton("Salvar", on_click=salvar_produto), ft.TextButton("Cancelar", on_click=lambda e: voltar_para_meus_produtos())])], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=True, padding=16)

    def criar_novo_registro(tipo, valor, pasta_id_forced=None):
        ean_field.data = None; form_title.value = "Adicionar Produto"
        pasta_dropdown.options = carregar_pastas_options(); pasta_dropdown.value = str(pasta_id_forced) if pasta_id_forced else None
        ean_field.read_only = False; plu_field.read_only = False
        ean_field.value, plu_field.value = (valor, "") if tipo == "EAN" else ("", valor)
        nome_field.value, qtd_field.value, validade_field.value, share_checkbox.value = "", "", hoje_str, False
        api_data = buscar_produto_na_api(tipo, valor)
        if api_data: nome_field.value = api_data.get("nome", "")
        
        page.appbar.visible = False
        page.bottom_appbar.visible = False
        page.floating_action_button.visible = False
        main_content.content = form_container
        page.update()
        
    def abrir_edicao_registro(produto_id: int):
        local_db = SessionLocal(); produto = local_db.get(Produto, produto_id); local_db.close()
        if not produto: page.snack_bar = ft.SnackBar(ft.Text("Produto não encontrado."), bgcolor=CORES["danger"]); page.snack_bar.open = True; page.update(); return
        ean_field.data = produto_id; form_title.value = "Editar Produto"
        pasta_dropdown.options = carregar_pastas_options(); pasta_dropdown.value = str(produto.pasta_id) if produto.pasta_id else None
        ean_field.value, plu_field.value, nome_field.value, qtd_field.value, validade_field.value, share_checkbox.value = produto.ean or "", produto.plu or "", produto.nome, str(produto.quantidade), produto.data_validade or hoje_str, produto.is_shared
        ean_field.read_only = True; plu_field.read_only = True
        
        page.appbar.visible = False
        page.bottom_appbar.visible = False
        page.floating_action_button.visible = False
        main_content.content = form_container
        page.update()

    def carregar_pastas_options():
        local_db = SessionLocal(); pastas = local_db.query(Pasta).all(); local_db.close()
        return [ft.dropdown.Option(str(p.id), p.nome) for p in pastas]
    
    def abrir_dialogo_criar_pasta(e):
        nome_field = ft.TextField(label="Nome da Pasta", width=250)
        def confirmar(ev):
            nome = nome_field.value.strip()
            if nome:
                local_db = SessionLocal(); local_db.add(Pasta(nome=nome)); local_db.commit(); local_db.close()
                page.close(dialogo); atualizar_pastas()
                page.snack_bar = ft.SnackBar(ft.Text(f"Pasta '{nome}' criada")); page.snack_bar.open = True; page.update()
        dialogo = ft.AlertDialog(modal=True, title=ft.Text("Criar Nova Pasta"), content=nome_field, actions=[ft.TextButton("Cancelar", on_click=lambda _: page.close(dialogo)), ft.TextButton("Criar", on_click=confirmar)])
        page.open(dialogo)

    def open_move_dialog_single(produto_id: int):
        pasta_options = carregar_pastas_options()
        if not pasta_options: page.snack_bar = ft.SnackBar(ft.Text("Crie uma pasta antes."), bgcolor=CORES["danger"]); page.snack_bar.open = True; page.update(); return
        move_dropdown = ft.Dropdown(label="Mover para", options=pasta_options, width=300)
        def confirmar_mover(ev):
            pasta_id = move_dropdown.value
            if not pasta_id: return
            local_db = SessionLocal(); produto = local_db.get(Produto, produto_id)
            if produto:
                produto.pasta_id = int(pasta_id); local_db.commit()
                page.snack_bar = ft.SnackBar(ft.Text(f"'{produto.nome}' movido com sucesso."))
                page.snack_bar.open = True
            local_db.close(); page.close(dlg); atualizar_lista()
        dlg = ft.AlertDialog(modal=True, title=ft.Text("Mover Produto"), content=ft.Column([ft.Text("Selecione a nova pasta:"), move_dropdown], tight=True), actions=[ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg)), ft.TextButton("Mover", on_click=confirmar_mover)])
        page.open(dlg)
    
    def open_move_dialog(e):
        if not selected_products: return
        pasta_options = carregar_pastas_options()
        if not pasta_options: page.snack_bar = ft.SnackBar(ft.Text("Crie uma pasta antes."), bgcolor=CORES["danger"]); page.snack_bar.open = True; page.update(); return
        move_dropdown = ft.Dropdown(label="Mover para", options=pasta_options, width=300)
        def confirmar_mover(ev):
            pasta_id = move_dropdown.value
            if not pasta_id: return
            local_db = SessionLocal()
            for prod_id in selected_products.keys():
                produto = local_db.get(Produto, prod_id) 
                if produto: produto.pasta_id = int(pasta_id)
            local_db.commit(); local_db.close()
            page.close(dlg); clear_selection()
            page.snack_bar = ft.SnackBar(ft.Text(f"{len(selected_products)} produtos movidos.")); page.snack_bar.open = True; atualizar_lista()
        dlg = ft.AlertDialog(modal=True, title=ft.Text(f"Mover {len(selected_products)} Produtos"), content=ft.Column([ft.Text("Selecione a nova pasta:"), move_dropdown], tight=True), actions=[ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg)), ft.TextButton("Mover", on_click=confirmar_mover)])
        page.open(dlg)

    def get_products_from_selection():
        if selected_products: return list(selected_products.values()) 
        elif selected_folders:
            local_db = SessionLocal()
            produtos = [p for pasta_id in selected_folders.keys() for p in local_db.query(Produto).options(joinedload(Produto.pasta)).filter(Produto.pasta_id == pasta_id).all()]
            local_db.close(); return produtos
        else: return get_visible_products() 

    def compartilhar_texto(ev):
        items = get_products_from_selection()
        if not items: page.snack_bar = ft.SnackBar(ft.Text("Nenhum item para compartilhar")); page.snack_bar.open = True; page.update(); return
        lines = [f"--- Lista de Produtos ({len(items)} itens) ---"]
        for p in items: lines.extend([f"\n{p.nome}", f"  * EAN: {p.ean or 'N/A'}", f"  * PLU: {p.plu or 'N/A'}", f"  * Quantidade: {p.quantidade}", f"  * Validade: {p.data_validade or 'N/A'}", f"  * Pasta: {p.pasta.nome if p.pasta else 'N/A'}"])
        page.set_clipboard("\n".join(lines))
        page.snack_bar = ft.SnackBar(ft.Text(f"Lista de {len(items)} itens copiada!")); page.snack_bar.open = True
        if selected_products or selected_folders: clear_selection()
        page.update()
        
    def set_sort_order(order: str):
        sort_order['value'] = order
        map_name = {"default": "Padrão", "name": "Nome", "date": "Data de Validade", "quantity": "Quantidade"}
        page.snack_bar = ft.SnackBar(ft.Text(f"Lista ordenada por: {map_name.get(order)}")); page.snack_bar.open = True
        atualizar_lista()

    def get_visible_products():
        local_db = SessionLocal(); query = local_db.query(Produto).options(joinedload(Produto.pasta))
        if current_view_context['value'] == 'compartilhados': query = query.filter(Produto.is_shared == True)
        elif current_view_context['value'] == 'pastas_detalhe' and active_folder_id['value'] is not None: query = query.filter(Produto.pasta_id == active_folder_id['value'])
        produtos = query.all(); local_db.close()
        term = busca_valor["value"].strip().lower()
        visible = [p for p in produtos if periodo_validade_boolean(p.data_validade or "") and (not term or term in (p.nome or "").lower() or term in (p.pasta.nome.lower() if p.pasta else ""))]
        order = sort_order['value']
        if order == 'name': visible.sort(key=lambda p: p.nome.lower())
        elif order == 'date':
            def get_date(p):
                try: return datetime.datetime.strptime(p.data_validade, "%d/%m/%Y").date()
                except (ValueError, TypeError): return datetime.date.max
            visible.sort(key=get_date)
        elif order == 'quantity': visible.sort(key=lambda p: p.quantidade)
        return visible

    def go_to_search(e):
        page.appbar.visible = False;
        page.bottom_appbar.visible = False
        page.floating_action_button.visible = False
        main_content.content = search_view
        filtro_dropdown.value = filtro_selecionado["value"]; page.update()
        
    def return_from_search(e):
        filtro_selecionado.update({"value": filtro_dropdown.value})
        voltar_para_meus_produtos()
        
    def show_pastas(e):
        current_view_context['value'] = 'pastas'
        active_folder_id['value'] = None
        main_content.content = pastas_view
        clear_selection()
        appbar.leading = None
        appbar.actions = [quick_count_button, ft.IconButton(icon=ft.Icons.CREATE_NEW_FOLDER, tooltip="Nova Pasta", icon_color=ft.Colors.WHITE, on_click=abrir_dialogo_criar_pasta)]
        appbar.title.value = "Coletor - Pastas"
        atualizar_pastas()
        page.update()

    def show_meus_produtos(e):
        current_view_context['value'] = 'meus_produtos'
        active_folder_id['value'] = None
        main_content.content = meus_produtos_view
        clear_selection()
        appbar.leading = None
        appbar.actions = [quick_count_button, sort_button, ft.IconButton(icon=ft.Icons.FILTER_LIST, tooltip="Filtro", icon_color=ft.Colors.WHITE, on_click=go_to_search)]
        header_text.value = "👤 Meus Produtos"
        appbar.title.value = "Coletor"
        atualizar_lista()
        page.update()
    
    def show_compartilhados(e):
        current_view_context['value'] = 'compartilhados'
        active_folder_id['value'] = None
        main_content.content = compartilhados_view
        clear_selection()
        appbar.leading = None
        appbar.actions = [quick_count_button, sort_button]
        appbar.title.value = "Produtos Compartilhados"
        atualizar_lista()
        page.update()

    def abrir_pasta(pasta: Pasta):
        current_view_context['value'] = 'pastas_detalhe'; active_folder_id['value'] = pasta.id
        main_content.content = meus_produtos_view
        clear_selection()
        appbar.leading = ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Voltar para Pastas", icon_color=ft.Colors.WHITE, on_click=show_pastas)
        header_text.value = f"📂 {pasta.nome}"
        appbar.actions = [quick_count_button, sort_button, ft.IconButton(icon=ft.Icons.ADD_CIRCLE, tooltip="Adicionar à Pasta", icon_color=ft.Colors.WHITE, on_click=lambda e: scanner_function(pasta_id_forced=pasta.id))]
        atualizar_lista()
        page.update()

    def toggle_quick_count_mode(e):
        quick_count_mode['value'] = not quick_count_mode['value']
        if quick_count_mode['value']:
            quick_count_button.icon_color = CORES["success"]; page.snack_bar = ft.SnackBar(ft.Text("Modo Contagem Rápida ATIVADO"))
        else:
            quick_count_button.icon_color = ft.Colors.WHITE; page.snack_bar = ft.SnackBar(ft.Text("Modo Contagem Rápida DESATIVADO"))
        page.snack_bar.open = True; page.update()
    
    quick_count_button = ft.IconButton(icon=ft.Icons.DATA_SAVER_ON_OUTLINED, icon_color=ft.Colors.WHITE, tooltip="Ativar Modo Contagem Rápida", on_click=toggle_quick_count_mode)
    sort_button = ft.PopupMenuButton(icon=ft.Icons.SORT, tooltip="Classificar", icon_color=ft.Colors.WHITE, items=[ft.PopupMenuItem(text="Padrão", on_click=lambda _: set_sort_order("default")), ft.PopupMenuItem(text="Ordem Alfabética (A-Z)", on_click=lambda _: set_sort_order("name")), ft.PopupMenuItem(text="Data de Validade", on_click=lambda _: set_sort_order("date")), ft.PopupMenuItem(text="Quantidade", on_click=lambda _: set_sort_order("quantity"))])
    def meus_produtos_header(): return ft.Row([header_text, ft.Row([ft.IconButton(icon=ft.Icons.SHARE, tooltip="Copiar lista", on_click=compartilhar_texto), ft.IconButton(icon=ft.Icons.DOWNLOAD, tooltip="Exportar xlsx", on_click=exportar_xlsx)], spacing=6)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    search_view = ft.Container(content=ft.Column([ft.Text("Período de Validade", size=20, weight=ft.FontWeight.BOLD), ft.Divider(), filtro_dropdown, ft.Container(height=20), ft.ElevatedButton("Aplicar Filtros e Voltar", icon=ft.Icons.CHECK, on_click=return_from_search)], expand=True), padding=12)
    meus_produtos_view = ft.Container(content=ft.Column([meus_produtos_header(), ft.Container(content=busca_field, padding=ft.padding.only(bottom=10)), prodList], expand=True), padding=12)
    pastas_view = ft.Container(content=ft.Column([ft.Text("📂 Pastas", size=22, weight=ft.FontWeight.BOLD), ft.Row([busca_pasta_field]), ft.Divider(), pastaList], expand=True), padding=12)
    compartilhados_view = ft.Container(content=ft.Column([ft.Row([ft.Text("👥 Compartilhados", size=22, weight=ft.FontWeight.BOLD), ft.Row([ft.IconButton(icon=ft.Icons.SHARE, tooltip="Copiar lista", on_click=compartilhar_texto), ft.IconButton(icon=ft.Icons.DOWNLOAD, tooltip="Exportar xlsx", on_click=exportar_xlsx)], spacing=6)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Text("Produtos marcados para compartilhar.", color=CORES["subtitle"]), ft.Divider(), prodList], spacing=10), padding=12)
    
    main_content = ft.AnimatedSwitcher(
        meus_produtos_view,
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=50,
        reverse_duration=100
    )
    
    appbar = ft.AppBar(title=ft.Text("Coletor"), bgcolor=CORES["primary"], center_title=True)
    page.appbar = appbar
    
    action_bar_products = ft.BottomAppBar(bgcolor=ft.Colors.BLUE_GREY_100, shape=ft.NotchShape.AUTO, visible=False, content=ft.Row([ft.Text("Selecionados: 0", weight=ft.FontWeight.BOLD), ft.Container(width=10), ft.IconButton(icon=ft.Icons.FOLDER_SHARED, tooltip="Mover", on_click=open_move_dialog), ft.IconButton(icon=ft.Icons.IOS_SHARE, tooltip="Compartilhar", icon_color=CORES["success"], on_click=share_selected_products), ft.IconButton(icon=ft.Icons.DOWNLOAD, tooltip="Exportar", on_click=exportar_xlsx), ft.IconButton(icon=ft.Icons.DELETE, tooltip="Deletar", icon_color=CORES["danger"], on_click=delete_selected_products), ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Limpar", on_click=clear_selection)], alignment=ft.MainAxisAlignment.START, spacing=10))
    action_bar_folders = ft.BottomAppBar(bgcolor=ft.Colors.BLUE_GREY_100, shape=ft.NotchShape.AUTO, visible=False, content=ft.Row([ft.Text("Selecionados: 0", weight=ft.FontWeight.BOLD), ft.Container(width=10), ft.IconButton(icon=ft.Icons.DOWNLOAD, tooltip="Exportar", on_click=exportar_xlsx), ft.IconButton(icon=ft.Icons.SHARE, tooltip="Compartilhar", on_click=compartilhar_texto), ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Limpar", on_click=clear_selection)], alignment=ft.MainAxisAlignment.START, spacing=10))
    
    page.add(action_bar_products, action_bar_folders)
    
    page.bottom_appbar = ft.BottomAppBar(bgcolor=CORES["primary"], shape=ft.NotchShape.CIRCULAR, content=ft.Row([ft.IconButton(icon=ft.Icons.FOLDER, icon_color=ft.Colors.WHITE, on_click=show_pastas), ft.Container(width=40), ft.IconButton(icon=ft.Icons.LIST, icon_color=ft.Colors.WHITE, on_click=show_meus_produtos), ft.IconButton(icon=ft.Icons.GROUP, icon_color=ft.Colors.WHITE, on_click=show_compartilhados)], alignment=ft.MainAxisAlignment.SPACE_AROUND))
    
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.CAMERA_ALT, bgcolor=CORES["danger"], foreground_color=ft.Colors.WHITE,
        on_click=lambda e: scanner_function(), # Chama a função correta para a plataforma
        shape=ft.CircleBorder()
    )
    page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_DOCKED
    
    page.add(main_content)
    show_meus_produtos(None)

# =========================================================
# === NOVO PONTO DE ENTRADA ASGI PARA UVICORN (FINAL) ===
# =========================================================

# Esta função é o que o Uvicorn (ASGI) vai buscar (app.main:asgi_app)
# Ela retorna o aplicativo Flet, passando 'main' como target.
asgi_app = ft.app(
    target=main, 
    # view=None,  <-- REMOVA ESTA LINHA
    assets_dir="assets"
)
