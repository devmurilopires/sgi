import customtkinter as ctk
from tkinter import messagebox
from src.modulos.admin.parametros.view import AdminParametrosView
from src.modulos.admin.usuarios.service import UsuariosService

class AdminUsuariosView:
    def __init__(self, master, usuario_dados):
        self.master = master
        self.usuario_dados = usuario_dados
        self.service = UsuariosService()
        self.color_accent = "#0F8C75"
        
        self.setup_ui()
        self.carregar_usuarios()

    def setup_ui(self):
        # Container Principal
        self.main_container = ctk.CTkFrame(self.master, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Título e Botão de Atualizar
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="Gestão de Usuários e Permissões", font=("Arial Bold", 24), text_color="#333333").pack(side="left")
        
        ctk.CTkButton(header_frame, text="🔄 Atualizar Lista", width=120, fg_color="#555555", command=self.carregar_usuarios).pack(side="right")

        # --- TABELA DE USUÁRIOS ---
        table_frame = ctk.CTkFrame(self.main_container, fg_color="#FFFFFF", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=2)
        
        # Cabeçalho da Tabela
        header_table = ctk.CTkFrame(table_frame, fg_color="#F9F9F9", height=40, corner_radius=0)
        header_table.pack(fill="x", side="top")
        header_table.pack_propagate(False)

        ctk.CTkLabel(header_table, text="NOME", font=("Arial Bold", 12), width=200, anchor="w").pack(side="left", padx=15)
        ctk.CTkLabel(header_table, text="USUÁRIO", font=("Arial Bold", 12), width=120, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header_table, text="PERFIL", font=("Arial Bold", 12), width=150, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header_table, text="ADMIN", font=("Arial Bold", 12), width=70).pack(side="left", padx=10)
        ctk.CTkLabel(header_table, text="AÇÕES", font=("Arial Bold", 12), width=180).pack(side="right", padx=20)

        # Área de Scroll
        self.scroll_table = ctk.CTkScrollableFrame(table_frame, fg_color="transparent", corner_radius=0)
        self.scroll_table.pack(fill="both", expand=True)

    def carregar_usuarios(self):
        for child in self.scroll_table.winfo_children():
            child.destroy()
            
        try:
            usuarios = self.service.listar_usuarios()
            
            for u in usuarios:
                row = ctk.CTkFrame(self.scroll_table, fg_color="transparent", height=50)
                row.pack(fill="x", pady=2)
                
                # Nome e Email
                name_frame = ctk.CTkFrame(row, fg_color="transparent", width=200)
                name_frame.pack(side="left", padx=15)
                name_frame.pack_propagate(False)
                ctk.CTkLabel(name_frame, text=u['nome_completo'], font=("Arial Bold", 13), anchor="w").pack(fill="x")
                ctk.CTkLabel(name_frame, text=u['email'], font=("Arial", 10), text_color="#777777", anchor="w").pack(fill="x")

                ctk.CTkLabel(row, text=u['username'], width=120, anchor="w").pack(side="left", padx=10)
                
                # Perfil (Combo ou Label)
                ctk.CTkLabel(row, text=u['tipo_perfil'].replace(',', ' | '), width=150, anchor="w", font=("Arial", 11)).pack(side="left", padx=10)
                
                # Admin Switch
                sw_admin = ctk.CTkSwitch(row, text="", width=70, progress_color=self.color_accent, 
                                        command=lambda uid=u['id'], var=u['is_admin']: self.acao_toggle_admin(uid, not var))
                if u['is_admin']: sw_admin.select()
                sw_admin.pack(side="left", padx=10)

                # Botões de Ação
                actions_frame = ctk.CTkFrame(row, fg_color="transparent")
                actions_frame.pack(side="right", padx=10)

                status_text = "Inativar" if u['is_ativo'] else "Ativar"
                status_color = "#F24822" if u['is_ativo'] else "#28A745"
                
                ctk.CTkButton(actions_frame, text=status_text, width=80, height=28, 
                             fg_color=status_color, font=("Arial Bold", 11),
                             command=lambda uid=u['id'], st=u['is_ativo']: self.acao_toggle_ativo(uid, not st)).pack(side="right", padx=5)
                
                ctk.CTkButton(actions_frame, text="Editar", width=70, height=28, 
                             fg_color="#555555", font=("Arial Bold", 11)).pack(side="right", padx=5)

                ctk.CTkFrame(self.scroll_table, fg_color="#EEEEEE", height=1).pack(fill="x")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar usuários: {e}")

    def acao_toggle_admin(self, uid, novo_status):
        try:
            self.service.alterar_status_admin(uid, novo_status)
            self.carregar_usuarios()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def acao_toggle_ativo(self, uid, novo_status):
        msg = "Inativar este usuário impedirá seu acesso ao sistema. Continuar?" if not novo_status else "Reativar acesso deste usuário?"
        if messagebox.askyesno("Confirmação", msg):
            try:
                self.service.alterar_status_ativo(uid, novo_status)
                self.carregar_usuarios()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

class AdminCentralView:
    def __init__(self, master, usuario_dados):
        self.master = master
        self.usuario_dados = usuario_dados
        
        self.setup_ui()

    def setup_ui(self):
        # TabView Principal
        self.tabview = ctk.CTkTabview(self.master, segmented_button_selected_color="#0F8C75")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Adicionando Abas
        self.tabview.add("Configurações")
        self.tabview.add("Usuários")
        self.tabview.add("Auditoria") # Placeholder para Etapa 6

        # Renderizando Sub-Views
        AdminParametrosView(self.tabview.tab("Configurações"), self.usuario_dados)
        AdminUsuariosView(self.tabview.tab("Usuários"), self.usuario_dados)
        
        # Placeholder Auditoria
        ctk.CTkLabel(self.tabview.tab("Auditoria"), text="Módulo de Auditoria em desenvolvimento (Etapa 6)", font=("Arial", 16)).pack(pady=50)

def renderizar(container, usuario_dados):
    return AdminCentralView(container, usuario_dados)
