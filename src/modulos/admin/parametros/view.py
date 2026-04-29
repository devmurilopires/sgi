import customtkinter as ctk
from tkinter import messagebox
from src.modulos.admin.parametros.service import ParametrosService

class AdminParametrosView:
    def __init__(self, master, usuario_dados):
        self.master = master
        self.usuario_dados = usuario_dados
        self.service = ParametrosService()
        self.color_accent = "#0F8C75"
        
        # Mapeamento de Setores e Campos conforme solicitado
        self.config_map = {
            "Ponto de Parada": {
                "TIPO_ITEM": "Tipo de Item",
                "ACAO_OS": "Ação da OS",
                "ORIGEM_DEMANDA": "Origem da Demanda",
                "SOLICITANTE": "Solicitante"
            },
            "Itinerário": {
                "ORIGEM": "Origem",
                "EVENTO": "Nome do Evento",
                "SOLICITANTE": "Solicitante",
                "ASSUNTO": "Assunto"
            },
            "Quadro de Horário": {
                "SOLICITANTE": "Solicitante",
                "ASSUNTO": "Assunto",
                "EVENTO": "Evento",
                "ORIGEM": "Origem"
            }
        }
        
        self.setor_selecionado = "Ponto de Parada"
        self.campo_selecionado = "TIPO_ITEM"
        
        self.setup_ui()
        self.atualizar_lista()

    def setup_ui(self):
        # Container Principal com duas colunas
        self.main_container = ctk.CTkFrame(self.master, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # --- COLUNA ESQUERDA: SELEÇÃO DE SETOR E CAMPO ---
        sidebar = ctk.CTkFrame(self.main_container, width=250, fg_color="#FFFFFF", corner_radius=10)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)
        
        ctk.CTkLabel(sidebar, text="Selecione o Setor:", font=("Arial Bold", 14), text_color="#555555").pack(pady=(20, 10), padx=15, anchor="w")
        
        self.combo_setor = ctk.CTkComboBox(sidebar, values=list(self.config_map.keys()), command=self.on_setor_change, width=220)
        self.combo_setor.pack(padx=15, pady=5)
        
        ctk.CTkLabel(sidebar, text="Parâmetro:", font=("Arial Bold", 14), text_color="#555555").pack(pady=(20, 10), padx=15, anchor="w")
        
        self.scroll_campos = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", height=300)
        self.scroll_campos.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.botoes_campos = {}
        self.atualizar_menu_campos()

        # --- COLUNA DIREITA: GESTÃO DO PARÂMETRO ---
        content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)
        
        # Header do Conteúdo
        self.lbl_contexto = ctk.CTkLabel(content, text="Gerenciando: Setor > Campo", font=("Arial Bold", 18), text_color=COLOR_PRIMARY)
        self.lbl_contexto.pack(anchor="w", pady=(5, 15))
        
        # Formulário de Adição
        add_frame = ctk.CTkFrame(content, fg_color="#FFFFFF", corner_radius=10)
        add_frame.pack(fill="x", pady=(0, 15))
        
        self.entry_valor = ctk.CTkEntry(add_frame, placeholder_text="Digite o novo valor para a lista...", height=40)
        self.entry_valor.pack(side="left", fill="x", expand=True, padx=15, pady=15)
        
        self.btn_add = ctk.CTkButton(add_frame, text="+ Adicionar", width=120, height=40, fg_color=self.color_accent, command=self.acao_adicionar)
        self.btn_add.pack(side="right", padx=15, pady=15)
        
        # Tabela de Listagem
        table_container = ctk.CTkFrame(content, fg_color="#FFFFFF", corner_radius=10)
        table_container.pack(fill="both", expand=True)
        
        self.scroll_lista = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll_lista.pack(fill="both", expand=True, padx=10, pady=10)

    def atualizar_menu_campos(self):
        """Reconstrói a lista de botões de campos baseada no setor selecionado."""
        for b in self.botoes_campos.values(): b.destroy()
        self.botoes_campos = {}
        
        campos = self.config_map[self.setor_selecionado]
        for chave, rotulo in campos.items():
            btn = ctk.CTkButton(
                self.scroll_campos, 
                text=rotulo, 
                fg_color="transparent", 
                text_color="#333333",
                anchor="w",
                hover_color="#F0F0F0",
                command=lambda k=chave: self.on_campo_change(k)
            )
            btn.pack(fill="x", pady=2)
            self.botoes_campos[chave] = btn
        
        # Selecionar o primeiro por padrão se o atual não existir no novo setor
        if self.campo_selecionado not in campos:
            self.campo_selecionado = list(campos.keys())[0]
        self.destacar_campo_ativo()

    def destacar_campo_ativo(self):
        for k, b in self.botoes_campos.items():
            if k == self.campo_selecionado:
                b.configure(fg_color=self.color_accent, text_color="white")
            else:
                b.configure(fg_color="transparent", text_color="#333333")
        
        rotulo_campo = self.config_map[self.setor_selecionado][self.campo_selecionado]
        self.lbl_contexto.configure(text=f"Gerenciando: {self.setor_selecionado} > {rotulo_campo}")

    def on_setor_change(self, setor):
        self.setor_selecionado = setor
        self.atualizar_menu_campos()
        self.atualizar_lista()

    def on_campo_change(self, campo):
        self.campo_selecionado = campo
        self.destacar_campo_ativo()
        self.atualizar_lista()

    def atualizar_lista(self):
        for child in self.scroll_lista.winfo_children(): child.destroy()
        
        # A categoria no banco será um slug: SETOR_CAMPO
        categoria_slug = f"{self.setor_selecionado.upper().replace(' ', '_')}_{self.campo_selecionado}"
        
        try:
            parametros = self.service.listar_por_categoria(categoria_slug)
            
            if not parametros:
                ctk.CTkLabel(self.scroll_lista, text="Lista vazia. Adicione opções acima.", text_color="#999").pack(pady=40)
                return

            for p in parametros:
                item_row = ctk.CTkFrame(self.scroll_lista, fg_color="transparent", height=45)
                item_row.pack(fill="x", pady=1)
                
                ctk.CTkLabel(item_row, text=p['valor'], font=("Arial", 14)).pack(side="left", padx=15)
                
                btn_del = ctk.CTkButton(item_row, text="Excluir", width=70, height=26, fg_color="#F24822", 
                                       command=lambda pid=p['id']: self.acao_excluir(pid))
                btn_del.pack(side="right", padx=15)
                
                ctk.CTkFrame(self.scroll_lista, fg_color="#EEEEEE", height=1).pack(fill="x")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def acao_adicionar(self):
        valor = self.entry_valor.get().strip()
        if not valor: return
        
        categoria_slug = f"{self.setor_selecionado.upper().replace(' ', '_')}_{self.campo_selecionado}"
        try:
            self.service.adicionar_parametro(categoria_slug, valor)
            self.entry_valor.delete(0, 'end')
            self.atualizar_lista()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def acao_excluir(self, pid):
        if messagebox.askyesno("Confirmar", "Deseja excluir esta opção da lista?"):
            try:
                self.service.inativar_parametro(pid)
                self.atualizar_lista()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

def renderizar(container, usuario_dados):
    return AdminParametrosView(container, usuario_dados)
