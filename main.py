#Python 3.12.9

import sys
import os

# =====================================================================
# BLINDAGEM DE ESCOPO: Garante que o Python encontre a raiz 'src' e os submódulos
# =====================================================================
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
if diretorio_atual not in sys.path:
    sys.path.append(diretorio_atual)

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from PIL import Image

# =====================================================================
# 1. IMPORTS DA NOVA ARQUITETURA (DDD)
# =====================================================================
try:
    from src.core.auth.view import LoginView
    from src.core.auth.service import AuthService
    from src.core.historico.view import renderizar as renderizar_historico
    from src.painel_geral.dashboard.view import renderizar as renderizar_dashboard_geral
    
    from src.modulos.ponto_parada.dashboard.view import renderizar as renderizar_dashboard_pp
    from src.modulos.ponto_parada.ordem_servico.view import renderizar as renderizar_os_pp
    from src.modulos.ponto_parada.parecer.view import renderizar as renderizar_parecer_pp
    from src.modulos.ponto_parada.relatorios.view import renderizar as renderizar_relatorios_pp
    from src.modulos.ponto_parada.enderecos.view import renderizar as renderizar_enderecos_pp
    
    from src.modulos.itinerario.dashboard.view import renderizar as renderizar_dashboard_iti
    from src.modulos.itinerario.ordem_servico.view import renderizar as renderizar_os_iti
    from src.modulos.itinerario.parecer.view import renderizar as renderizar_parecer_iti
    from src.modulos.itinerario.relatorios.view import renderizar as renderizar_relatorios_iti
    
    from src.modulos.quadro_horario.dashboard.view import renderizar as renderizar_dashboard_qh
    from src.modulos.quadro_horario.parecer.view import renderizar as renderizar_parecer_qh
    from src.modulos.quadro_horario.pesquisas.view import renderizar as renderizar_pesquisas_qh
    from src.modulos.quadro_horario.relatorios.view import renderizar as renderizar_relatorios_qh
    
    # --- NOVOS IMPORTS: PROJETOS DE MOBILIDADE ---
    from src.modulos.projetos_mobilidade.dashboard.view import renderizar as renderizar_dashboard_pm
    from src.modulos.projetos_mobilidade.parecer.view import renderizar as renderizar_parecer_pm
    from src.modulos.projetos_mobilidade.relatorios.view import renderizar as renderizar_relatorios_pm
    
    from src.modulos.admin.view import renderizar as renderizar_admin_central
    from src.core.shared.utils import resource_path
except ImportError as e:
    print(f"[Aviso] Falha ao importar submódulos: {e}")
    print("Core modules ou shared utils não encontrados. Fallback para resource_path básico.")
    def resource_path(path): return path

# --- Definição de Cores Profissionais UI/UX (Clean Admin) ---
COLOR_BG_CONTENT = "#F2F2F2"      
COLOR_SIDEBAR = "#FFFFFF"         
COLOR_ACCENT = "#0F8C75"          
COLOR_TEXT_DARK = "#333333"       
COLOR_TEXT_MUTED = "#888888"      
COLOR_HOVER = "#E9ECEF"           

# --- Definição de ÍCONES PNG UI/UX "Premium" ---
ICONS_PATH = "assets"
SIZE_HEADER = (24, 24)
SIZE_ITEM = (20, 20)

