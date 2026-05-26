import customtkinter as ctk
from tkinter import messagebox
from src.modulos.ponto_parada.parecer.service import ParecerService
from src.core.shared.components.parameters_combo import CtkParametrosComboBox

class ParecerView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.ids_list = []

        self._construir_interface()

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Gerador de Parecer Técnico", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        bloco1 = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        bloco1.pack(fill="x", pady=10, padx=10)

        row1 = ctk.CTkFrame(bloco1, fg_color="transparent")
        row1.pack(fill="x", pady=(15, 5), padx=15)

        self.origem_combo = self._criar_param_combo(row1, "Origem", "Ponto de Parada", "ORIGEM_DEMANDA", width=300)

        self.tipo_parecer_combo = self._criar_param_combo(
            row1, 
            "Tipo do Parecer", 
            "Ponto de Parada", 
            "DECISAO_PARECER", 
            width=500, 
            command=self._atualizar_campos
        )
        self.tipo_parecer_combo.set("Deferido")
        
        self.processo_var = ctk.StringVar()
        self.processo_var.trace_add("write", self._converter_maiusculas)
        self._criar_entry(row1, "Nº do Processo", self.processo_var, width=450)

        row2 = ctk.CTkFrame(bloco1, fg_color="transparent")
        row2.pack(fill="x", pady=(5, 15), padx=15)

        # MODIFICAÇÃO: Solicitante agora busca nativamente e diretamente do banco (Modo Banco de Dados)
        self.solicitante_combo = self._criar_param_combo(row2, "Solicitante", "Ponto de Parada", "SOLICITANTE_PARECER", width=625)

        # MODIFICAÇÃO: Assunto agora busca nativamente e diretamente do banco (Modo Banco de Dados)
        self.assunto_combo = self._criar_param_combo(row2, "Assunto", "Ponto de Parada", "ASSUNTO_PARECER", width=625)

        bloco2 = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        bloco2.pack(fill="x", pady=10, padx=10)

        row3 = ctk.CTkFrame(bloco2, fg_color="transparent")
        row3.pack(fill="x", pady=(15, 5), padx=15)

        self.acao_combo = self._criar_param_combo(row3, "Ação", "Ponto de Parada", "ACAO_OS", width=625)
        
        # MODIFICAÇÃO: "Tipo de Item" usa componente moderno em Modo Estático, pois precisamos juntar as duas listas!
        lista_itens = self.service.obter_itens()
        if not lista_itens: lista_itens = ["Nenhum item cadastrado"]
        self.item_combo = self._criar_combobox(row3, "Tipo de Item", lista_itens, width=625)
        self.item_combo.set(lista_itens[0])

        row4 = ctk.CTkFrame(bloco2, fg_color="transparent")
        row4.pack(fill="x", pady=(5, 15), padx=15)

        self.endereco_var = ctk.StringVar()
        self._criar_entry(row4, "Endereço Completo", self.endereco_var, width=625)

        self.quantidade_var = ctk.StringVar()
        self._criar_entry(row4, "Quantidade (Por extenso: Um, Dois...)", self.quantidade_var, width=625)

        bloco3 = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        bloco3.pack(fill="x", pady=10, padx=10)

        row_id = ctk.CTkFrame(bloco3, fg_color="transparent")
        row_id.pack(fill="x", pady=15, padx=15)

        self.id_entry_var = ctk.StringVar()
        self._criar_entry(row_id, "Adicionar ID", self.id_entry_var, width=300)
        
        btn_add_id = ctk.CTkButton(row_id, text="➕ Adicionar ID", fg_color="#0F8C75", font=("Arial Bold", 13), height=35, command=self._adicionar_ids)
        btn_add_id.pack(side="left", padx=10, pady=(20,0)) 

        self.lista_ids_frame = ctk.CTkFrame(bloco3, fg_color="#FFFFFF", corner_radius=6)
        self.lista_ids_frame.pack(fill="x", padx=15, pady=(0, 15))
        self._renderizar_lista_ids() 

        self.frame_motivo = ctk.CTkFrame(self.scroll_frame, fg_color="#FFF0F0", corner_radius=10, border_width=1, border_color="#FFD6D6")
        ctk.CTkLabel(self.frame_motivo, text="Motivo do Indeferimento:", font=("Arial Bold", 13), text_color="#C21010").pack(anchor="w", padx=15, pady=(10, 0))
        self.entry_motivo = ctk.CTkTextbox(self.frame_motivo, height=100)
        self.entry_motivo.pack(fill="x", padx=15, pady=(5, 15))

        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=30)
        
        ctk.CTkLabel(footer_frame, text=f"Responsável: {self.usuario_logado}", text_color="gray", font=("Arial", 12)).pack(side="left", padx=10)
        ctk.CTkButton(footer_frame, text="📄 GERAR PARECER TÉCNICO", fg_color="#0F8C75", font=("Arial Bold", 16), height=50, width=300, command=self._acao_gerar_parecer).pack(side="right", padx=10)

    def _criar_entry(self, parent, label_text, variable, width):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        ctk.CTkEntry(container, textvariable=variable, width=width, height=35).pack(anchor="w", pady=(2,0))

    # MODIFICAÇÃO: Helper estático agora usa CtkParametrosComboBox
    def _criar_combobox(self, parent, label_text, values, width, command=None):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = CtkParametrosComboBox(container, values=values, width=width, height=35, command=command)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    def _criar_param_combo(self, parent, label_text, setor, campo, width, command=None):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        # Passa o comando diretamente para o construtor do componente moderno
        combo = CtkParametrosComboBox(container, setor=setor, campo=campo, width=width, height=35, command=command)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    def _atualizar_campos(self, escolha=None):
        # Validação blindada em caixa alta para interceptar o 'INDEFERIDO' do banco
        if self.tipo_parecer_combo.get().upper() == "INDEFERIDO":
            self.frame_motivo.pack(fill="x", pady=10, padx=10, before=self.scroll_frame.winfo_children()[-1])
        else:
            self.frame_motivo.pack_forget()

    def _converter_maiusculas(self, *args):
        val = self.processo_var.get()
        self.processo_var.set(val.upper())

    def _adicionar_ids(self):
        texto = self.id_entry_var.get().strip()
        if not texto: 
            messagebox.showwarning("Atenção", "Digite um ID antes de adicionar.")
            return
        
        partes = [p.strip() for p in texto.split(",") if p.strip()]
        for p in partes:
            if p not in self.ids_list:
                self.ids_list.append(p)
        
        self.id_entry_var.set("")
        self._renderizar_lista_ids()

    def _renderizar_lista_ids(self):
        for w in self.lista_ids_frame.winfo_children(): 
            w.destroy()
        
        if not self.ids_list:
            ctk.CTkLabel(self.lista_ids_frame, text="Nenhum ID adicionado ainda.", text_color="gray", font=("Arial", 12)).pack(pady=10)
            return

        container_badges = ctk.CTkFrame(self.lista_ids_frame, fg_color="transparent")
        container_badges.pack(fill="x", pady=10, padx=10)

        for idx, id_val in enumerate(self.ids_list):
            badge = ctk.CTkFrame(container_badges, fg_color="#0F8C75", corner_radius=15)
            badge.pack(side="left", padx=5, pady=5)
            
            ctk.CTkLabel(badge, text=f"ID: {id_val}", text_color="white", font=("Arial Bold", 12)).pack(side="left", padx=(10, 5))
            
            btn_remover = ctk.CTkButton(badge, text="X", width=20, height=20, fg_color="transparent", hover_color="#C21010", text_color="white", font=("Arial Bold", 12), command=lambda i=idx: self._remover_id(i))
            btn_remover.pack(side="right", padx=(0,5))

    def _remover_id(self, index):
        del self.ids_list[index]
        self._renderizar_lista_ids()

    def _acao_gerar_parecer(self):
        dados_form = {
            'origem': self.origem_combo.get(),
            'tipo': self.tipo_parecer_combo.get(),
            'processo': self.processo_var.get().strip(),
            'assunto': self.assunto_combo.get().strip(),
            'solicitante': self.solicitante_combo.get().strip(),
            'tipo_execucao': self.acao_combo.get().strip(),
            'item': self.item_combo.get().strip(),
            'endereco': self.endereco_var.get().strip(),
            'motivo': self.entry_motivo.get("1.0", "end").strip(),
            'quantidade': self.quantidade_var.get().strip()
        }

        sucesso, msg = self.service.processar_geracao_parecer(dados_form, self.ids_list, self.usuario_logado)
        
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            self._limpar_formulario()
        else:
            messagebox.showerror("Erro", msg)

    def _limpar_formulario(self):
        self.processo_var.set("")
        self.endereco_var.set("")
        self.quantidade_var.set("")
        self.entry_motivo.delete("1.0", "end")
        self.ids_list.clear()
        self._renderizar_lista_ids()
        self.id_entry_var.set("")

def renderizar(frame_destino, usuario_logado):
    return ParecerView(master=frame_destino, usuario_logado=usuario_logado)