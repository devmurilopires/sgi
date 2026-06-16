import customtkinter as ctk
from tkinter import messagebox
from src.modulos.ponto_parada.ordem_servico.service import OSService
from src.core.shared.components.parameters_combo import CtkParametrosComboBox
from src.core.shared.colors import COLOR_PRIMARY, COLOR_BG, COLOR_TEXT, COLOR_WHITE, COLOR_HOVER

class OSView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = OSService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.descricoes_acumuladas = []

        self._construir_interface()

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLOR_WHITE)
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- CABEÇALHO ---
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header_frame, text="Gerador de Ordem de Serviço", font=("Arial Black", 24), text_color=COLOR_PRIMARY).pack(side="left")
        
        self.modelo_combo = CtkParametrosComboBox(
            header_frame, 
            setor="Ponto de Parada", 
            campo="MODELO_OS", 
            width=150,
            command=self.ao_mudar_modelo
        )
        self.modelo_combo.pack(side="right", padx=10)
        
        ctk.CTkLabel(header_frame, text="Modelo:", font=("Arial Bold", 14)).pack(side="right", padx=5)

        # --- FORMULÁRIO ---
        form_frame = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_WHITE, corner_radius=10)
        form_frame.pack(fill="x", pady=10, padx=10)

        # Linha 1: Origem, Ação, Tipo de Item, Nº do Processo e ID
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(15, 5), padx=15)

        w_campos = 235
        self.origem_combo = self._criar_param_combo(row1, "Origem da Demanda", "Ponto de Parada", "ORIGEM", width=w_campos, side="left")
        self.tipo_os_combo = self._criar_param_combo(row1, "Ação da OS", "Ponto de Parada", "ACAO_OS", width=w_campos, side="left")
        self.tipo_item_combo = self._criar_param_combo(row1, "Tipo de Item", "Ponto de Parada", "ITEM_URBMIDIA", width=w_campos, side="left")
        
        self.processo_entry = self._criar_campo(row1, "Nº do Processo", width=w_campos, side="left")
        
        self.id_entry = self._criar_campo(row1, "ID do Ponto", width=w_campos, side="left")
        self.id_entry.bind("<FocusOut>", self.ao_sair_do_id)

        # Linha 2: Endereçamento
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5, padx=15)
        
        # Como agora _criar_campo tem maiúsculas automáticas, o usuário não consegue errar o preenchimento!
        self.endereco_entry = self._criar_campo(row2, "Endereço", width=300, side="left")
        self.numero_entry = self._criar_campo(row2, "Número", width=300, side="left")
        self.bairro_entry = self._criar_campo(row2, "Bairro", width=300, side="left")
        self.complemento_entry = self._criar_campo(row2, "Complemento", width=300, side="left")

        # Botão Adicionar
        ctk.CTkButton(form_frame, text="➕ Adicionar à Lista", fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, font=("Arial Bold", 14), height=40, command=self.adicionar_descricao).pack(pady=(10, 20))

        # --- TABELA ---
        tabela_container = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_WHITE, corner_radius=10)
        tabela_container.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(tabela_container, text="Itens da OS (Descrições Acumuladas)", font=("Arial Bold", 16), text_color=COLOR_TEXT).pack(anchor="w", padx=15, pady=(15,5))
        
        self.tabela_frame = ctk.CTkFrame(tabela_container, fg_color="transparent")
        self.tabela_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # --- RODAPÉ ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)

        self.criado_por_label = ctk.CTkLabel(footer_frame, text=f"Responsável: {self.usuario_logado}", font=("Arial", 12), text_color="gray")
        self.criado_por_label.pack(side="left", padx=10)

        ctk.CTkButton(footer_frame, text="✅ GERAR ORDEM DE SERVIÇO", fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, font=("Arial Bold", 16), height=50, width=300, command=self.acao_criar_os).pack(side="right", padx=10)

        self.ao_mudar_modelo(self.modelo_combo.get())

    # --- UTILITÁRIOS VISUAIS ---
    def _criar_campo(self, parent, label_text, width, side="top"):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, padx=10, fill="x")
        
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w")
        
        cor_padrao = "#E0E0E0" 
        var = ctk.StringVar()
        entry = ctk.CTkEntry(container, width=width, height=35, border_width=1, border_color=cor_padrao, textvariable=var)
        entry.pack(anchor="w", pady=(2,0))

        # Lógica Mágica: Força o UpperCase e muda a cor da borda ao mesmo tempo
        def ao_digitar(*args):
            texto = var.get()
            if texto != texto.upper():
                var.set(texto.upper())
                texto = texto.upper()
                
            if texto.strip():
                entry.configure(border_color=COLOR_PRIMARY) 
            else:
                entry.configure(border_color=cor_padrao)      

        # O trace_add fica "escutando" a variável sem precisar de clique no teclado.
        var.trace_add("write", ao_digitar)

        return entry
    
    def _criar_combobox(self, parent, label_text, width, values, side="top"):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w")
        combo = ctk.CTkComboBox(container, width=width, height=35, values=values, state="readonly")
        combo.pack(anchor="w", pady=(2,0))
        return combo

    def _criar_param_combo(self, parent, label_text, setor, campo, width, side="top"):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w")
        combo = CtkParametrosComboBox(container, setor=setor, campo=campo, width=width, height=35)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    # --- AÇÕES ---
    def ao_mudar_modelo(self, modelo_selecionado):
        itens = self.service.obter_itens_por_modelo(modelo_selecionado)
        if itens:
            self.tipo_item_combo.configure(values=itens)
            self.tipo_item_combo.set(itens[0])
        else:
            self.tipo_item_combo.configure(values=["Nenhum item cadastrado"])
            self.tipo_item_combo.set("Nenhum item cadastrado")

    def ao_sair_do_id(self, event=None):
        id_digitado = self.id_entry.get().strip().upper()
        if not id_digitado: return
        
        dados = self.service.consultar_endereco(id_digitado)
        
        # Limpa os campos antes de mais nada
        self.endereco_entry.delete(0, ctk.END)
        self.numero_entry.delete(0, ctk.END)
        self.bairro_entry.delete(0, ctk.END)
        self.complemento_entry.delete(0, ctk.END)

        if dados:
            # Preenche os dados automaticamente
            self.endereco_entry.insert(0, dados.get("endereco", ""))
            self.numero_entry.insert(0, dados.get("numero", ""))
            self.bairro_entry.insert(0, dados.get("bairro", ""))
            self.complemento_entry.insert(0, dados.get("complemento", ""))
        else:
            # BLINDAGEM: Se não existe, avisa o usuário e limpa o ID
            messagebox.showwarning(
                "ID Não Encontrado", 
                f"O ID '{id_digitado}' não está cadastrado no banco de dados.\n\n"
                "As Ordens de Serviço só podem ser geradas para Pontos de Parada oficiais.\n"
                "Por favor, acesse o módulo 'Gestão de Endereços' para cadastrar este Ponto primeiro."
            )
            self.id_entry.delete(0, ctk.END)
            # Foco volta para o ID para ele tentar novamente
            self.id_entry.focus_set()

    def adicionar_descricao(self):
        id_texto = self.id_entry.get().strip().upper()
        if not id_texto:
            messagebox.showerror("Atenção", "Digite o ID do Ponto primeiro.")
            return
            
        # DUPLA VALIDAÇÃO: Garante que o usuário não consiga burlar clicando em Add muito rápido
        if not self.service.consultar_endereco(id_texto):
            messagebox.showerror("Acesso Negado", "Este ID não está cadastrado. Utilize o módulo 'Gestão de Endereços' para cadastrar novos IDs.")
            return

        endereco = self.endereco_entry.get().upper()
        numero = self.numero_entry.get().upper()
        bairro = self.bairro_entry.get().upper()
        
        if not endereco or not numero or not bairro:
            messagebox.showerror("Atenção", "Os dados de endereço estão incompletos.")
            return

        tipo_os = self.tipo_os_combo.get().upper()
        tipo_item = self.tipo_item_combo.get().upper()
        complemento = self.complemento_entry.get().upper()

        endereco_formatado = f"{endereco}, Nº {numero} - BAIRRO {bairro}"
        if complemento: endereco_formatado += f" - {complemento}"
        
        descricao = f"{tipo_os} DE {tipo_item} NA {endereco_formatado}, CONFORME DESCRIÇÃO DO CROQUI EM ANEXO.".upper()
        
        self.descricoes_acumuladas.append({"id": id_texto, "descricao": descricao})
        self._renderizar_tabela()

    def _renderizar_tabela(self):
        for widget in self.tabela_frame.winfo_children():
            widget.destroy()
            
        for idx, item in enumerate(self.descricoes_acumuladas):
            linha = ctk.CTkFrame(self.tabela_frame, fg_color="white", corner_radius=6)
            linha.pack(fill="x", pady=2)
            
            ctk.CTkLabel(linha, text=f"ID: {item['id']}", font=("Arial Bold", 13), width=80, text_color=COLOR_PRIMARY).pack(side="left", padx=10)
            ctk.CTkLabel(linha, text=item["descricao"], font=("Arial", 12), justify="left", wraplength=600).pack(side="left", fill="x", expand=True, padx=10, pady=5)
            
            btn_excluir = ctk.CTkButton(linha, text="X", width=30, fg_color="transparent", hover_color="#FFE0E0", text_color="red", font=("Arial Bold", 14), command=lambda i=idx: self.excluir_da_tabela(i))
            btn_excluir.pack(side="right", padx=10)

    def excluir_da_tabela(self, index):
        if 0 <= index < len(self.descricoes_acumuladas):
            del self.descricoes_acumuladas[index]
            self._renderizar_tabela()

    def acao_criar_os(self):
        processo_digitado = self.processo_entry.get().strip().upper()
        if not processo_digitado:
            messagebox.showerror("Erro", "O preenchimento do Nº do Processo é obrigatório para gerar a OS.")
            return

        if not self.descricoes_acumuladas:
            messagebox.showerror("Erro", "Você precisa adicionar pelo menos um item à lista para gerar a OS.")
            return

        id_principal = self.descricoes_acumuladas[0]["id"]
        resposta = messagebox.askyesno("Verificação de Histórico", f"Você já consultou o histórico do ID {id_principal}?\n\nSe não, clique em NÃO para visualizar o histórico de Ordens de Serviço desse ponto.")
        if not resposta:
            historico = self.service.obter_historico_formatado(id_principal)
            messagebox.showinfo(f"Histórico ID {id_principal}", historico)
            return

        # Já não passamos os dados de endereço do formulário porque eles não serão atualizados aqui
        modelo_operacao = self.modelo_combo.get()
        doc_template = "dados/modelo_etufor_mcmensagem_pp.docx" if modelo_operacao == "McMensagem" else "dados/modelo_etufor_urbmidia_pp.docx"

        sucesso, mensagem = self.service.processar_criacao_os(
            descricoes_acumuladas=self.descricoes_acumuladas,
            modelo_operacao=modelo_operacao,
            modelo_escolhido=doc_template,
            tipo_os=self.tipo_os_combo.get(),
            tipo_item=self.tipo_item_combo.get(),
            processo=processo_digitado,
            usuario_logado=self.usuario_logado,
            origem_demanda=self.origem_combo.get() 
        )

        if sucesso:
            messagebox.showinfo("OS Gerada com Sucesso!", mensagem)
            self.processo_entry.delete(0, ctk.END)
            self.id_entry.delete(0, ctk.END)
            self.endereco_entry.delete(0, ctk.END)
            self.numero_entry.delete(0, ctk.END)
            self.bairro_entry.delete(0, ctk.END)
            self.complemento_entry.delete(0, ctk.END)
            self.descricoes_acumuladas.clear()
            self._renderizar_tabela()
        else:
            messagebox.showerror("Erro ao Gerar OS", mensagem)

def renderizar(frame_destino, usuario_logado):
    return OSView(master=frame_destino, usuario_logado=usuario_logado)