ICONS_PNG = {
    "Header_Admin": resource_path(f"{ICONS_PATH}/admin-header.png"),
    "Header_Dashboards": resource_path(f"{ICONS_PATH}/dashboard-header.png"), 
    "Header_PontoParada": resource_path(f"{ICONS_PATH}/ponto-parada-header.png"), 
    "Header_Itinerario": resource_path(f"{ICONS_PATH}/itinerario-header.png"), 
    "Header_QuadroHorario": resource_path(f"{ICONS_PATH}/quadro-horario-header.png"), 
    "Header_ProjetosMobilidade": resource_path(f"{ICONS_PATH}/projetos-mobilidade-header.png"), # Ícone do novo módulo
    "Header_Sistema": resource_path(f"{ICONS_PATH}/sistema-header.png"),
    
    "Dashboard_Item": resource_path(f"{ICONS_PATH}/dashboard-item.png"), 
    "OS": resource_path(f"{ICONS_PATH}/os-icon.png"),
    "Parecer": resource_path(f"{ICONS_PATH}/parecer-icon.png"),
    "Relatorios_Os": resource_path(f"{ICONS_PATH}/relatorios-os-icon.png"),
    "Relatorios_Parecer": resource_path(f"{ICONS_PATH}/relatorios-parecer-icon.png"),
    "Relatorio_Pesquisas": resource_path(f"{ICONS_PATH}/relatorio-pesquisas-icon.png"),
    "Enderecos": resource_path(f"{ICONS_PATH}/enderecos-icon.png"), 
    "Pesquisas": resource_path(f"{ICONS_PATH}/pesquisas-icon.png"), 
    "Historico": resource_path(f"{ICONS_PATH}/historico-icon.png"),
    "Sair": resource_path(f"{ICONS_PATH}/sair-icon.png"),       
    "Menu": resource_path(f"{ICONS_PATH}/menu-icon.png"),
    "Arrow_Down": resource_path(f"{ICONS_PATH}/arrow-down-icon.png")
}

