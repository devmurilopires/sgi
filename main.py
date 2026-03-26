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
from src.painel_geral.dashboard.view import renderizar as renderizar_dashboard

# MÓDULOS: PONTO DE PARADA
from src.modulos.ponto_parada.ordem_servico.view import renderizar as renderizar_os_pp
from src.modulos.ponto_parada.parecer.view import renderizar as renderizar_parecer_pp
from src.modulos.ponto_parada.relatorios.view import renderizar as renderizar_relatorios_pp
from src.modulos.ponto_parada.enderecos.view import renderizar as renderizar_enderecos_pp

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

    app = ctk.CTk()
    # Título do sistema atualizado
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
        # Texto da Splash atualizado
        ctk.CTkLabel(tela_carregamento, text="SGI - DIPLA", font=("Arial Black", 80), text_color=COLOR_PRIMARY).pack(expand=True, pady=(150, 10))
        
    ctk.CTkLabel(tela_carregamento, text="Carregando módulos e painéis do sistema...\nPor favor, aguarde. ⏳", font=("Arial Bold", 23), text_color="#555", justify="center").pack(expand=True, pady=(0, 150))
    
    app.update()

    # =====================================================================
    # MONTAGEM DO SISTEMA
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

    # Título do cabeçalho atualizado
    ctk.CTkLabel(frame_topo, text="Sistema de Gestão Integrado", font=("Century Gothic bold", 20)).pack(side="left", pady=(12, 0))

    perfil_texto = f"👤 Olá, {nome_usuario} ({'Admin' if is_admin else 'Comum'})"
    ctk.CTkLabel(frame_topo, text=perfil_texto, font=("Arial", 14), text_color="gray").pack(side="right", padx=20)

    # MENU LATERAL / BOTOES
    menu_container = ctk.CTkFrame(frame_principal, fg_color="transparent")
    menu_container.pack(fill="x", padx=10, pady=(15, 0))

    # Nomes dos botões atualizados para clareza
    menu_botoes = [
        ("Visão Geral (Painel)", COLOR_PRIMARY),
        ("OS (Paradas)", COLOR_PRIMARY),
        ("Relatórios OS (Paradas)", COLOR_PRIMARY),
        ("Parecer (Paradas)", COLOR_PRIMARY),
        ("Relatórios Parecer (Paradas)", COLOR_PRIMARY),
        ("Histórico Global", COLOR_PRIMARY),
    ]
    if is_admin: menu_botoes.append(("Endereços (Paradas)", "#F24822"))

    # CONTEÚDO
    frame_conteudo = ctk.CTkFrame(frame_principal, fg_color="#FFFFFF", corner_radius=15)
    frame_conteudo.pack(fill="both", expand=True, padx=20, pady=20)

    abas = {}

    for nome, _ in menu_botoes:
        aba = ctk.CTkFrame(frame_conteudo, fg_color="transparent")
        abas[nome] = aba

    # Renderiza os painéis mapeando para as novas abas
    view_dash = renderizar_dashboard(abas["Visão Geral (Painel)"], usuario_dados)
    view_os_pp = renderizar_os_pp(abas["OS (Paradas)"], usuario_dados)
    view_rel_os_pp = renderizar_relatorios_pp(abas["Relatórios OS (Paradas)"], usuario_dados, tipo="OS")
    view_par_pp = renderizar_parecer_pp(abas["Parecer (Paradas)"], usuario_dados)
    view_rel_par_pp = renderizar_relatorios_pp(abas["Relatórios Parecer (Paradas)"], usuario_dados, tipo="PARECER")
    view_hist = renderizar_historico(abas["Histórico Global"], usuario_dados)
    if is_admin: 
        view_end = renderizar_enderecos_pp(abas["Endereços (Paradas)"], usuario_dados)

    def selecionar_aba(nome_aba):
        for aba in abas.values(): aba.pack_forget()
        abas[nome_aba].pack(fill="both", expand=True)

        # AUTO-ATUALIZAÇÃO
        if nome_aba == "Visão Geral (Painel)":
            view_dash.atualizar_completo()
        elif nome_aba == "Relatórios OS (Paradas)":
            view_rel_os_pp.acao_buscar()
        elif nome_aba == "Relatórios Parecer (Paradas)":
            view_rel_par_pp.acao_buscar()

    for texto, cor in menu_botoes:
        btn = ctk.CTkButton(menu_container, text=texto, fg_color=cor, font=("Arial Bold", 13), corner_radius=8, height=35, hover_color=COLOR_PRIMARY_HOVER, command=lambda t=texto: selecionar_aba(t))
        btn.pack(side="left", padx=5)

    # Inicia na aba de OS de Paradas
    selecionar_aba("OS (Paradas)")

    tela_carregamento.destroy()
    frame_principal.pack(fill="both", expand=True)
    
    try:
        app.state("zoomed") 
    except:
        pass

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