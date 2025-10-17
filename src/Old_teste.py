# teste.py
import flet as ft
import datetime
import csv
import os
from models import Produto, Pasta, SessionLocal, init_db

# --------- Paleta de cores / constantes ----------
CORES = {
    "background": "#F5F6FA",
    "primary": "#0A2E73",
    "danger": "#D9043D",
    "success": "#28A745",
    "title": "#1A237E",
    "subtitle": "#444444",
}

# --------- Helper: placeholder para futura API ----------
def buscar_produto_na_api(tipo: str, valor: str):
    """
    PLACEHOLDER: aqui você integrará chamadas externas para preencher
    automaticamente Nome, imagem, validade etc. por EAN/PLU.
    Atualmente retorna None (sem auto-preenchimento).
    """
    # Exemplo futuro:
    # if tipo == "EAN": call external API...
    return None

# --------- App principal ----------
def main(page: ft.Page):
    page.title = "Coletor de Conferência"
    page.window.height = 800
    page.window.width = 400
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = CORES["background"]

    # inicia (cria tabelas se necessário)
    init_db()
    db = SessionLocal()

    # Controle de UI
    prodList = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)
    pastaList = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)

    # NOVO: Estado para controlar a visibilidade da barra de busca/filtro
    show_search_and_filter = {"value": False} 
    
    # Valores de filtro atualizados
    # valores: "Todos","Próximos 7 dias","Vencem este Mês","Vencem este Ano", "Vencidos"
    filtro_selecionado = {"value": "Todos"} 
    busca_valor = {"value": ""}
    busca_pasta_valor = {"value": ""} 

    hoje_date = datetime.date.today()
    hoje_str = hoje_date.strftime("%d/%m/%Y")
    
    # ---------- Funções de controle de estado ----------
    def toggle_search(e):
        # 1. Alterna o estado de visibilidade
        show_search_and_filter["value"] = not show_search_and_filter["value"]
        
        # 2. Limpa a busca e filtro ao esconder
        if not show_search_and_filter["value"]:
            busca_valor["value"] = ""
            busca_field.value = ""
            busca_pasta_valor["value"] = "" 
            busca_pasta_field.value = "" 
            filtro_selecionado["value"] = "Todos"
            filtro_dropdown.value = "Todos"
        
        # 3. Oculta/Exibe o teclado (apenas uma sugestão visual)
        page.keyboard_visibility = show_search_and_filter["value"]
            
        # 4. Chama a função de atualização da lista ativa
        if main_stack.controls[0] == meus_produtos_view:
            atualizar_lista()
        elif main_stack.controls[0] == pastas_view:
            atualizar_pastas()
            
        # 5. Garante que a UI é redesenhada
        page.update()
        
    # ---------- Funções de Snackbar (Para o Botão EDITAR e MOVER) ----------
    def mostrar_snack_em_implementacao(e):
        # FUNÇÃO AUXILIAR para ações futuras (Editar, Mover)
        page.snack_bar = ft.SnackBar(ft.Text("Funcionalidade em desenvolvimento"))
        page.snack_bar.open = True
        page.update()

    # ---------- Funções de validade / filtro ----------
    def cor_validade(data_str: str):
        try:
            data = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            delta = (data - hoje_date).days
            if delta < 0:
                return CORES["danger"]
            elif delta <= 7:
                return "#FFC107"  # amarelo
            else:
                return CORES["success"]
        except:
            return CORES["subtitle"]

    def periodo_validade_boolean(data_str: str):
        """
        Retorna True se o produto com data_str deve aparecer
        segundo o filtro atual em filtro_selecionado["value"].
        """
        try:
            data = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            delta = (data - hoje_date).days

            if filtro_selecionado["value"] == "Próximos 7 dias":
                return 0 <= delta <= 7
            elif filtro_selecionado["value"] == "Vencem este Mês":
                # Vence neste mês E ainda não venceu (delta >= 0)
                return data.year == hoje_date.year and data.month == hoje_date.month and delta >= 0
            elif filtro_selecionado["value"] == "Vencem este Ano":
                # Vence neste ano E ainda não venceu (delta >= 0)
                return data.year == hoje_date.year and delta >= 0
            elif filtro_selecionado["value"] == "Vencidos":
                # Venceu no passado
                return delta < 0
            elif filtro_selecionado["value"] == "Todos":
                return True
            else:
                return True
        except:
            # se data inválida:
            return filtro_selecionado["value"] == "Todos"


    # ---------- Funções de DB / UI ----------
    def criar_card(produto: Produto):
        cor = cor_validade(produto.data_validade or "")
        return ft.Card(
            elevation=2,
            color=ft.Colors.WHITE,
            content=ft.Container(
                padding=10,
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.SHOPPING_BASKET, size=40, color=CORES["primary"]),
                        ft.Column(
                            [
                                ft.Text(produto.nome, weight=ft.FontWeight.BOLD, size=14, color=CORES["title"]),
                                ft.Text(f"Validade: {produto.data_validade or 'N/A'}", size=12, color=cor),
                                ft.Text(f"Qtd: {produto.quantidade}", size=12, color=CORES["subtitle"]),
                                # Mostra a pasta do produto se existir
                                ft.Text(f"Pasta: {produto.pasta.nome if produto.pasta else 'N/A'}", size=10, color=CORES["primary"] if produto.pasta else ft.Colors.GREY_500),
                            ],
                            expand=True,
                        ),
                        # Menu Pop-up para opções de Editar/Deletar/Mover
                        ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(
                                    text="Editar (breve)",
                                    icon=ft.Icons.EDIT,
                                    on_click=mostrar_snack_em_implementacao
                                ),
                                ft.PopupMenuItem(
                                    text="Mover para Pasta",
                                    icon=ft.Icons.FOLDER_SHARED,
                                    on_click=mostrar_snack_em_implementacao 
                                ),
                                ft.PopupMenuItem(
                                    text="Deletar Produto",
                                    # Usar um Row com ft.Icon no atributo 'content'
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.DELETE, color=CORES["danger"]), # Ícone com cor
                                        ft.Text("Deletar Produto"), # Texto
                                    ], spacing=10),
                                    # Chamar a função deletar_produto com o EAN/PLU
                                    on_click=lambda e, c=produto.ean: deletar_produto(c)
                                ),
                            ],
                            # Ícone que abre o menu
                            icon=ft.Icons.MORE_VERT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            ),
        )

    def atualizar_lista():
        prodList.controls.clear()
        produtos = db.query(Produto).all()
        term = busca_valor["value"].strip().lower()
        
        for p in produtos:
            # Pega o nome da pasta, se existir, e converte para minúsculas
            pasta_nome = p.pasta.nome.lower() if p.pasta else ""
            
            # aplica filtro por validez (periodo) E (busca por nome do produto OU nome da pasta)
            if periodo_validade_boolean(p.data_validade or ""):
                # Lógica de busca combinada
                if not term or term in (p.nome or "").lower() or term in pasta_nome:
                    prodList.controls.append(criar_card(p))
        page.update()

    def deletar_produto(codigo):
        # procura por EAN ou PLU (prioriza EAN)
        produto = None
        if codigo:
            produto = db.query(Produto).filter(Produto.ean == codigo).first()
            if not produto:
                produto = db.query(Produto).filter(Produto.plu == codigo).first()
        if produto:
            db.delete(produto)
            db.commit()
            atualizar_lista()
            page.snack_bar = ft.SnackBar(ft.Text("Produto deletado"))
            page.snack_bar.open = True
            page.update()

    # ---------- Pastas: CRUD simples ----------
    def carregar_pastas_options():
        return [ft.dropdown.Option(str(p.id), p.nome) for p in db.query(Pasta).all()]
    def abrir_pasta(pasta: Pasta):
        produtos = db.query(Produto).filter(Produto.pasta_id == pasta.id).all()

        lista = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)
        for p in produtos:
            lista.controls.append(criar_card(p))

        conteudo = ft.Container(
            content=ft.Column([
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            tooltip="Voltar",
                            on_click=lambda e: show_pastas(e),
                        ),
                        ft.Text(f"📂 {pasta.nome}", size=22, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Divider(),
                lista if produtos else ft.Text("Nenhum produto nesta pasta."),
            ], spacing=10, expand=True),
            padding=15,
        )

        main_stack.controls.clear()
        main_stack.controls.append(conteudo)

    # FAB agora serve para adicionar produto na pasta
        page.floating_action_button.tooltip = f"Adicionar em {pasta.nome}"
        page.floating_action_button.on_click = lambda _: abrir_codigo_dialog(pasta.id)

        page.update()
    def criar_card_pasta(pasta_obj, count):
        # cartão clicável que abre a pasta
        return ft.Card(
            elevation=1,
            content=ft.Container(
                padding=8,
                on_click=lambda e, p=pasta_obj: abrir_pasta(p),
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.FOLDER, size=36, color=CORES["primary"]),
                        ft.Column([ft.Text(pasta_obj.nome, weight=ft.FontWeight.BOLD), ft.Text(f"{count} produtos", size=11)], expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=CORES["danger"], on_click=lambda e, pid=pasta_obj.id: deletar_pasta(pid)),
                    ],
                ),
            ),
        )

    def atualizar_pastas():
        pastaList.controls.clear()
        pastas = db.query(Pasta).all()
        term = busca_pasta_valor["value"].strip().lower() 
        
        for p in pastas:
            # Filtra pastas por nome
            if not term or term in p.nome.lower():
                cnt = db.query(Produto).filter(Produto.pasta_id == p.id).count()
                pastaList.controls.append(criar_card_pasta(p, cnt))
        page.update()

    def deletar_pasta(pasta_id):
        p = db.query(Pasta).filter(Pasta.id == pasta_id).first()
        if not p:
            return
        cnt = db.query(Produto).filter(Produto.pasta_id == p.id).count()
        if cnt > 0:
            dlg = ft.AlertDialog(title=ft.Text("Erro"), content=ft.Text("Não é possível excluir pasta com produtos."), actions=[ft.TextButton("OK", on_click=lambda _: page.close(dlg))])
            page.open(dlg)
            return
        db.delete(p)
        db.commit()
        atualizar_pastas()
        page.snack_bar = ft.SnackBar(ft.Text("Pasta excluída"))
        page.snack_bar.open = True
        page.update()

    # ---------- Formulário de Produto ----------
    # máscaras/validações leves
    def only_digits_max(e, max_len):
        v = "".join(filter(str.isdigit, e.control.value))
        if len(v) > max_len:
            v = v[:max_len]
        e.control.value = v
        page.update()

    ean_field = ft.TextField(label="EAN (13 dígitos)", width=300, on_change=lambda e: only_digits_max(e, 13))
    plu_field = ft.TextField(label="PLU (5 dígitos)", width=300, on_change=lambda e: only_digits_max(e, 5))
    nome_field = ft.TextField(label="Nome do Produto", width=300)
    qtd_field = ft.TextField(label="Quantidade", width=300, on_change=lambda e: only_digits_max(e, 6))
    pasta_dropdown = ft.Dropdown(label="Pasta (opcional)", options=[], width=300)
    validade_field = ft.TextField(label="Data de Validade (dd/mm/yyyy)", width=300, value=hoje_str)

    def salvar_produto(e):
        ean = ean_field.value.strip()
        plu = plu_field.value.strip()
        nome = nome_field.value.strip()
        qtd = int(qtd_field.value.strip() or "0")
        validade = validade_field.value.strip()
        pasta_id = int(pasta_dropdown.value) if pasta_dropdown.value else None

        # Validações básicas
        if not ean and not plu:
            msg = "Informe EAN (13) ou PLU (5)."
        elif ean and len(ean) != 13:
            msg = "EAN deve ter 13 dígitos."
        elif plu and len(plu) != 5:
            msg = "PLU deve ter 5 dígitos."
        elif not nome:
            msg = "Nome obrigatório."
        else:
            msg = None

        if msg:
            d = ft.AlertDialog(title=ft.Text("Erro"), content=ft.Text(msg), actions=[ft.TextButton("OK", on_click=lambda _: page.close(d))])
            page.open(d)
            return

        novo = Produto(ean=ean or None, plu=plu or None, nome=nome, quantidade=qtd, data_validade=validade, pasta_id=pasta_id)
        db.add(novo)
        db.commit()
        page.snack_bar = ft.SnackBar(ft.Text("Produto salvo"))
        page.snack_bar.open = True
        page.update()
        voltar_para_meus_produtos()

    form_container = ft.Container(
        expand=True,
        padding=16,
        content=ft.Column(
            [
                ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: voltar_para_meus_produtos()), ft.Text("Adicionar Produto", size=20, weight=ft.FontWeight.BOLD)]),
                ean_field,
                plu_field,
                nome_field,
                qtd_field,
                validade_field,
                pasta_dropdown,
                ft.Row([ft.ElevatedButton("Salvar", on_click=salvar_produto), ft.TextButton("Cancelar", on_click=lambda e: voltar_para_meus_produtos())]),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    # ---------- Fluxo do FAB / coletor de código ----------
    codigo_temp = {"tipo": None, "valor": None}  # apenas se precisar

    def validar_codigo_dialog(e):
        only_digits_max(e, 13)

    codigo_field = ft.TextField(label="Digite o código (EAN 13 ou PLU 5)", width=260, on_change=validar_codigo_dialog, max_length=13)

    def criar_novo_registro(tipo, valor, pasta_id_forced=None):
        # atualiza opções de pastas antes
        pasta_dropdown.options = carregar_pastas_options()
        if pasta_id_forced:
            pasta_dropdown.value = str(pasta_id_forced)
        else:
            pasta_dropdown.value = None

        if tipo == "EAN":
            ean_field.value = valor
            plu_field.value = ""
        else:
            plu_field.value = valor
            ean_field.value = ""
        nome_field.value = ""
        qtd_field.value = ""
        validade_field.value = hoje_str

        # tentar autocompletar via API externa (placeholder)
        api_data = buscar_produto_na_api(tipo, valor)
        if api_data:
            # ex: api_data = {"nome": "...", "validade":"dd/mm/yyyy", "quantidade": N}
            nome_field.value = api_data.get("nome", nome_field.value)
            validade_field.value = api_data.get("validade", validade_field.value)
            qtd_field.value = str(api_data.get("quantidade", qtd_field.value))

        main_stack.controls.clear()
        main_stack.controls.append(form_container)
        page.update()

    def confirmar_codigo(e):
        valor = codigo_field.value.strip()
        if valor.isdigit() and len(valor) == 13:
            tipo = "EAN"
        elif valor.isdigit() and len(valor) == 5:
            tipo = "PLU"
        else:
            dlg = ft.AlertDialog(title=ft.Text("Erro"), content=ft.Text("Código deve ser EAN(13) ou PLU(5)"), actions=[ft.TextButton("OK", on_click=lambda _: page.close(dlg))])
            page.open(dlg)
            return

        # busca produto existente por EAN ou PLU
        produto_existente = None
        if tipo == "EAN":
            produto_existente = db.query(Produto).filter(Produto.ean == valor).first()
        else:
            produto_existente = db.query(Produto).filter(Produto.plu == valor).first()

        if produto_existente:
            # abre diálogo para somar quantidade OU adicionar novo
            qtd_field_dialog = ft.TextField(label="Quantidade a somar", width=150, on_change=lambda ev: only_digits_max(ev, 6))
            def confirmar_soma(ev):
                try:
                    qtd = int(qtd_field_dialog.value or "0")
                    if qtd > 0:
                        produto_existente.quantidade += qtd
                        db.commit()
                        atualizar_lista()
                        page.close(dialogo_existente)
                        page.snack_bar = ft.SnackBar(ft.Text(f"Somado {qtd} ao produto"))
                        page.snack_bar.open = True
                        page.update()
                except ValueError:
                    err = ft.AlertDialog(title=ft.Text("Erro"), content=ft.Text("Quantidade inválida"), actions=[ft.TextButton("OK", on_click=lambda _: page.close(err))])
                    page.open(err)

            def criar_novo_ev(ev):
                page.close(dialogo_existente)
                # abre formulário com pasta se dialog veio de uma pasta (uso codigo_field.data)
                criar_novo_registro(tipo, valor, getattr(codigo_field, "data", None))

            dialogo_existente = ft.AlertDialog(
                modal=True,
                title=ft.Text("Produto já cadastrado"),
                content=ft.Column([ft.Text(f"Código {valor} já existe."), ft.Text(f"Quantidade atual: {produto_existente.quantidade}"), qtd_field_dialog], tight=True),
                actions=[ft.TextButton("Somar", on_click=confirmar_soma), ft.TextButton("Adicionar novo", on_click=criar_novo_ev), ft.TextButton("Cancelar", on_click=lambda _: page.close(dialogo_existente))],
            )
            page.open(dialogo_existente)
        else:
            # novo -> fecha dialog e abre form preenchido
            page.close(codigo_dialog)
            criar_novo_registro(tipo, valor, getattr(codigo_field, "data", None))

    codigo_dialog = ft.AlertDialog(modal=True, title=ft.Text("Novo Produto"), content=codigo_field, actions=[ft.TextButton("Confirmar", on_click=confirmar_codigo), ft.TextButton("Cancelar", on_click=lambda _: page.close(codigo_dialog))])

    def abrir_codigo_dialog(pasta_id=None):
        codigo_field.value = ""
        # armazena a pasta de onde veio (se houver) para pré-seleção
        codigo_field.data = pasta_id
        page.open(codigo_dialog)

    # ---------- Views: Pastas / Meus Produtos / Compartilhados ----------
    
    # Filtro com opções semânticas
    filtro_dropdown = ft.Dropdown(
        value="Todos",
        options=[
            ft.dropdown.Option("Todos"),
            ft.dropdown.Option("Próximos 7 dias"), 
            ft.dropdown.Option("Vencem este Mês"), 
            ft.dropdown.Option("Vencem este Ano"), 
            ft.dropdown.Option("Vencidos"),
        ],
        on_change=lambda e: (filtro_selecionado.update({"value": e.control.value}), atualizar_lista()),
        width=160,
        label="Filtro", # Adicionado label para clareza
    )

    # Campo de busca para produtos (Meus Produtos)
    busca_field = ft.TextField(
        hint_text="Buscar produto por nome ou pasta...", 
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda e: (busca_valor.update({"value": e.control.value}), atualizar_lista()),
        expand=True, 
        on_submit=lambda e: page.keyboard_visibility(False), 
    )

    # NOVO: Campo de busca para pastas (Pastas)
    busca_pasta_field = ft.TextField(
        hint_text="Buscar pasta por nome...", 
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda e: (busca_pasta_valor.update({"value": e.control.value}), atualizar_pastas()),
        expand=True,
        on_submit=lambda e: page.keyboard_visibility(False),
    )

    # ações extras na view "Meus Produtos": compartilhar e exportar
    def get_visible_products():
        """Retorna lista de objetos Produto visíveis atualmente segundo filtro + busca."""
        produtos = db.query(Produto).all()
        term = busca_valor["value"].strip().lower()
        visible = []
        for p in produtos:
            # Pega o nome da pasta, se existir, e converte para minúsculas
            pasta_nome = p.pasta.nome.lower() if p.pasta else ""
            
            if periodo_validade_boolean(p.data_validade or ""):
                # Lógica de busca combinada
                if not term or term in (p.nome or "").lower() or term in pasta_nome:
                    visible.append(p)
        return visible

    def compartilhar_texto(ev):
        items = get_visible_products()
        if not items:
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum produto visível para compartilhar"))
            page.snack_bar.open = True
            page.update()
            return
        lines = ["--- Lista de Produtos (Filtro Atual) ---"]
        for p in items:
            lines.append(f"{p.nome} — Qtd: {p.quantidade} — Validade: {p.data_validade or 'N/A'}")
        text = "\n".join(lines)
        page.set_clipboard(text)
        page.snack_bar = ft.SnackBar(ft.Text("Lista copiada para área de transferência"))
        page.snack_bar.open = True
        page.update()

    def exportar_csv(ev):
        items = get_visible_products()
        if not items:
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum produto para exportar"))
            page.snack_bar.open = True
            page.update()
            return
        # monta CSV
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"produtos_export_{timestamp}.csv"
        # salva no diretório atual
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["EAN", "PLU", "Nome", "Quantidade", "Validade", "Pasta"])
                for p in items:
                    pasta_nome = ""
                    if p.pasta_id:
                        pasta_obj = db.query(Pasta).filter(Pasta.id == p.pasta_id).first()
                        pasta_nome = pasta_obj.nome if pasta_obj else ""
                    writer.writerow([p.ean or "", p.plu or "", p.nome or "", p.quantidade, p.data_validade or "", pasta_nome])
            page.snack_bar = ft.SnackBar(ft.Text(f"CSV salvo: {os.path.abspath(filename)}"))
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar CSV: {e}"))
            page.snack_bar.open = True
            page.update()

    # Header / title row for "Meus Produtos" with share & download icons
    def meus_produtos_header():
        return ft.Row(
            [
                ft.Text("👤 Meus Produtos", size=22, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.IconButton(icon=ft.Icons.SHARE, tooltip="Copiar lista visível", on_click=compartilhar_texto),
                        ft.IconButton(icon=ft.Icons.DOWNLOAD, tooltip="Exportar CSV (visível)", on_click=exportar_csv),
                    ],
                    spacing=6,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    # Views
    # PASTAS VIEW - Com busca condicional
    pastas_view = ft.Container(
        content=ft.Column(
            [
                ft.Text("📂 Pastas", size=22, weight=ft.FontWeight.BOLD),
                # Container que mostra o campo de busca APENAS se a lupa na AppBar for clicada
                ft.Column(
                    [
                        ft.Row([busca_pasta_field]), 
                        ft.Divider(height=1, thickness=1),
                    ],
                    # Usa o estado para controlar a visibilidade
                    visible=show_search_and_filter["value"], 
                ),
                pastaList
            ],
            expand=True
        ), 
        padding=12
    )

    
    # MEUS PRODUTOS VIEW - Com busca e filtro condicionais
    meus_produtos_view = ft.Container(
        content=ft.Column(
            [
                meus_produtos_header(),
                # Container que mostra o campo de busca e o filtro APENAS se a lupa na AppBar for clicada
                ft.Column(
                    [
                        ft.Row([busca_field]), # Busca na primeira linha
                        ft.Row(
                            [
                                ft.Text("Filtrar por validade:", size=12, weight=ft.FontWeight.BOLD),
                                filtro_dropdown # Filtro na segunda linha
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ), 
                        ft.Divider(height=1, thickness=1),
                    ],
                    # Usa o estado para controlar a visibilidade
                    visible=show_search_and_filter["value"], 
                ),
                prodList,
            ],
            expand=True,
        ),
        padding=12,
    )
    
    compartilhados_view = ft.Container(content=ft.Column([ft.Text("👥 Compartilhados", size=22, weight=ft.FontWeight.BOLD), ft.Text("Somente leitura (implementação futura)")], spacing=10), padding=12)

    main_stack = ft.Stack([meus_produtos_view])

    def voltar_para_meus_produtos():
        # recarrega opções de pasta
        pasta_dropdown.options = carregar_pastas_options()
        main_stack.controls.clear()
        main_stack.controls.append(meus_produtos_view)
        atualizar_lista()
        page.update()

    # ---------- Criação de pasta via FAB ----------
    nova_pasta_field = ft.TextField(label="Nome da pasta", width=260)
    def confirmar_criar_pasta(e):
        n = nova_pasta_field.value.strip()
        if not n:
            d = ft.AlertDialog(title=ft.Text("Erro"), content=ft.Text("Nome não pode ser vazio"), actions=[ft.TextButton("OK", on_click=lambda _: page.close(d))])
            page.open(d)
            return
        db.add(Pasta(nome=n))
        db.commit()
        page.close(nova_pasta_dialog)
        atualizar_pastas()
        page.snack_bar = ft.SnackBar(ft.Text("Pasta criada"))
        page.snack_bar.open = True
        page.update()

    nova_pasta_dialog = ft.AlertDialog(modal=True, title=ft.Text("Nova Pasta"), content=nova_pasta_field, actions=[ft.TextButton("Cancelar", on_click=lambda _: page.close(nova_pasta_dialog)), ft.TextButton("Criar", on_click=confirmar_criar_pasta)])

    def abrir_criar_pasta(e):
        nova_pasta_field.value = ""
        page.open(nova_pasta_dialog)

    # FUNÇÃO DE SNACKBAR CORRIGIDA
    def mostrar_snack_compartilhados(e):
        page.snack_bar = ft.SnackBar(ft.Text("Apenas leitura"))
        page.snack_bar.open = True
        page.update()

    # ---------- Navegação e BottomAppBar ----------
    def show_pastas(e):
        main_stack.controls.clear()
        main_stack.controls.append(pastas_view)
        page.floating_action_button.tooltip = "Criar Pasta"
        page.floating_action_button.on_click = abrir_criar_pasta
        atualizar_pastas()
        page.update()

    def show_meus_produtos(e):
        main_stack.controls.clear()
        main_stack.controls.append(meus_produtos_view)
        page.floating_action_button.tooltip = "Novo Produto"
        # FAB abre diálogo de código para coletor / leitor (função principal)
        page.floating_action_button.on_click = lambda ev: abrir_codigo_dialog(None)
        atualizar_lista()
        page.update()

    def show_compartilhados(e):
        main_stack.controls.clear()
        main_stack.controls.append(compartilhados_view)
        page.floating_action_button.tooltip = "Somente leitura"
        # Chamada corrigida
        page.floating_action_button.on_click = mostrar_snack_compartilhados
        page.update()

    page.bottom_appbar = ft.BottomAppBar(
        bgcolor=CORES["primary"],
        shape=ft.NotchShape.CIRCULAR,
        content=ft.Row(
            [ft.IconButton(icon=ft.Icons.FOLDER, on_click=show_pastas, icon_color=ft.Colors.WHITE),
             ft.Container(width=40),
             ft.IconButton(icon=ft.Icons.LIST, on_click=show_meus_produtos, icon_color=ft.Colors.WHITE),
             ft.IconButton(icon=ft.Icons.GROUP, on_click=show_compartilhados, icon_color=ft.Colors.WHITE)],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
    )

    # ---------- AppBar com pesquisa e input manual ----------
    page.appbar = ft.AppBar(
        title=ft.Text("Coletor - Inventário", color="white"),
        bgcolor=CORES["primary"],
        center_title=True,
        actions=[
            # AÇÃO CORRIGIDA: Lupa que ativa/desativa a busca e o filtro
            ft.IconButton(icon=ft.Icons.SEARCH, tooltip="Buscar e Filtrar", icon_color="white", on_click=lambda e: toggle_search(e)),
            # Botão de input manual (teclado)
            ft.IconButton(icon=ft.Icons.KEYBOARD, tooltip="Digitar código manualmente", icon_color="white", on_click=lambda e: abrir_codigo_dialog(None)),
        ],
    )

    # ---------- FAB ----------
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        bgcolor=CORES["danger"],
        foreground_color=ft.Colors.WHITE,
        shape=ft.CircleBorder(),
        tooltip="Adicionar",
        on_click=lambda ev: abrir_codigo_dialog(None),
    )
    page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_DOCKED

    # ---------- Inicialização ----------
    page.add(main_stack)
    show_meus_produtos(None) 
    
if __name__ == "__main__":
    ft.app(target=main)