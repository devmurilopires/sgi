import customtkinter as ctk
from tkinter import messagebox
from src.modulos.admin.parametros.view import AdminParametrosView
from src.modulos.admin.usuarios.service import UsuariosService

# NOVA IMPORTAÇÃO DO MÓDULO DE LINHAS
from src.modulos.admin.linhas.view import AdminLinhasView
from src.core.shared.colors import COLOR_PRIMARY, COLOR_SECONDARY, COLOR_BG, COLOR_TEXT, COLOR_WHITE,COLOR_HOVER
class AdminUsuariosView:
    def __init__(self, master, usuario_dados):
        self.master = master
        self.usuario_dados = usuario_dados
        self.service = UsuariosService()
        self.color_accent = COLOR_PRIMARY
        self.color_bg_card = COLOR_WHITE
        
        self.setup_ui()
        self.carregar_usuarios()

    def setup_ui(self):
        # Container Principal
        self.main_container = ctk.CTkFrame(self.master, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Moderno
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")
        
        ctk.CTkLabel(title_box, text="Gestão de Usuários", font=("Arial Bold", 28), text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Controle de acessos, perfis e permissões administrativas", font=("Arial", 13), text_color=COLOR_TEXT).pack(anchor="w")
        
        ctk.CTkButton(header_frame, text="🔄 Atualizar Lista", width=140, height=40, 
                     fg_color=COLOR_WHITE, text_color=COLOR_TEXT, border_width=1, border_color="#DDDDDD",
                     hover_color=COLOR_HOVER, font=("Arial Bold", 13),
                     command=self.carregar_usuarios).pack(side="right", pady=5)

        # Área de Scroll para os Cards
        self.scroll_container = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True)

    def carregar_usuarios(self):
        for child in self.scroll_container.winfo_children():
            child.destroy()
            
        try:
            usuarios = self.service.listar_usuarios()
            for u in usuarios:
                self.criar_card_usuario(u)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar usuários: {e}")

    def criar_card_usuario(self, user):
        card = ctk.CTkFrame(self.scroll_container, fg_color=self.color_bg_card, corner_radius=12, border_width=1, border_color="#EEEEEE")
        card.pack(fill="x", pady=8, padx=5)
        
        card.columnconfigure(0, weight=3) # Info
        card.columnconfigure(1, weight=2) # Perfil
        card.columnconfigure(2, weight=1) # Status/Admin
        card.columnconfigure(3, weight=1) # Ações

        # 1. INFORMAÇÕES BÁSICAS
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=0, padx=20, pady=15, sticky="nsew")
        
        ctk.CTkLabel(info_frame, text=user['nome_completo'].upper(), font=("Arial Bold", 15), text_color=COLOR_TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"👤 {user['username']}  |  ✉️ {user['email']}", font=("Arial", 12), text_color=COLOR_TEXT, anchor="w").pack(fill="x", pady=(2, 0))

        # 2. PERFIL DE ACESSO
        perfil_frame = ctk.CTkFrame(card, fg_color="transparent")
        perfil_frame.grid(row=0, column=1, padx=10, pady=15, sticky="nsew")
        
        ctk.CTkLabel(perfil_frame, text="PERFIS ATIVOS:", font=("Arial Bold", 10), text_color=COLOR_TEXT, anchor="w").pack(fill="x")
        
        perfis = user['tipo_perfil'].split(',') if user['tipo_perfil'] else ["SEM PERFIL"]
        for p in perfis:
            p_text = p.strip().replace('_', ' ')
            tag = ctk.CTkLabel(perfil_frame, text=f" • {p_text}", font=("Arial Bold", 11), text_color=self.color_accent, anchor="w")
            tag.pack(fill="x")

        # 3. ADMIN & STATUS
        status_frame = ctk.CTkFrame(card, fg_color="transparent")
        status_frame.grid(row=0, column=2, padx=10, pady=15, sticky="nsew")
        
        sw_admin = ctk.CTkSwitch(status_frame, text="Administrador", font=("Arial", 12), progress_color=self.color_accent, 
                                command=lambda uid=user['id'], var=user['is_admin']: self.acao_toggle_admin(uid, not var))
        if user['is_admin']: sw_admin.select()
        sw_admin.pack(anchor="w", pady=2)
        
        status_text = "ATIVO" if user['is_ativo'] else "INATIVO"
        status_color = COLOR_SECONDARY if user['is_ativo'] else COLOR_PRIMARY
        lbl_status = ctk.CTkLabel(status_frame, text=status_text, font=("Arial Bold", 11), text_color=status_color)
        lbl_status.pack(anchor="w", padx=5)

        # 4. BOTÕES DE AÇÃO
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.grid(row=0, column=3, padx=20, pady=15, sticky="e")

        ctk.CTkButton(actions_frame, text="Editar", width=80, height=32, 
                     fg_color="#F0F0F0", text_color=COLOR_TEXT, hover_color="#E0E0E0",
                     font=("Arial Bold", 12), command=lambda: self.abrir_modal_edicao(user)).pack(side="left", padx=5)

        btn_toggle_text = "Inativar" if user['is_ativo'] else "Ativar"
        btn_toggle_color = COLOR_PRIMARY if user['is_ativo'] else COLOR_SECONDARY
        
        ctk.CTkButton(actions_frame, text=btn_toggle_text, width=80, height=32, 
                     fg_color=btn_toggle_color, text_color="white", hover_color=COLOR_HOVER,
                     font=("Arial Bold", 12),
                     command=lambda uid=user['id'], st=user['is_ativo']: self.acao_toggle_ativo(uid, not st)).pack(side="left", padx=5)

    def abrir_modal_edicao(self, user):
        modal = ctk.CTkToplevel(self.master)
        modal.title(f"Editar Usuário: {user['username']}")
        modal.geometry("500x550")
        modal.grab_set() 
        modal.focus_force()
        modal.resizable(False, False)

        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (500 // 2)
        y = (modal.winfo_screenheight() // 2) - (550 // 2)
        modal.geometry(f"+{x}+{y}")

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(container, text="Editar Perfil de Acesso", font=("Arial Bold", 20)).pack(pady=(0, 20))

        ctk.CTkLabel(container, text="Selecione os módulos permitidos:", font=("Arial Bold", 13), text_color=COLOR_TEXT).pack(anchor="w", pady=5)
        
        perfis_atuais = [p.strip() for p in user['tipo_perfil'].split(',')] if user['tipo_perfil'] else []
        
        opcoes = [
            ("PONTO DE PARADA", "Ponto de Parada"),
            ("ITINERARIO", "Itinerário"),
            ("QUADRO DE HORARIO", "Quadro de Horário"),
            ("PROJETOS DE MOBILIDADE", "Projetos de Mobilidade")
        ]
        
        vars_perfil = {}
        for valor, rotulo in opcoes:
            var = ctk.BooleanVar(value=valor in perfis_atuais)
            cb = ctk.CTkCheckBox(container, text=rotulo, variable=var, fg_color=self.color_accent)
            cb.pack(anchor="w", pady=8, padx=10)
            vars_perfil[valor] = var

        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=10)

        def salvar():
            novos_perfis = [k for k, v in vars_perfil.items() if v.get()]
            perfil_string = ",".join(novos_perfis)
            
            sucesso, msg = self.service.atualizar_perfil_acesso(user['id'], perfil_string)
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_usuarios()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(footer, text="Cancelar", width=100, fg_color="#C71E1E", command=modal.destroy).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="Salvar Alterações", width=180, fg_color=self.color_accent, command=salvar).pack(side="right", padx=5)

    def acao_toggle_admin(self, uid, novo_status):
        sucesso, msg = self.service.alterar_status_admin(uid, novo_status)
        if sucesso:
            self.carregar_usuarios()
        else:
            messagebox.showerror("Erro", msg)

    def acao_toggle_ativo(self, uid, novo_status):
        msg_confirmacao = "Inativar este usuário impedirá seu acesso ao sistema. Continuar?" if not novo_status else "Reativar acesso deste usuário?"
        if messagebox.askyesno("Confirmação", msg_confirmacao):
            sucesso, msg = self.service.alterar_status_ativo(uid, novo_status)
            if sucesso:
                self.carregar_usuarios()
            else:
                messagebox.showerror("Erro", msg)

class AdminCentralView:
    def __init__(self, master, usuario_dados):
        self.master = master
        self.usuario_dados = usuario_dados
        
        self.setup_ui()

    def setup_ui(self):
        # TabView Principal
        self.tabview = ctk.CTkTabview(self.master, segmented_button_selected_color=COLOR_PRIMARY)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Adicionando Abas
        self.tabview.add("Configurações")
        self.tabview.add("Usuários")
        
        # MODIFICAÇÃO: Nova Aba adicionada
        self.tabview.add("Linhas de Ônibus")

        # Renderizando Sub-Views
        AdminParametrosView(self.tabview.tab("Configurações"), self.usuario_dados)
        AdminUsuariosView(self.tabview.tab("Usuários"), self.usuario_dados)
        
        # MODIFICAÇÃO: Instanciando a nova view das linhas dentro da aba
        AdminLinhasView(self.tabview.tab("Linhas de Ônibus"))

def renderizar(container, usuario_dados):
    return AdminCentralView(container, usuario_dados)