import customtkinter as ctk
from tkinter import messagebox
from src.parecer.service import ParecerService

class ParecerView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.ids_list = []

        # Listas Padrões
        self._assuntos_padrao = [
            "Solicitação de Implantação de Abrigo Metálico",
            "Solicitação de Implantação de Placa/Barrote",
            "Solicitação de Implantação de Placa/Poste",
            "Solicitação de Implantação de Parada Segura",
            "Solicitação de Implantação de Abrigo Concreto",
            "Solicitação de Transferência de Abrigo Metálico",
            "Solicitação de Transferência de Placa/Barrote",
            "Solicitação de Transferência de Placa/Poste",
            "Solicitação de Transferência de Parada Segura",
            "Solicitação de Transferência de Abrigo Concreto",
            "Solicitação de Remoção de Abrigo Metálico",
            "Solicitação de Remoção de Placa/Barrote",
            "Solicitação de Remoção de Placa/Poste",
            "Solicitação de Remoção de Parada Segura",
            "Solicitação de Remoção de Abrigo Concreto",
            "Solicitação de Substituição de Abrigo Metálico",
            "Solicitação de Substituição de Placa/Barrote",
            "Solicitação de Substituição de Placa/Poste",
            "Solicitação de Substituição de Parada Segura",
            "Solicitação de Substituição de Abrigo Concreto",
            "Solicitação de Manutenção de Abrigo Metálico",
            "Solicitação de Manutenção de Placa/Barrote",
            "Solicitação de Manutenção de Placa/Poste",
            "Solicitação de Manutenção de Parada Segura",
            "Solicitação de Manutenção de Abrigo Concreto",
            "Outros"
        ]


        self._solicitantes_padrao = [
        "AGEFIS - Agência de Fiscalização de Fortaleza", "ALECE - Assembléia Legislativa do Ceará", "AMC - Autarquia Municipal de Trânsito e Cidadania",
        "Assessoria Esportiva", "Ceará Sporting Club", "CGM - Controladoria e Ouvidoria Geral do Município",
        "Cidadão", "CITINOVA - fundação da Ciência, Tecnologia e Inovação de Fortaleza", "CMF - Câmara Municipal de Fortaleza",
        "Comunidade", "Construtoras", "Cootraps",
        "Empreendimento Comercial", "Empreendimento Residencial", "Empresas Operadoras",
        "Fortaleza Esporte Clube", "FUNCI - Fundação da Criança e da Família Cidadã", "GMF - Guarda Municipal de Fortaleza",
        "HABITAFOR - Secretaria Municipal de Desenvolvimento Habitacional de Fortaleza", "IMPARH - Instituto Municipal de Desenvolvimento de Recursos Humanos", "Imprensa",
        "Instituição de Ensino", "Instituição Religiosa", "Instituições Particulares",
        "IPEM - Instituro de Pesos e Medidas", "IPLANFOR - Instituto de Planejamento de Fortaleza", "IPM - Instituto de Previdência do Município",
        "Ministério Público", "Ouvidoria Etufor", "Ouvidoria Geral do Município de Fortaleza",
        "PGM - Procuradoria Geral do Município", "Polícia Militar do Ceará", "PROCON - Departamento Municipal de Proteção e Defesa dos Direitos do Consumidor",
        "SCDH - Secretaria Municipal de Cidadania e Direitos Humanos", "SCSP - Secretaria Municipal de Conservação e Serviços Públicos", "SDE - Secretaria Municipal de Desenvolvimento Econômico",
        "SECEL - Secretaria Municipal de Esporte e Lazer", "SECULTFOR - Secretaria Municipal de Cultura de Fortaleza", "SEFIN - Secretaria de Finanças",
        "SEGER - Secretaria Municipal de Gestão Regional", "SEINF - Secretaria Municipal de Infraestrutura", "SEJUV - Secretaria Municipal da Juventude",
        "SEPOG - Secretaria de Planejamento, Orçamento e Gestão", "SEPOG - Secretaria Municipal de Governo", "SER 1 - Secretaria Regional 1",
        "SER 2 - Secretaria Regional 2", "SER 3 - Secretaria Regional 3", "SER 4 - Secretaria Regional 4",
        "SER 5 - Secretaria Regional 5", "SER 6 - Secretaria Regional 6", "SER 7 - Secretaria Regional 7",
        "SER 8 - Secretaria Regional 8", "SER 9 - Secretaria Regional 9", "SER 10 - Secretaria Regional 10",
        "SER 11 - Secretaria Regional 11", "SER 12 - Secretaria Regional 12", "SERCE - Secretaria Regional Centro",
        "SESEC - Secretaria Municipal de Segurança Cidadã", "SETFOR - Secretaria Municipal de Turismo de Fortaleza", "SETRA - Secretaria Municipal de Trabalho, Desenvolvimento Social e Combate a fome",
        "SEUMA - Secretaria Municipal de Urbanismo e Meio Ambiente", "Sindiônibus", "SME - Secretaria Municipal de Educação",
        "SMS - Secretaria Municipal de Saúde", "TRANSITAR", "TRE - Tribunal Regional Eleitoral",
        "TRE - Tribunal Regional Eleitoral do Ceará", "URBFOR - Autarquia de Urbanismo e Paisagismo de Fortaleza",
        "DIARH", "DIASIS", "DICUSTO", "DIFIS", "DIMON", "DIOPE", "DIPRE", "DITEC", "DITRAN", "Ouvidoria", "Protocolo", "Vice Presidência", "Outros"
        ]
        
        self._tipos_padrao = ["Implantação", "Transferência", "Remoção", "Substituição", "Manutenção"]
        self._itens_padrao = ["Abrigo Metálico", "Placa/Barrote", "Placa/Poste","Parada Segura", "Abrigo Concreto"]

        self._construir_interface()

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- CABEÇALHO ---
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Gerador de Parecer Técnico", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        # DADOS BÁSICOS DO PROCESSO
        bloco1 = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        bloco1.pack(fill="x", pady=10, padx=10)

        # Origem, Tipo e Processo
        row1 = ctk.CTkFrame(bloco1, fg_color="transparent")
        row1.pack(fill="x", pady=(15, 5), padx=15)

        # Origem da Demanda
        self.origem_var = ctk.StringVar(value="SPU")
        self._criar_combobox(row1, "Origem", self.origem_var, ["SPU", "SISGEP"], width=130, state="readonly")

        self.tipo_parecer_var = ctk.StringVar(value="Deferido")
        self.tipo_parecer_var.trace_add("write", self._atualizar_campos) 
        
        self._criar_combobox(row1, "Tipo do Parecer", self.tipo_parecer_var, ["Deferido", "Indeferido"], width=200, state="readonly")
        
        self.processo_var = ctk.StringVar()
        self.processo_var.trace_add("write", self._converter_maiusculas)
        self._criar_entry(row1, "Nº do Processo", self.processo_var, width=450)

        # Solicitante e Assunto
        row2 = ctk.CTkFrame(bloco1, fg_color="transparent")
        row2.pack(fill="x", pady=(5, 15), padx=15)

        self.solicitante_var = ctk.StringVar()
        self._criar_combobox(row2, "Solicitante", self.solicitante_var, self._solicitantes_padrao, width=300)

        self.assunto_var = ctk.StringVar()
        self._criar_combobox(row2, "Assunto", self.assunto_var, self._assuntos_padrao, width=500)

        # DADOS TÉCNICOS E ENDEREÇO
        bloco2 = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        bloco2.pack(fill="x", pady=10, padx=10)

        # Tipo de Execução e Item
        row3 = ctk.CTkFrame(bloco2, fg_color="transparent")
        row3.pack(fill="x", pady=(15, 5), padx=15)

        self.tipo_exec_var = ctk.StringVar(value=self._tipos_padrao[0])
        self._criar_combobox(row3, "Ação", self.tipo_exec_var, self._tipos_padrao, width=500, state="readonly")

        self.item_var = ctk.StringVar(value=self._itens_padrao[0])
        self._criar_combobox(row3, "Tipo de Item", self.item_var, self._itens_padrao, width=300, state="readonly")

        # Endereço e Quantidade
        row4 = ctk.CTkFrame(bloco2, fg_color="transparent")
        row4.pack(fill="x", pady=(5, 15), padx=15)

        self.endereco_var = ctk.StringVar()
        self._criar_entry(row4, "Endereço Completo", self.endereco_var, width=500)

        self.quantidade_var = ctk.StringVar()
        self._criar_entry(row4, "Quantidade (Por extenso: Um, Dois...)", self.quantidade_var, width=300)

        # GESTÃO DE IDs DO PONTO
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

        # MOTIVO DE INDEFERIMENTO
        self.frame_motivo = ctk.CTkFrame(self.scroll_frame, fg_color="#FFF0F0", corner_radius=10, border_width=1, border_color="#FFD6D6")
        
        ctk.CTkLabel(self.frame_motivo, text="Motivo do Indeferimento:", font=("Arial Bold", 13), text_color="#C21010").pack(anchor="w", padx=15, pady=(10, 0))
        self.entry_motivo = ctk.CTkTextbox(self.frame_motivo, height=100)
        self.entry_motivo.pack(fill="x", padx=15, pady=(5, 15))

        # RODAPÉ: BOTÃO DE GERAR
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=30)
        
        ctk.CTkLabel(footer_frame, text=f"Responsável: {self.usuario_logado}", text_color="gray", font=("Arial", 12)).pack(side="left", padx=10)
        ctk.CTkButton(footer_frame, text="📄 GERAR PARECER TÉCNICO", fg_color="#0F8C75", font=("Arial Bold", 16), height=50, width=300, command=self._acao_gerar_parecer).pack(side="right", padx=10)

    # --- FUNÇÕES DE CONSTRUÇÃO DE UI ---
    def _criar_entry(self, parent, label_text, variable, width):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        ctk.CTkEntry(container, textvariable=variable, width=width, height=35).pack(anchor="w", pady=(2,0))

    def _criar_combobox(self, parent, label_text, variable, values, width, state="normal"):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(container, variable=variable, values=values, width=width, height=35, state=state)
        combo.pack(anchor="w", pady=(2,0))

    # --- LÓGICA DE INTERFACE ---
    def _atualizar_campos(self, *args):
        if self.tipo_parecer_var.get() == "Indeferido":
            self.frame_motivo.pack(fill="x", pady=10, padx=10, before=self.scroll_frame.winfo_children()[-1])
        else:
            self.frame_motivo.pack_forget()

    def _converter_maiusculas(self, *args):
        val = self.processo_var.get()
        self.processo_var.set(val.upper())

    # --- GESTÃO DA LISTA DE IDs ---
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

    # --- AÇÃO PRINCIPAL ---
    def _acao_gerar_parecer(self):
        dados_form = {
            'origem': self.origem_var.get(),
            'tipo': self.tipo_parecer_var.get(),
            'processo': self.processo_var.get().strip(),
            'assunto': self.assunto_var.get().strip(),
            'solicitante': self.solicitante_var.get().strip(),
            'tipo_execucao': self.tipo_exec_var.get().strip(),
            'item': self.item_var.get().strip(),
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