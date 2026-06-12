import customtkinter as ctk
from tkinter import ttk, messagebox
from src.modulos.admin.linhas.service import LinhasService
from src.core.shared.colors import COLOR_PRIMARY, COLOR_SECONDARY, COLOR_BG, COLOR_TEXT, COLOR_WHITE,COLOR_HOVER

class AdminLinhasView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)
        
        self.service = LinhasService()
        self.linhas_atuais = []
        
        self._configurar_estilos()
        self.setup_ui()
        self.carregar_linhas()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Linhas.Treeview", background=COLOR_WHITE, rowheight=35, font=("Arial", 11), borderwidth=0)
        style.configure("Linhas.Treeview.Heading", font=("Arial Bold", 11), background=COLOR_BG, foreground=COLOR_TEXT)
        style.map("Linhas.Treeview", background=[('selected', COLOR_PRIMARY)], foreground=[('selected', 'white')])

    def setup_ui(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header_frame, text="Gestão de Linhas de Ônibus", font=("Arial Bold", 24), text_color=COLOR_TEXT).pack(side="left")
        ctk.CTkButton(header_frame, text="➕ Nova Linha", font=("Arial Bold", 13), height=38, fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, command=self.abrir_modal_linha).pack(side="right")

        # Filtro de Busca Rápida
        filtro_frame = ctk.CTkFrame(self.main_container, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        filtro_frame.pack(fill="x", pady=(0, 10))
        
        self.busca_var = ctk.StringVar()
        self.busca_var.trace_add("write", self.filtrar_lista)
        ctk.CTkEntry(filtro_frame, textvariable=self.busca_var, placeholder_text="🔍 Pesquisar por Código ou Nome da linha...", width=400, height=38, fg_color="#F9FAFB", border_color="#D1D5DB").pack(side="left", padx=15, pady=10)

        # Tabela (Treeview)
        tabela_frame = ctk.CTkFrame(self.main_container, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        tabela_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tabela_frame, columns=("id", "codigo", "nome", "status"), show="headings", style="Linhas.Treeview")
        self.tree.heading("id", text="ID")
        self.tree.heading("codigo", text="Código")
        self.tree.heading("nome", text="Nome da Linha")
        self.tree.heading("status", text="Status")
        
        self.tree.column("id", width=0, stretch=False)
        self.tree.column("codigo", width=100, anchor="center")
        self.tree.column("nome", width=500, anchor="w")
        self.tree.column("status", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(15,0), pady=15)
        scrollbar.pack(side="right", fill="y", padx=(0,15), pady=15)
        
        self.tree.bind("<Double-1>", lambda e: self.editar_linha_selecionada())

        # Rodapé com Ações
        rodape = ctk.CTkFrame(self.main_container, fg_color="transparent")
        rodape.pack(fill="x", pady=10)
        
        ctk.CTkButton(rodape, text="✏️ Editar Linha", font=("Arial Bold", 12), height=35, fg_color=COLOR_TEXT, hover_color=COLOR_HOVER, command=self.editar_linha_selecionada).pack(side="left", padx=5)
        ctk.CTkButton(rodape, text="🔄 Ativar / Inativar", font=("Arial Bold", 12), height=35, fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, command=self.toggle_status).pack(side="left", padx=5)

    def carregar_linhas(self):
        self.linhas_atuais = self.service.listar_linhas()
        self.filtrar_lista()

    def filtrar_lista(self, *args):
        termo = self.busca_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        
        for linha in self.linhas_atuais:
            texto_busca = f"{linha['codigo']} {linha['nome']}".lower()
            if termo in texto_busca:
                status = "🟢 ATIVA" if linha['is_ativo'] else "🔴 INATIVA"
                tag = 'ativo' if linha['is_ativo'] else 'inativo'
                self.tree.insert("", "end", values=(linha['id'], linha['codigo'], linha['nome'], status), tags=(tag,))
                
        self.tree.tag_configure('inativo', foreground="#999999")

    def abrir_modal_linha(self, linha=None):
        modal = ctk.CTkToplevel(self)
        titulo = "Editar Linha" if linha else "Nova Linha"
        modal.title(titulo)
        modal.geometry("500x350")
        modal.grab_set()
        
        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(container, text=titulo, font=("Arial Bold", 20), text_color=COLOR_PRIMARY).pack(pady=(0, 20))
        
        ctk.CTkLabel(container, text="Código da Linha (Ex: 015):", font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w")
        ent_codigo = ctk.CTkEntry(container, width=150, height=38, fg_color=COLOR_BG, border_color="#CCC")
        ent_codigo.pack(anchor="w", pady=(2, 15))
        
        ctk.CTkLabel(container, text="Nome da Linha:", font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w")
        ent_nome = ctk.CTkEntry(container, width=440, height=38, fg_color=COLOR_BG, border_color="#CCC")
        ent_nome.pack(anchor="w", pady=(2, 20))
        
        if linha:
            ent_codigo.insert(0, linha['codigo'])
            ent_nome.insert(0, linha['nome'])
            
        def salvar():
            cod = ent_codigo.get().strip()
            nom = ent_nome.get().strip()
            l_id = linha['id'] if linha else None
            
            sucesso, msg = self.service.salvar_linha(l_id, cod, nom.upper())
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                modal.destroy()
                self.carregar_linhas()
            else:
                messagebox.showerror("Erro", msg)
                
        ctk.CTkButton(container, text="Salvar Linha", fg_color=COLOR_PRIMARY, height=40, font=("Arial Bold", 14), command=salvar).pack(fill="x", pady=10)

    def editar_linha_selecionada(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione uma linha na tabela para editar.")
        item = self.tree.item(sel[0])['values']
        linha_obj = {"id": item[0], "codigo": str(item[1]).zfill(3), "nome": item[2]}
        self.abrir_modal_linha(linha_obj)

    def toggle_status(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione uma linha na tabela.")
        item = self.tree.item(sel[0])['values']
        l_id = item[0]
        status_atual = True if "ATIVA" in str(item[3]) else False
        
        novo_status = not status_atual
        acao = "INATIVAR" if not novo_status else "ATIVAR"
        
        if messagebox.askyesno("Confirmação", f"Deseja realmente {acao} esta linha?\n\nLinhas inativas param de aparecer nos formulários do sistema."):
            sucesso, msg = self.service.alterar_status(l_id, novo_status)
            if sucesso:
                self.carregar_linhas()
            else:
                messagebox.showerror("Erro", msg)