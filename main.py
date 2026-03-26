import customtkinter as ctk
from PIL import Image

# =====================================================================
# 1. IMPORTS DA NOVA ARQUITETURA (DDD)
# =====================================================================
# CORE (Coração do sistema)
from src.core.auth.view import LoginView
from src.core.auth.service import AuthService
from src.core.historico.view import renderizar as renderizar_historico

# PAINEL GERAL (Visão da Chefia)
from src.painel_geral.dashboard.view import renderizar as renderizar_dashboard_geral

# MÓDULOS: PONTO DE PARADA (PP)
from src.modulos.ponto_parada.dashboard.view import renderizar as renderizar_dashboard_pp
from src.modulos.ponto_parada.ordem_servico.view import renderizar as renderizar_os_pp
from src.modulos.ponto_parada.parecer.view import renderizar as renderizar_parecer_pp
from src.modulos.ponto_parada.relatorios.view import renderizar as renderizar_relatorios_pp
from src.modulos.ponto_parada.enderecos.view import renderizar as renderizar_enderecos_pp

# MÓDULOS: ITINERÁRIO (ITI)
from src.modulos.itinerario.dashboard.view import renderizar as renderizar_dashboard_iti
from src.modulos.itinerario.ordem_servico.view import renderizar as renderizar_os_iti
from src.modulos.itinerario.parecer.view import renderizar as renderizar_parecer_iti
from src.modulos.itinerario.relatorios.view import renderizar as renderizar_relatorios_iti

# MÓDULOS: QUADRO DE HORÁRIO (SPR)
from src.modulos.quadro_horario.dashboard.view import renderizar as renderizar_dashboard_qh
from src.modulos.quadro_horario.parecer.view import renderizar as renderizar_parecer_qh
from src.modulos.quadro_horario.pesquisas.view import renderizar as renderizar_pesquisas_qh
from src.modulos.quadro_horario.relatorios.view import renderizar as renderizar_relatorios_qh

try:
    from src.core.shared.utils import resource_path
except ImportError:
    def resource_path(path): return path

COLOR_PRIMARY = "#0F8C75"
COLOR_PRIMARY_HOVER = "#0B6B59"
COLOR_BG = "#F2F2F2"

