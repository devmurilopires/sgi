import customtkinter as ctk
from tkinter import messagebox
from src.modulos.admin.parametros.service import ParametrosService

COLOR_PRIMARY = "#0F8C75"

class AdminParametrosView:
    def __init__(self, master, usuario_dados):
        self.master = master
        self.usuario_dados = usuario_dados
        self.service = ParametrosService()
        self.color_accent = COLOR_PRIMARY
        
        self.config_map = {
            "Ponto de Parada": {
                "ACAO_OS": "Ação da OS",
                "ITEM_URBMIDIA": "Itens (Urbmídia)",
                "ITEM_MCMENSAGEM": "Itens (McMensagem)",
                "ORIGEM_DEMANDA": "Origem da Demanda",
                "SOLICITANTE_PARECER": "Solicitante",
                "ASSUNTO_PARECER": "Assunto"
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

    def _notificar_mudancas_globais(self):
        toplevel = self.master.winfo_toplevel()
        toplevel.event_generate("<<ParametrosAtualizados>>")

    def setup_ui(self):
        self.main_container = ctk.CTkFrame(self.master, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")
        
        ctk.CTkLabel(title_box, text="Configurações do Sistema", font=("Arial Bold", 28), text_color="#1A1A1A").pack(anchor="w")
        ctk.CTkLabel(title_box, text="Gerencie as listas de opções e parâmetros globais de cada setor", font=("Arial", 13), text_color="#666666").pack(anchor="w")

        layout_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        layout_container.pack(fill="both", expand=True)
        
        sidebar = ctk.CTkFrame(layout_container, width=280, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#EEEEEE")
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)
        
        ctk.CTkLabel(sidebar, text="SETORES", font=("Arial Bold", 11), text_color="#999999").pack(pady=(20, 10), padx=20, anchor="w")
        
        self.combo_setor = ctk.CTkComboBox(sidebar, values=list(self.config_map.keys()), 
                                         command=self.on_setor_change, width=240, height=38,
                                         fg_color="#F9F9F9", border_color="#DDDDDD", button_color=self.color_accent)
        self.combo_setor.pack(padx=20, pady=(0, 20))
        
        ctk.CTkLabel(sidebar, text="PARÂMETROS DISPONÍVEIS", font=("Arial Bold", 11), text_color="#999999").pack(pady=(10, 5), padx=20, anchor="w")
        
        self.scroll_campos = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.scroll_campos.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.botoes_campos = {}

        content = ctk.CTkFrame(layout_container, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)
        
        self.lbl_contexto = ctk.CTkLabel(content, text="Gerenciando: Setor > Campo", font=("Arial Bold", 18), text_color=self.color_accent)
        self.lbl_contexto.pack(anchor="w", pady=(0, 20))
        
        self.atualizar_menu_campos()

        add_frame = ctk.CTkFrame(content, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#EEEEEE")
        add_frame.pack(fill="x", pady=(0, 20))
        
        self.entry_valor = ctk.CTkEntry(add_frame, placeholder_text="Digite o novo valor para adicionar à lista...", 
                                       height=45, fg_color="#F9F9F9", border_color="#DDDDDD")
        self.entry_valor.pack(side="left", fill="x", expand=True, padx=20, pady=20)
        
        self.btn_add = ctk.CTkButton(add_frame, text="+ Adicionar", width=130, height=45, 
                                    fg_color=self.color_accent, font=("Arial Bold", 13),
                                    command=self.acao_adicionar)
        self.btn_add.pack(side="right", padx=20, pady=20)
        
        table_container = ctk.CTkFrame(content, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#EEEEEE")
        table_container.pack(fill="both", expand=True)
        
        self.scroll_lista = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.scroll_lista.pack(fill="both", expand=True, padx=15, pady=15)

    def atualizar_menu_campos(self):
        for b in self.botoes_campos.values(): b.destroy()
        self.botoes_campos = {}
        
        campos = self.config_map[self.setor_selecionado]
        for chave, rotulo in campos.items():
            btn = ctk.CTkButton(
                self.scroll_campos, text=rotulo, fg_color="transparent", text_color="#333333",
                anchor="w", hover_color="#F0F0F0", command=lambda k=chave: self.on_campo_change(k)
            )
            btn.pack(fill="x", pady=2)
            self.botoes_campos[chave] = btn
        
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

    def get_roteamento(self):
        """Mapeia dinamicamente a tabela do banco SGI v2.2 alvo."""
        return self.service.obter_roteamento(self.setor_selecionado, self.campo_selecionado)

    def atualizar_lista(self):
        for child in self.scroll_lista.winfo_children(): child.destroy()
        
        routing = self.get_roteamento()
        parametros = self.service.listar_parametros(routing)
        
        if not parametros:
            ctk.CTkLabel(self.scroll_lista, text="Lista vazia. Adicione opções acima.", text_color="#999").pack(pady=40)
            return

        for p in parametros:
            item_row = ctk.CTkFrame(self.scroll_lista, fg_color="transparent", height=45)
            item_row.pack(fill="x", pady=1)
            
            ctk.CTkLabel(item_row, text=p['valor'], font=("Arial", 14)).pack(side="left", padx=15)
            
            btns_row = ctk.CTkFrame(item_row, fg_color="transparent")
            btns_row.pack(side="right", padx=10)

            btn_edit = ctk.CTkButton(btns_row, text="Editar", width=70, height=26, fg_color="#555555", 
                                   command=lambda param=p: self.abrir_modal_edicao(param))
            btn_edit.pack(side="left", padx=5)

            btn_del = ctk.CTkButton(btns_row, text="Excluir", width=70, height=26, fg_color="#F24822", 
                                   command=lambda pid=p['id']: self.acao_excluir(pid))
            btn_del.pack(side="left", padx=5)
            
            ctk.CTkFrame(self.scroll_lista, fg_color="#EEEEEE", height=1).pack(fill="x")

    def abrir_modal_edicao(self, param):
        modal = ctk.CTkToplevel(self.master)
        modal.title("Editar Parâmetro")
        modal.geometry("400x250")
        modal.grab_set()
        modal.resizable(False, False)

        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (400 // 2)
        y = (modal.winfo_screenheight() // 2) - (250 // 2)
        modal.geometry(f"+{x}+{y}")

        ctk.CTkLabel(modal, text="Renomear Parâmetro", font=("Arial Bold", 16)).pack(pady=20)
        
        entry_edit = ctk.CTkEntry(modal, width=300, height=40)
        entry_edit.insert(0, param['valor'])
        entry_edit.pack(pady=10)
        entry_edit.focus_force()

        def salvar():
            novo_valor = entry_edit.get().strip()
            if not novo_valor: return
            
            routing = self.get_roteamento()
            sucesso, msg = self.service.editar_parametro(routing, param['id'], novo_valor)
            if sucesso:
                modal.destroy()
                self.atualizar_lista()
                self._notificar_mudancas_globais()
            else:
                messagebox.showerror("Erro", msg)

        btn_save = ctk.CTkButton(modal, text="Salvar", fg_color=self.color_accent, command=salvar)
        btn_save.pack(pady=20)

    def acao_adicionar(self):
        valor = self.entry_valor.get().strip()
        if not valor: return
        
        routing = self.get_roteamento()
        sucesso, msg = self.service.adicionar_parametro(routing, valor)
        
        if sucesso:
            self.entry_valor.delete(0, 'end')
            self.atualizar_lista()
            self._notificar_mudancas_globais()
        else:
            messagebox.showerror("Erro", msg)

    def acao_excluir(self, pid):
        if messagebox.askyesno("Confirmar", "Deseja excluir esta opção da lista?"):
            routing = self.get_roteamento()
            sucesso, msg = self.service.inativar_parametro(routing, pid)
            if sucesso:
                self.atualizar_lista()
                self._notificar_mudancas_globais()
            else:
                messagebox.showerror("Erro", msg)

def renderizar(container, usuario_dados):
    return AdminParametrosView(container, usuario_dados)