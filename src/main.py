import flet as ft
from flet_webview import WebView
import datetime

# --- App colors and constants ---
CORES = {
    "background": "#F1F0FB",
    "primary": "#0A2E73",
    "danger": "#E2002E",
    "success": "#28A745",
    "title": "#1A2E73",
    "subtitle": "#444444",
}

# --- In-memory data storage ---
produtos = []
pastas = []
shared_produtos = set()

# --- Helpers ---
def cor_validade(data_str: str):
    try:
        data = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
        delta = (data - datetime.date.today()).days
        if delta < 0:
            return CORES["danger"]
        elif delta <= 7:
            return "#FFC107"
        return CORES["success"]
    except:
        return CORES["subtitle"]


def main(page: ft.Page):
    page.title = "Coletor de Conferência (Web)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = CORES["background"]

    # --- UI state ---
    current_view = {"value": "meus_produtos"}
    selected_products = set()

    # --- Product list container ---
    prodList = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)
    header_text = ft.Text("👤 Meus Produtos", size=22, weight=ft.FontWeight.BOLD)

    # --- Scanner using your scanner.html ---
    def show_web_scanner(e=None):
        def handle_message(ev):
            code = ev.data
            if code == "CAMERA_ERROR":
                page.snack_bar = ft.SnackBar(ft.Text("Erro ao acessar a câmera."), bgcolor=CORES["danger"])
            elif code:
                page.snack_bar = ft.SnackBar(ft.Text(f"Código lido: {code}"), bgcolor=CORES["success"])
                ean_field.value = code
                page.update()
            page.snack_bar.open = True
            voltar_meus_produtos()

        webview_control = WebView(url="/scanner.html")
        webview_control.on_message = handle_message

        scanner_view = ft.Container(
            expand=True,
            content=ft.Column(
                [
                    ft.Container(
                        bgcolor=CORES["primary"],
                        height=50,
                        content=ft.Row(
                            [
                                ft.IconButton(
                                    ft.Icons.ARROW_BACK,
                                    icon_color=ft.Colors.WHITE,
                                    on_click=lambda e: voltar_meus_produtos(),
                                ),
                                ft.Text("Aponte para o Código", color=ft.Colors.WHITE, size=20),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ),
                    webview_control,
                ],
                spacing=0,
            ),
        )

        main_content.content = scanner_view
        page.update()

    # --- Create / edit form ---
    ean_field = ft.TextField(label="EAN (13 dígitos)", width=300)
    nome_field = ft.TextField(label="Nome do Produto", width=300)
    qtd_field = ft.TextField(label="Quantidade", width=300)
    validade_field = ft.TextField(
        label="Data de Validade",
        width=300,
        value=datetime.date.today().strftime("%d/%m/%Y"),
    )

    def salvar_produto(e):
        produto = {
            "ean": ean_field.value.strip(),
            "nome": nome_field.value.strip(),
            "quantidade": qtd_field.value.strip() or "0",
            "data_validade": validade_field.value.strip(),
        }
        if not produto["nome"]:
            page.snack_bar = ft.SnackBar(ft.Text("Nome é obrigatório."), bgcolor=CORES["danger"])
            page.snack_bar.open = True
            return
        produtos.append(produto)
        page.snack_bar = ft.SnackBar(ft.Text("Produto salvo!"), bgcolor=CORES["success"])
        page.snack_bar.open = True
        voltar_meus_produtos()

    form_container = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: voltar_meus_produtos()),
                        ft.Text("Adicionar Produto", size=20, weight=ft.FontWeight.BOLD),
                    ]
                ),
                ean_field,
                nome_field,
                qtd_field,
                validade_field,
                ft.Row(
                    [
                        ft.ElevatedButton("Salvar", on_click=salvar_produto),
                        ft.TextButton("Cancelar", on_click=lambda e: voltar_meus_produtos()),
                    ]
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        expand=True,
        padding=16,
    )

    # --- Functions ---
    def voltar_meus_produtos():
        main_content.content = meus_produtos_view
        atualizar_lista()
        page.update()

    def criar_card(prod):
        cor = cor_validade(prod["data_validade"])
        return ft.Card(
            elevation=2,
            content=ft.Container(
                padding=10,
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.SHOPPING_BASKET, size=40, color=CORES["primary"]),
                        ft.Column(
                            [
                                ft.Text(prod["nome"], weight=ft.FontWeight.BOLD, size=14, color=CORES["title"]),
                                ft.Text(f"Validade: {prod['data_validade']}", size=12, color=cor),
                                ft.Text(f"Qtd: {prod['quantidade']}", size=12, color=CORES["subtitle"]),
                            ],
                            expand=True,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ),
        )

    def atualizar_lista():
        prodList.controls.clear()
        if not produtos:
            prodList.controls.append(
                ft.Text("Nenhum produto cadastrado.", color=CORES["subtitle"], text_align=ft.TextAlign.CENTER)
            )
        else:
            for p in produtos:
                prodList.controls.append(criar_card(p))
        page.update()

    def adicionar_produto(e):
        main_content.content = form_container
        page.update()

    def exportar_xlsx(ev):
        page.snack_bar = ft.SnackBar(ft.Text("Exportar XLSX não disponível no modo web."), bgcolor=CORES["danger"])
        page.snack_bar.open = True
        page.update()

    # --- Main views ---
    meus_produtos_header = ft.Row(
        [
            header_text,
            ft.Row(
                [
                    ft.IconButton(icon=ft.Icons.DOWNLOAD, tooltip="Exportar XLSX", on_click=exportar_xlsx),
                ],
                spacing=6,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    meus_produtos_view = ft.Container(
        content=ft.Column(
            [
                meus_produtos_header,
                ft.Container(content=prodList, padding=ft.padding.only(top=10)),
            ],
            expand=True,
        ),
        padding=12,
    )

    main_content = ft.AnimatedSwitcher(
        meus_produtos_view,
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=50,
        reverse_duration=100,
    )

    # --- AppBar & Navigation ---
    appbar = ft.AppBar(title=ft.Text("Coletor de Conferência"), bgcolor=CORES["primary"], center_title=True)
    page.appbar = appbar

    page.bottom_appbar = ft.BottomAppBar(
        bgcolor=CORES["primary"],
        shape=ft.NotchShape.CIRCULAR,
        content=ft.Row(
            [
                ft.IconButton(icon=ft.Icons.LIST, icon_color=ft.Colors.WHITE, on_click=lambda e: voltar_meus_produtos()),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
    )

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.CAMERA_ALT,
        bgcolor=CORES["danger"],
        foreground_color=ft.Colors.WHITE,
        on_click=show_web_scanner,
        tooltip="Abrir Leitor de Código",
    )

    page.add(main_content)
    atualizar_lista()


# Run app
if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