def iniciar_sistema(usuario_dados):
    nome_usuario = usuario_dados.get("nome", "Usuário")
    is_admin = usuario_dados.get("is_admin", False)
    
    # Pegamos o perfil exato do banco de dados (ex: 'PONTO_PARADA,ITINERARIO')
    tipo_perfil = str(usuario_dados.get("tipo_perfil", "")).strip().upper()

    app = ctk.CTk()
    app.title("SGI - DIPLA | Sistema de Gestão Integrado")
    app.configure(fg_color=COLOR_BG)
    
    try:
        app.state("zoomed") 
        app.iconbitmap(resource_path("assets/sigp_logo.ico"))
    except:
        app.geometry("1280x720")

    # =====================================================================
    # TELA DE CARREGAMENTO (SPLASH SCREEN)
    # =====================================================================
    tela_carregamento = ctk.CTkFrame(app, fg_color=COLOR_BG)
    tela_carregamento.pack(fill="both", expand=True)
    
    try:
        caminho_logo = resource_path("assets/sigp_logo.png")
        img_logo_splash = ctk.CTkImage(Image.open(caminho_logo), size=(350, 350))
        ctk.CTkLabel(tela_carregamento, image=img_logo_splash, text="").pack(expand=True, pady=(150, 10))
    except:
        ctk.CTkLabel(tela_carregamento, text="SGI - DIPLA", font=("Arial Black", 80), text_color=COLOR_PRIMARY).pack(expand=True, pady=(150, 10))
        
    ctk.CTkLabel(tela_carregamento, text="Carregando módulos de acordo com o seu perfil...\nPor favor, aguarde. ⏳", font=("Arial Bold", 23), text_color="#555", justify="center").pack(expand=True, pady=(0, 150))
    app.update()

    # =====================================================================
    # MONTAGEM DA INTERFACE PRINCIPAL
    # =====================================================================
    frame_principal = ctk.CTkFrame(app, fg_color="transparent")
    
    # TOPO
    frame_topo = ctk.CTkFrame(frame_principal, height=85, corner_radius=0)
    frame_topo.pack(fill="x")

    try:
        caminho_logo = resource_path("assets/sigp_logo.png")
        img_logo = ctk.CTkImage(Image.open(caminho_logo), size=(90, 90))
        ctk.CTkLabel(frame_topo, image=img_logo, text="").pack(side="left", padx=(20, 10), pady=5)
    except:
        ctk.CTkLabel(frame_topo, text="SGI", font=("Arial Black", 24), text_color=COLOR_PRIMARY).pack(side="left", padx=(20, 10))

    ctk.CTkLabel(frame_topo, text="Sistema de Gestão Integrado", font=("Century Gothic bold", 20)).pack(side="left", pady=(12, 0))

    perfil_texto = f"👤 Olá, {nome_usuario} ({'Chefia' if is_admin else tipo_perfil.replace(',', ' & ')})"
    ctk.CTkLabel(frame_topo, text=perfil_texto, font=("Arial", 14), text_color="gray").pack(side="right", padx=20)

    # MENU LATERAL / BOTÕES (Agora Scrollable para suportar muitos botões)
    menu_container = ctk.CTkScrollableFrame(frame_principal, fg_color="transparent", height=50, orientation="horizontal")
    menu_container.pack(fill="x", padx=10, pady=(15, 0))

    # =====================================================================
    # CONTROLE DE ACESSO (RBAC) - DEFINIÇÃO DINÂMICA DE ABAS
    # =====================================================================
    config_abas = []

    # 👑 REGRA 1: CHEFIA (ADMIN) - Acesso total aos relatórios e configurações
    if is_admin:
        config_abas.extend([
            {"nome": "Visão Global DIPLA", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_dashboard_geral(a, u)},
            # Paradas
            {"nome": "Relatórios OS (Paradas)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_pp(a, u, "OS")},
            {"nome": "Relatórios Parecer (Paradas)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_pp(a, u, "PARECER")},
            {"nome": "Endereços (Paradas)", "cor": "#F24822", "render": lambda a, u: renderizar_enderecos_pp(a, u)},
            # Itinerário
            {"nome": "Relatórios OS (Itinerário)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_iti(a, u, "OS")},
            {"nome": "Relatórios Parecer (Itinerário)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_iti(a, u, "PARECER")},
            # Quadro de Horários (SPR)
            {"nome": "Parecer (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_parecer_qh(a, u)},
            {"nome": "Pesquisas (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_pesquisas_qh(a, u)},
            {"nome": "Relatórios Parecer (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_qh(a, u, "PARECER")},
            {"nome": "Relatórios Pesquisas (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_qh(a, u, "PESQUISA")},
            # Sistema
            {"nome": "Histórico Global", "cor": "#F24822", "render": lambda a, u: renderizar_historico(a, u)}
        ])

    # 👷 REGRAS ACUMULATIVAS (Técnicos da Operação)
    else:
        # 🚌 PONTO DE PARADA
        if "PONTO DE PARADA" in tipo_perfil:
            config_abas.extend([
                {"nome": "Meu Painel (Paradas)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_dashboard_pp(a, u)},
                {"nome": "OS (Paradas)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_os_pp(a, u)},
                {"nome": "Parecer (Paradas)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_parecer_pp(a, u)},
                {"nome": "Relatórios OS (Paradas)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_pp(a, u, "OS")},
                {"nome": "Relatórios Parecer (Paradas)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_pp(a, u, "PARECER")},
            ])

        # 🗺️ ITINERÁRIO
        if "ITINERARIO" in tipo_perfil:
            config_abas.extend([
                {"nome": "Meu Painel (Itinerário)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_dashboard_iti(a, u)},
                {"nome": "OS (Itinerário)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_os_iti(a, u)},
                {"nome": "Parecer (Itinerário)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_parecer_iti(a, u)},
                {"nome": "Relatórios OS (Itinerário)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_iti(a, u, "OS")},
                {"nome": "Relatórios Parecer (Itinerário)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_iti(a, u, "PARECER")},
            ])

        # ⏱️ QUADRO DE HORÁRIO (SPR)
        if "QUADRO DE HORARIO" in tipo_perfil:
            config_abas.extend([
                {"nome": "Meu Painel (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_dashboard_qh(a, u)},
                {"nome": "Parecer (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_parecer_qh(a, u)},
                {"nome": "Pesquisas (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_pesquisas_qh(a, u)},
                {"nome": "Relatórios Parecer (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_qh(a, u, "PARECER")},
                {"nome": "Relatórios Pesquisas (Horários)", "cor": COLOR_PRIMARY, "render": lambda a, u: renderizar_relatorios_qh(a, u, "PESQUISA")},
            ])

    # =====================================================================
    # RENDERIZAÇÃO INTELIGENTE
    # =====================================================================
    frame_conteudo = ctk.CTkFrame(frame_principal, fg_color="#FFFFFF", corner_radius=15)
    frame_conteudo.pack(fill="both", expand=True, padx=20, pady=20)

    abas = {}
    instancias_views = {}

    # Só cria as telas que o usuário tem acesso!
    for conf in config_abas:
        nome_aba = conf["nome"]
        aba_frame = ctk.CTkFrame(frame_conteudo, fg_color="transparent")
        abas[nome_aba] = aba_frame
        # Chama a função e guarda o objeto da tela
        view_instancia = conf["render"](aba_frame, usuario_dados)
        instancias_views[nome_aba] = view_instancia

    def selecionar_aba(nome_aba):
        for aba in abas.values(): 
            aba.pack_forget()
        abas[nome_aba].pack(fill="both", expand=True)

        # MÁGICA DO AUTO-REFRESH
        view = instancias_views.get(nome_aba)
        if view:
            if hasattr(view, 'atualizar_completo'):
                view.atualizar_completo()
            elif hasattr(view, 'acao_buscar'):
                view.acao_buscar()

    # Desenha os botões dinamicamente no menu scrollável
    for conf in config_abas:
        btn = ctk.CTkButton(menu_container, text=conf["nome"], fg_color=conf["cor"], font=("Arial Bold", 13), 
                            corner_radius=8, height=35, hover_color=COLOR_PRIMARY_HOVER, 
                            command=lambda t=conf["nome"]: selecionar_aba(t))
        btn.pack(side="left", padx=5)

    # Inicia sempre na primeira aba disponível para o usuário
    if config_abas:
        selecionar_aba(config_abas[0]["nome"])

    tela_carregamento.destroy()
    frame_principal.pack(fill="both", expand=True)
    
    try: app.state("zoomed") 
    except: pass

    app.mainloop()

def bootstrap():
    auth = AuthService()
    sessao = auth.ler_sessao()
    
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