def iniciar_sistema(usuario_dados):
    nome_usuario = usuario_dados.get("nome", "Usuário")
    is_admin = usuario_dados.get("is_admin", False)
    tipo_perfil = str(usuario_dados.get("tipo_perfil", "")).strip().upper()

    app = ctk.CTk()
    app.title("SGI - DIPLA | Sistema de Gestão Integrado")
    
    try:
        app.state("zoomed") 
        app.iconbitmap(resource_path("assets/sgi_logo.ico"))
    except:
        app.geometry("1400x800")

    # def fechar_sistema():
    #     app.quit()
    #     app.destroy()
    #     sys.exit(0) # Força o Python a matar qualquer animação em segundo plano

    # app.protocol("WM_DELETE_WINDOW", fechar_sistema)

    # =====================================================================
    # ESTILIZAÇÃO GLOBAL E TELA DE CARREGAMENTO
    # =====================================================================
    ctk.set_appearance_mode("Light") 
    app.configure(fg_color=COLOR_BG_CONTENT)

    tela_carregamento = ctk.CTkFrame(app, fg_color=COLOR_BG_CONTENT)
    tela_carregamento.pack(fill="both", expand=True)
    
    try:
        caminho_logo = resource_path("assets/sgi_logo.png")
        img_logo_splash = ctk.CTkImage(Image.open(caminho_logo), size=(550, 550))
        ctk.CTkLabel(tela_carregamento, image=img_logo_splash, text="").pack(expand=True, pady=(120, 10))
    except:
        ctk.CTkLabel(tela_carregamento, text="SGI | DIPLA", font=("Arial Black", 60), text_color=COLOR_ACCENT).pack(expand=True, pady=(120, 10))
        
    ctk.CTkLabel(tela_carregamento, text="A organizar o ambiente de trabalho...\nPor favor, aguarde. ⏳", font=("Arial Bold", 20), text_color=COLOR_TEXT_MUTED, justify="center").pack(expand=True, pady=(0, 150))
    app.update()

    # Variáveis de Estado UI/UX
    is_sidebar_expanded = tk.BooleanVar(value=True)
    
    # Listas para guardar referências e gerir o encolhimento
    labels_dropdown = [] 
    listas_botoes_texto = [] 
    listas_botoes_frames = [] 

    def load_icon_png(path, size):
        try:
            img = Image.open(path)
            return ctk.CTkImage(img, size=size)
        except Exception as e:
            print(f"Erro Crítico UI/UX ao carregar ícone {path}: {e}")
            return None 

    # =====================================================================
    # CARREGAMENTO ÚNICO DE IMAGENS NA MEMÓRIA (Otimização)
    # =====================================================================
    loaded_imgs_headers = {}
    loaded_imgs_items = {}

    header_keys = ["Header_Dashboards", "Header_PontoParada", "Header_Itinerario", "Header_QuadroHorario", "Header_ProjetosMobilidade", "Header_Sistema", "Header_Admin"]
    for key in header_keys:
        loaded_imgs_headers[key] = load_icon_png(ICONS_PNG[key], SIZE_HEADER)

    item_keys = ["Dashboard_Item", "OS", "Parecer", "Relatorios_Os", "Relatorios_Parecer", "Relatorio_Pesquisas", "Enderecos", "Pesquisas", "Historico", "Menu", "Sair"]
    for key in item_keys:
        loaded_imgs_items[key] = load_icon_png(ICONS_PNG[key], SIZE_ITEM)

    try:
        img_seta = Image.open(ICONS_PNG["Arrow_Down"])
        loaded_imgs_items["Arrow_Down"] = ctk.CTkImage(img_seta, size=(16, 16))
        loaded_imgs_items["Arrow_Closed"] = ctk.CTkImage(img_seta.rotate(90), size=(16, 16))
    except Exception as e:
        print("Erro ao carregar seta:", e)
        loaded_imgs_items["Arrow_Down"] = None
        loaded_imgs_items["Arrow_Closed"] = None

    # =====================================================================
    # MONTAGEM DA ESTRUTURA (Layout Vertical)
    # =====================================================================
    root_frame = ctk.CTkFrame(app, fg_color="transparent")

    # --- 1. SIDEBAR (Barra Lateral Esquerda) ---
    sidebar_frame = ctk.CTkFrame(root_frame, width=230, fg_color=COLOR_SIDEBAR, corner_radius=0)
    sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
    sidebar_frame.pack_propagate(False)

    # --- 2. ÁREA DE CONTEÚDO (Centro/Direita) ---
    content_area = ctk.CTkFrame(root_frame, fg_color=COLOR_BG_CONTENT, corner_radius=0)
    content_area.pack(side="left", fill="both", expand=True)

    # =====================================================================
    # COMPONENTES DA SIDEBAR
    # =====================================================================
    top_sidebar_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
    top_sidebar_frame.pack(fill="x", pady=(15, 20))

    btn_toggle = ctk.CTkButton(
        top_sidebar_frame, 
        image=loaded_imgs_items["Menu"], 
        text="", 
        fg_color="transparent", 
        hover_color=COLOR_HOVER, 
        width=40, 
        height=40, 
        command=lambda: toggle_sidebar()
    )
    btn_toggle.pack(side="left", padx=(10, 0)) 

    logo_center_container = ctk.CTkFrame(top_sidebar_frame, fg_color="transparent")
    logo_center_container.pack(fill="x", expand=True, padx=(0, 40)) 

    try:
        caminho_logo = resource_path("assets/sgi_logo.png")
        img_logo = ctk.CTkImage(Image.open(caminho_logo), size=(70, 70))
        lbl_logo = ctk.CTkLabel(logo_center_container, image=img_logo, text="")
        lbl_logo.pack(anchor="center")
    except:
        lbl_logo = ctk.CTkLabel(logo_center_container, text="E", font=("Arial Black", 30), text_color="white", fg_color=COLOR_ACCENT, corner_radius=35, width=70, height=70)
        lbl_logo.pack(anchor="center")

    menu_scroll_frame = ctk.CTkScrollableFrame(sidebar_frame, fg_color="transparent", corner_radius=0)
    menu_scroll_frame.pack(fill="both", expand=True, pady=(0, 10))

    footer_sidebar_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent", corner_radius=0, height=90) 
    footer_sidebar_frame.pack(side="bottom", fill="x", pady=(20, 10)) 
    footer_sidebar_frame.pack_propagate(False)

    ctk.CTkFrame(footer_sidebar_frame, fg_color="#E0E0E0", height=1).pack(fill="x", side="top", pady=(0, 10)) 
    
    user_root_container = ctk.CTkFrame(footer_sidebar_frame, fg_color="transparent")
    user_root_container.pack(fill="both", expand=True, padx=12)

    user_text_hide_container = ctk.CTkFrame(user_root_container, fg_color="transparent")
    user_text_hide_container.pack(side="left", fill="both", expand=True)
    
    lbl_ol_nome = ctk.CTkLabel(user_text_hide_container, text=f"Olá, {nome_usuario.split()[0]}", font=("Arial Bold", 14), text_color=COLOR_TEXT_DARK, anchor="w")
    lbl_ol_nome.pack(fill="x", pady=(2,0))
    
    perfil_formatado = 'Chefia' if is_admin else tipo_perfil.replace(',', ' & ')
    lbl_perfil_setor = ctk.CTkLabel(user_text_hide_container, text=perfil_formatado.capitalize(), font=("Arial", 11), text_color=COLOR_TEXT_MUTED, anchor="w", wraplength=170, justify="left")
    lbl_perfil_setor.pack(fill="x")

    def fazer_logout():
        if messagebox.askyesno("Sair", "Tem certeza que deseja encerrar a sessão?"):
            app.destroy()
            from main import bootstrap
            bootstrap()

    btn_logout = ctk.CTkButton(user_root_container, image=loaded_imgs_items["Sair"], text="", font=("Arial Bold", 18), text_color="#D32F2F", fg_color="transparent", hover_color=COLOR_HOVER, width=40, height=40, command=fazer_logout)
    btn_logout.pack(side="right")

    # =====================================================================
    # ÁREA DE CONTEÚDO (Views Unificadas)
    # =====================================================================
    frame_conteudo_interno = ctk.CTkFrame(content_area, fg_color="transparent", corner_radius=10)
    frame_conteudo_interno.pack(fill="both", expand=True, padx=20, pady=20)

    abas = {}
    instancias_views = {}
    botoes_ui = [] 

    # Adicionado PROJETOS DE MOBILIDADE no dicionário
    categorias_menu = {
        "DASHBOARDS": [],
        "PONTO DE PARADA": [],
        "ITINERÁRIO": [],
        "QUADRO DE HORÁRIO": [],
        "PROJETOS DE MOBILIDADE": [],
        "SISTEMA": [],
        "ADMIN": []
    }

    if is_admin:
        # MENU DO ADMINISTRADOR AGORA COM ACESSO TOTAL
        categorias_menu["DASHBOARDS"].append({"nome": "Visão Global", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_geral(a, u)})
        categorias_menu["ADMIN"].append({"nome": "Configurações", "img_icon": loaded_imgs_items["Menu"], "render": lambda a, u: renderizar_admin_central(a, u)})
        
        categorias_menu["PONTO DE PARADA"].extend([
            {"nome": "Dashboard", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_pp(a, u)},
            {"nome": "Gerar OS", "img_icon": loaded_imgs_items["OS"], "render": lambda a, u: renderizar_os_pp(a, u)},
            {"nome": "Gerar Parecer", "img_icon": loaded_imgs_items["Parecer"], "render": lambda a, u: renderizar_parecer_pp(a, u)},
            {"nome": "Relatórios OS", "img_icon": loaded_imgs_items["Relatorios_Os"], "render": lambda a, u: renderizar_relatorios_pp(a, u, "OS")},
            {"nome": "Relatórios Parecer", "img_icon": loaded_imgs_items["Relatorios_Parecer"], "render": lambda a, u: renderizar_relatorios_pp(a, u, "PARECER")},
            {"nome": "Gestão Endereços", "img_icon": loaded_imgs_items["Enderecos"], "render": lambda a, u: renderizar_enderecos_pp(a, u)}
        ])
        
        categorias_menu["ITINERÁRIO"].extend([
            {"nome": "Dashboard", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_iti(a, u)},
            {"nome": "Gerar OS", "img_icon": loaded_imgs_items["OS"], "render": lambda a, u: renderizar_os_iti(a, u)},
            {"nome": "Gerar Parecer", "img_icon": loaded_imgs_items["Parecer"], "render": lambda a, u: renderizar_parecer_iti(a, u)},
            {"nome": "Relatórios OS", "img_icon": loaded_imgs_items["Relatorios_Os"], "render": lambda a, u: renderizar_relatorios_iti(a, u, "OS")},
            {"nome": "Relatórios Parecer", "img_icon": loaded_imgs_items["Relatorios_Parecer"], "render": lambda a, u: renderizar_relatorios_iti(a, u, "PARECER")}
        ])
        
        categorias_menu["QUADRO DE HORÁRIO"].extend([
            {"nome": "Dashboard", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_qh(a, u)},
            {"nome": "Gerar Parecer", "img_icon": loaded_imgs_items["Parecer"], "render": lambda a, u: renderizar_parecer_qh(a, u)},
            {"nome": "Pesquisas de Campo", "img_icon": loaded_imgs_items["Pesquisas"], "render": lambda a, u: renderizar_pesquisas_qh(a, u)},
            {"nome": "Relatórios Parecer", "img_icon": loaded_imgs_items["Relatorios_Parecer"], "render": lambda a, u: renderizar_relatorios_qh(a, u, "PARECER")},
            {"nome": "Relatórios Pesquisas", "img_icon": loaded_imgs_items["Relatorio_Pesquisas"], "render": lambda a, u: renderizar_relatorios_qh(a, u, "PESQUISA")}
        ])

        # --- NOVO BLOCO: PROJETOS DE MOBILIDADE (ADMIN) ---
        categorias_menu["PROJETOS DE MOBILIDADE"].extend([
            {"nome": "Dashboard", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_pm(a, u)},
            {"nome": "Gerar Parecer", "img_icon": loaded_imgs_items["Parecer"], "render": lambda a, u: renderizar_parecer_pm(a, u)},
            {"nome": "Relatórios Parecer", "img_icon": loaded_imgs_items["Relatorios_Parecer"], "render": lambda a, u: renderizar_relatorios_pm(a, u)}
        ])
        
        categorias_menu["SISTEMA"].append({"nome": "Histórico Global", "img_icon": loaded_imgs_items["Historico"], "render": lambda a, u: renderizar_historico(a, u)})

    else:
        # MENU DE UTILIZADOR COMUM
        if "PONTO DE PARADA" in tipo_perfil:
            categorias_menu["PONTO DE PARADA"].extend([
                {"nome": "Dashboard", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_pp(a, u)},
                {"nome": "Gerar OS", "img_icon": loaded_imgs_items["OS"], "render": lambda a, u: renderizar_os_pp(a, u)},
                {"nome": "Gerar Parecer", "img_icon": loaded_imgs_items["Parecer"], "render": lambda a, u: renderizar_parecer_pp(a, u)},
                {"nome": "Relatórios OS", "img_icon": loaded_imgs_items["Relatorios_Os"], "render": lambda a, u: renderizar_relatorios_pp(a, u, "OS")},
                {"nome": "Relatórios Parecer", "img_icon": loaded_imgs_items["Relatorios_Parecer"], "render": lambda a, u: renderizar_relatorios_pp(a, u, "PARECER")},
            ])

        if "ITINERARIO" in tipo_perfil:
            categorias_menu["ITINERÁRIO"].extend([
                {"nome": "Dashboard", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_iti(a, u)},
                {"nome": "Gerar OS", "img_icon": loaded_imgs_items["OS"], "render": lambda a, u: renderizar_os_iti(a, u)},
                {"nome": "Gerar Parecer", "img_icon": loaded_imgs_items["Parecer"], "render": lambda a, u: renderizar_parecer_iti(a, u)},
                {"nome": "Relatórios OS", "img_icon": loaded_imgs_items["Relatorios_Os"], "render": lambda a, u: renderizar_relatorios_iti(a, u, "OS")},
                {"nome": "Relatórios Parecer", "img_icon": loaded_imgs_items["Relatorios_Parecer"], "render": lambda a, u: renderizar_relatorios_iti(a, u, "PARECER")},
            ])

        if "QUADRO DE HORARIO" in tipo_perfil:
            categorias_menu["QUADRO DE HORÁRIO"].extend([
                {"nome": "Dashboard", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_qh(a, u)},
                {"nome": "Gerar Parecer", "img_icon": loaded_imgs_items["Parecer"], "render": lambda a, u: renderizar_parecer_qh(a, u)},
                {"nome": "Pesquisas de Campo", "img_icon": loaded_imgs_items["Pesquisas"], "render": lambda a, u: renderizar_pesquisas_qh(a, u)},
                {"nome": "Relatórios Parecer", "img_icon": loaded_imgs_items["Relatorios_Parecer"], "render": lambda a, u: renderizar_relatorios_qh(a, u, "PARECER")},
                {"nome": "Relatórios Pesquisas", "img_icon": loaded_imgs_items["Relatorio_Pesquisas"], "render": lambda a, u: renderizar_relatorios_qh(a, u, "PESQUISA")},
            ])

        # --- NOVO BLOCO: PROJETOS DE MOBILIDADE (UTILIZADOR) ---
        if "PROJETOS DE MOBILIDADE" in tipo_perfil:
            categorias_menu["PROJETOS DE MOBILIDADE"].extend([
                {"nome": "Dashboard", "img_icon": loaded_imgs_items["Dashboard_Item"], "render": lambda a, u: renderizar_dashboard_pm(a, u)},
                {"nome": "Gerar Parecer", "img_icon": loaded_imgs_items["Parecer"], "render": lambda a, u: renderizar_parecer_pm(a, u)},
                {"nome": "Relatórios Parecer", "img_icon": loaded_imgs_items["Relatorios_Parecer"], "render": lambda a, u: renderizar_relatorios_pm(a, u)}
            ])

    def selecionar_aba(chave_unica, master_frame):
        for aba in abas.values(): aba.pack_forget()
        abas[chave_unica].pack(fill="both", expand=True)

        for frame, icon_widget, text_widget in botoes_ui:
            if chave_unica == frame.chave:
                frame.configure(fg_color=COLOR_ACCENT)
                icon_widget.configure(text_color="white")
                text_widget.configure(text_color="white", font=("Arial Bold", 13))
            else:
                frame.configure(fg_color="transparent")
                icon_widget.configure(text_color=COLOR_TEXT_DARK)
                text_widget.configure(text_color=COLOR_TEXT_DARK, font=("Arial", 13))

        view = instancias_views.get(chave_unica)
        if view:
            if hasattr(view, 'atualizar_completo'): view.atualizar_completo()
            elif hasattr(view, 'acao_buscar'): view.acao_buscar()

    def toggle_dropdown(target_frame, arrow_label, expanded_var):
        if expanded_var.get():
            target_frame.pack_forget()
            arrow_label.configure(image=loaded_imgs_items["Arrow_Closed"]) 
            expanded_var.set(False)
        else:
            target_frame.pack(fill="x", pady=(2, 10))
            arrow_label.configure(image=loaded_imgs_items["Arrow_Down"]) 
            expanded_var.set(True)

    def toggle_sidebar():
        if is_sidebar_expanded.get():
            sidebar_frame.configure(width=75) 
            
            user_text_hide_container.pack_forget()
            btn_logout.pack_forget()
            
            for btn_fr in listas_botoes_frames: btn_fr.pack_configure(padx=5)
            for txt_lbl in listas_botoes_texto: txt_lbl.pack_forget()
            for arr_lbl in labels_dropdown: arr_lbl.pack_forget()
            
            user_root_container.pack_configure(padx=5)
            is_sidebar_expanded.set(False)
        else:
            sidebar_frame.configure(width=230) 

            user_text_hide_container.pack(side="left", fill="both", expand=True)
            btn_logout.pack(side="right")
            
            for btn_fr in listas_botoes_frames: btn_fr.pack_configure(padx=10)
            for txt_lbl in listas_botoes_texto: txt_lbl.pack(side="left", padx=(10, 0))
            for arr_lbl in labels_dropdown: arr_lbl.pack(side="right", padx=15)
            
            user_root_container.pack_configure(padx=12)
            is_sidebar_expanded.set(True)

    # =====================================================================
    # RENDERIZAÇÃO DO MENU (Estilo Accordion) E DEFINIÇÃO DA ABA INICIAL
    # =====================================================================
    
    # Variáveis para a inteligência da aba inicial
    aba_inicial_chave = None
    primeiro_master_frame = None
    
    aba_preferida_chave = None
    master_frame_preferido = None

    for categoria, itens in categorias_menu.items():
        if not itens: continue 

        cat_header_frame = ctk.CTkFrame(menu_scroll_frame, fg_color="transparent")
        cat_header_frame.pack(fill="x", pady=(5, 0))

        expanded_var = tk.BooleanVar(value=True) 

        btn_header_frame = ctk.CTkFrame(cat_header_frame, fg_color="transparent", height=40, cursor="hand2")
        btn_header_frame.pack(fill="x")
        btn_header_frame.pack_propagate(False) 

        img_cat_icon = None
        if "DASHBOARDS" in categoria: img_cat_icon = loaded_imgs_headers["Header_Dashboards"]
        elif "PONTO DE PARADA" in categoria: img_cat_icon = loaded_imgs_headers["Header_PontoParada"]
        elif "ITINERÁRIO" in categoria: img_cat_icon = loaded_imgs_headers["Header_Itinerario"]
        elif "QUADRO DE HORÁRIO" in categoria: img_cat_icon = loaded_imgs_headers["Header_QuadroHorario"]
        elif "PROJETOS DE MOBILIDADE" in categoria: img_cat_icon = loaded_imgs_headers.get("Header_ProjetosMobilidade") or loaded_imgs_headers["Header_Sistema"]
        elif "SISTEMA" in categoria: img_cat_icon = loaded_imgs_headers["Header_Sistema"]
        elif "ADMIN" in categoria: img_cat_icon = loaded_imgs_headers["Header_Admin"] # Adicione esta linha aqui

        lbl_cat_icon = ctk.CTkLabel(btn_header_frame, image=img_cat_icon, text="")
        lbl_cat_icon.pack(side="left", padx=10)

        # CORREÇÃO 1: Empacotamos a seta para a direita ANTES do texto.
        # Assim garantimos que ela não seja expulsa da tela por nomes longos.
        lbl_seta = ctk.CTkLabel(btn_header_frame, image=loaded_imgs_items["Arrow_Down"], text="")
        lbl_seta.pack(side="right", padx=15)
        labels_dropdown.append(lbl_seta)

        # CORREÇÃO 2: Lógica de abreviação para Projetos de Mobilidade
        texto_exibicao = "PROJ. DE MOBILIDADE" if categoria == "PROJETOS DE MOBILIDADE" else categoria

        lbl_titulo = ctk.CTkLabel(btn_header_frame, text=texto_exibicao, font=("Arial Bold", 11), text_color=COLOR_TEXT_MUTED)
        lbl_titulo.pack(side="left", padx=5) 
        listas_botoes_texto.append(lbl_titulo)

        sub_itens_frame = ctk.CTkFrame(cat_header_frame, fg_color="transparent")
        sub_itens_frame.pack(fill="x", pady=(2, 10))

        btn_header_frame.bind("<Enter>", lambda e, f=btn_header_frame: f.configure(fg_color=COLOR_HOVER))
        btn_header_frame.bind("<Leave>", lambda e, f=btn_header_frame: f.configure(fg_color="transparent"))
        
        comando_toggle = lambda e, sub=sub_itens_frame, seta=lbl_seta, var=expanded_var: toggle_dropdown(sub, seta, var)
        btn_header_frame.bind("<Button-1>", comando_toggle)
        lbl_cat_icon.bind("<Button-1>", comando_toggle)
        lbl_titulo.bind("<Button-1>", comando_toggle)
        lbl_seta.bind("<Button-1>", comando_toggle)

        for item in itens:
            chave_unica = f"{categoria}_{item['nome']}"
            
            aba_frame = ctk.CTkFrame(frame_conteudo_interno, fg_color="transparent")
            abas[chave_unica] = aba_frame
            instancias_views[chave_unica] = item["render"](aba_frame, usuario_dados)

            master_btn_frame = ctk.CTkFrame(sub_itens_frame, fg_color="transparent", height=45, corner_radius=8, cursor="hand2")
            master_btn_frame.pack(fill="x", padx=10, pady=2) 
            master_btn_frame.chave = chave_unica 
            listas_botoes_frames.append(master_btn_frame)

            lbl_icon = ctk.CTkLabel(master_btn_frame, image=item["img_icon"], text="", width=35)
            lbl_icon.pack(side="left", padx=(5, 0), pady=6) 

            lbl_text = ctk.CTkLabel(master_btn_frame, text=item["nome"], font=("Arial", 13), text_color=COLOR_TEXT_DARK, anchor="w")
            lbl_text.pack(side="left", padx=(10, 0))
            listas_botoes_texto.append(lbl_text) 

            master_btn_frame.bind("<Button-1>", lambda e, c=chave_unica, m=master_btn_frame: selecionar_aba(c, m))
            lbl_icon.bind("<Button-1>", lambda e, c=chave_unica, m=master_btn_frame: selecionar_aba(c, m))
            lbl_text.bind("<Button-1>", lambda e, c=chave_unica, m=master_btn_frame: selecionar_aba(c, m))
            
            master_btn_frame.bind("<Enter>", lambda e, f=master_btn_frame: f.configure(fg_color=COLOR_HOVER) if f.cget("fg_color") == "transparent" else None)
            master_btn_frame.bind("<Leave>", lambda e, f=master_btn_frame: f.configure(fg_color="transparent") if f.cget("fg_color") == COLOR_HOVER else None)

            botoes_ui.append((master_btn_frame, lbl_icon, lbl_text))

            if not aba_inicial_chave:
                aba_inicial_chave = chave_unica
                primeiro_master_frame = master_btn_frame

            if item["nome"] == "Gerar OS" and not aba_preferida_chave:
                aba_preferida_chave = chave_unica
                master_frame_preferido = master_btn_frame

    if aba_preferida_chave and master_frame_preferido:
        selecionar_aba(aba_preferida_chave, master_frame_preferido)
    elif aba_inicial_chave and primeiro_master_frame:
        selecionar_aba(aba_inicial_chave, primeiro_master_frame)

    tela_carregamento.destroy()
    root_frame.pack(fill="both", expand=True)
    
    try: app.state("zoomed") 
    except: pass

    app.mainloop()

def bootstrap():
    auth = AuthService()
    sessao = auth.ler_sessao()
    
    try: 
        ctk.set_appearance_mode("Light") 
    except: 
        pass 
        
    if sessao:
        iniciar_sistema(sessao)
    else:
        def on_login_sucesso(dados_usuario):
            app_login.destroy()
            iniciar_sistema(dados_usuario)

        app_login = LoginView(on_login_success=on_login_sucesso)
        app_login.mainloop()

if __name__ == "__main__":
    bootstrap()