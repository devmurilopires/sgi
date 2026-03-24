import math
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from src.relatorios.service import RelatorioService

class RelatorioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado, tipo_relatorio):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = RelatorioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.is_admin = usuario_logado.get('is_admin', False) if isinstance(usuario_logado, dict) else False
        
        self.tipo_relatorio = tipo_relatorio 
        self.filtros_widgets = {} 
        self.dados_completos = []
        self.pagina_atual = 1
        self.itens_por_pagina = 25

        self._assuntos_padrao = ["Todos", "Solicitação de Implantação de Abrigo Metálico", "Solicitação de Implantação de Placa/Barrote", "Solicitação de Implantação de Placa/Poste", "Solicitação de Implantação de Parada Segura", "Solicitação de Implantação de Abrigo Concreto", "Solicitação de Transferência de Abrigo Metálico", "Solicitação de Transferência de Placa/Barrote", "Solicitação de Transferência de Placa/Poste", "Solicitação de Transferência de Parada Segura", "Solicitação de Transferência de Abrigo Concreto", "Solicitação de Remoção de Abrigo Metálico", "Solicitação de Remoção de Placa/Barrote", "Solicitação de Remoção de Placa/Poste", "Solicitação de Remoção de Parada Segura", "Solicitação de Remoção de Abrigo Concreto", "Solicitação de Substituição de Abrigo Metálico", "Solicitação de Substituição de Placa/Barrote", "Solicitação de Substituição de Placa/Poste", "Solicitação de Substituição de Parada Segura", "Solicitação de Substituição de Abrigo Concreto", "Solicitação de Manutenção de Abrigo Metálico", "Solicitação de Manutenção de Placa/Barrote", "Solicitação de Manutenção de Placa/Poste", "Solicitação de Manutenção de Parada Segura", "Solicitação de Manutenção de Abrigo Concreto", "Outros"]
        self._solicitantes_padrao = ["Todos", "AGEFIS - Agência de Fiscalização de Fortaleza", "ALECE - Assembléia Legislativa do Ceará", "AMC - Autarquia Municipal de Trânsito e Cidadania", "Assessoria Esportiva", "Ceará Sporting Club", "CGM - Controladoria e Ouvidoria Geral do Município", "Cidadão", "CITINOVA - fundação da Ciência, Tecnologia e Inovação de Fortaleza", "CMF - Câmara Municipal de Fortaleza", "Comunidade", "Construtoras", "Cootraps", "Empreendimento Comercial", "Empreendimento Residencial", "Empresas Operadoras", "Fortaleza Esporte Clube", "FUNCI - Fundação da Criança e da Família Cidadã", "GMF - Guarda Municipal de Fortaleza", "HABITAFOR - Secretaria Municipal de Desenvolvimento Habitacional de Fortaleza", "IMPARH - Instituto Municipal de Desenvolvimento de Recursos Humanos", "Imprensa", "Instituição de Ensino", "Instituição Religiosa", "Instituições Particulares", "IPEM - Instituro de Pesos e Medidas", "IPLANFOR - Instituto de Planejamento de Fortaleza", "IPM - Instituto de Previdência do Município", "Ministério Público", "Ouvidoria Etufor", "Ouvidoria Geral do Município de Fortaleza", "PGM - Procuradoria Geral do Município", "Polícia Militar do Ceará", "PROCON - Departamento Municipal de Proteção e Defesa dos Direitos do Consumidor", "SCDH - Secretaria Municipal de Cidadania e Direitos Humanos", "SCSP - Secretaria Municipal de Conservação e Serviços Públicos", "SDE - Secretaria Municipal de Desenvolvimento Econômico", "SECEL - Secretaria Municipal de Esporte e Lazer", "SECULTFOR - Secretaria Municipal de Cultura de Fortaleza", "SEFIN - Secretaria de Finanças", "SEGER - Secretaria Municipal de Gestão Regional", "SEINF - Secretaria Municipal de Infraestrutura", "SEJUV - Secretaria Municipal da Juventude", "SEPOG - Secretaria de Planejamento, Orçamento e Gestão", "SEPOG - Secretaria Municipal de Governo", "SER 1 - Secretaria Regional 1", "SER 2 - Secretaria Regional 2", "SER 3 - Secretaria Regional 3", "SER 4 - Secretaria Regional 4", "SER 5 - Secretaria Regional 5", "SER 6 - Secretaria Regional 6", "SER 7 - Secretaria Regional 7", "SER 8 - Secretaria Regional 8", "SER 9 - Secretaria Regional 9", "SER 10 - Secretaria Regional 10", "SER 11 - Secretaria Regional 11", "SER 12 - Secretaria Regional 12", "SERCE - Secretaria Regional Centro", "SESEC - Secretaria Municipal de Segurança Cidadã", "SETFOR - Secretaria Municipal de Turismo de Fortaleza", "SETRA - Secretaria Municipal de Trabalho, Desenvolvimento Social e Combate a fome", "SEUMA - Secretaria Municipal de Urbanismo e Meio Ambiente", "Sindiônibus", "SME - Secretaria Municipal de Educação", "SMS - Secretaria Municipal de Saúde", "TRANSITAR", "TRE - Tribunal Regional Eleitoral", "TRE - Tribunal Regional Eleitoral do Ceará", "URBFOR - Autarquia de Urbanismo e Paisagismo de Fortaleza", "DIARH", "DIASIS", "DICUSTO", "DIFIS", "DIMON", "DIOPE", "DIPRE", "DITEC", "DITRAN", "Ouvidoria", "Protocolo", "Vice Presidência", "Outros"]

        self._construir_interface()
        self.acao_buscar() 

    # CONSTRUÇÃO DA INTERFACE
    def _construir_interface(self):
        titulo = "Relatórios de Ordens de Serviço" if self.tipo_relatorio == "OS" else "Relatórios de Pareceres Técnicos"
        ctk.CTkLabel(self, text=titulo, font=("Arial Black", 22), text_color="#0F8C75").pack(side="top", pady=(10, 5), anchor="w", padx=20)

        filtros_container = ctk.CTkFrame(self, fg_color="#F2F2F2", corner_radius=8)
        filtros_container.pack(side="top", fill="x", padx=20, pady=0)

        grid_frame = ctk.CTkFrame(filtros_container, fg_color="transparent")
        grid_frame.pack(padx=10, pady=8, fill="x") 

        if self.tipo_relatorio == "OS":
            self._add_filtro_grid(grid_frame, "ID", "id", 0, 0, width=140)
            self._add_filtro_grid(grid_frame, "Nº OS", "numero_os", 0, 1, width=200)
            self._add_combo_grid(grid_frame, "Tipo OS", "tipo_os", ["Todos", "Implantação", "Transferência", "Remoção", "Substituição", "Manutenção"], 0, 2, width=130)
            self._add_combo_grid(grid_frame, "Pasta", "pasta", ["Todos", "URBMIDIA", "PROXIMA PARADA"], 0, 3, width=130)
            self._add_combo_grid(grid_frame, "Status", "concluida", ["Todos", "SIM", "NÃO", "NÃO AUTORIZADA"], 0, 4, width=320)
            self._add_combo_grid(grid_frame, "Tipo do Item", "tipo_item", ["Todos", "Placa/Poste", "Placa/Barrote", "Abrigo Metálico", "Abrigo Concreto", "Parada Segura"], 0, 5, width=180)

            self._add_filtro_grid(grid_frame, "Bairro", "bairro", 1, 0, width=140)
            self._add_filtro_grid(grid_frame, "Endereço", "endereco", 1, 1, width=200) 
            self._add_filtro_grid(grid_frame, "Responsável", "criado_por", 1, 2, width=130)
            self._add_combo_grid(grid_frame, "Origem", "origem", ["Todos", "SPU", "SISGEP"], 1, 3, width=130)
            
            datas_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
            datas_frame.grid(row=1, column=4, columnspan=2, pady=(5,0), sticky="e", padx=5)

        else:
            self._add_filtro_grid(grid_frame, "ID", "id", 0, 0, width=140)
            self._add_filtro_grid(grid_frame, "Nº Parecer", "numero_parecer", 0, 1, width=200)
            self._add_combo_grid(grid_frame, "Assunto", "assunto", self._assuntos_padrao, 0, 2, width=190)
            self._add_combo_grid(grid_frame, "Decisão", "tipo", ["Todos", "DEFERIDO", "INDEFERIDO"], 0, 3, width=220)
            self._add_combo_grid(grid_frame, "Solicitante", "solicitante", self._solicitantes_padrao, 0, 4, width=330, columnspan=2)

            self._add_filtro_grid(grid_frame, "Nº Processo", "processo", 1, 0, width=140)
            self._add_filtro_grid(grid_frame, "Endereço", "endereco", 1, 1, width=200) 
            self._add_filtro_grid(grid_frame, "Criado por", "criado_por", 1, 2, width=190)
            self._add_combo_grid(grid_frame, "Origem", "origem", ["Todos", "SPU", "SISGEP"], 1, 3, width=220)

            datas_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
            datas_frame.grid(row=1, column=4, columnspan=2, pady=(5,0), sticky="e", padx=5)

        self.usar_data_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(datas_frame, text="Período", variable=self.usar_data_var, font=("Arial Bold", 11)).pack(side="left", padx=(0, 10))
        self.data_inicio = DateEntry(datas_frame, date_pattern="dd/mm/yyyy", width=10, font=("Arial", 11))
        self.data_inicio.pack(side="left", padx=2)
        ctk.CTkLabel(datas_frame, text="à", text_color="#555", font=("Arial Bold", 11)).pack(side="left", padx=2)
        self.data_fim = DateEntry(datas_frame, date_pattern="dd/mm/yyyy", width=10, font=("Arial", 11))
        self.data_fim.pack(side="left", padx=(2, 15))

        # Botões de Buscar e Limpar 
        ctk.CTkButton(datas_frame, text="🔍 Buscar", fg_color="#0F8C75", font=("Arial Bold", 14), width=90, height=35, command=self.acao_buscar).pack(side="left", padx=(0, 5))
        ctk.CTkButton(datas_frame, text="🧹 Limpar", fg_color="#F24822", hover_color="#FF4319", font=("Arial Bold", 14), width=90, height=35, command=self.acao_limpar).pack(side="left")

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(15, 5))
        self.lbl_contador = ctk.CTkLabel(info_frame, text="0 resultados", font=("Arial Bold", 14), text_color="#333333")
        self.lbl_contador.pack(side="left")
        
        #Paginação
        pag_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        pag_frame.pack(side="right")
        self.btn_ant = ctk.CTkButton(pag_frame, text="<", width=35, height=30, fg_color="#0F8C75",hover_color="#0B6B59", font=("Arial Black", 14), command=self._pagina_anterior)
        self.btn_ant.pack(side="left", padx=5)
        self.lbl_paginacao = ctk.CTkLabel(pag_frame, text="1 / 1", font=("Arial Bold", 12))
        self.lbl_paginacao.pack(side="left", padx=10)
        self.btn_prox = ctk.CTkButton(pag_frame, text=">", width=35, height=30, fg_color="#0F8C75", hover_color="#0B6B59", font=("Arial Black", 14), command=self._proxima_pagina)
        self.btn_prox.pack(side="left", padx=5)

        self.tabela_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        self.tabela_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.header_frame = ctk.CTkFrame(self.tabela_container, fg_color="#0F8C75", corner_radius=6)
        self.header_frame.pack(fill="x", padx=5, pady=(5, 0))
        self.scroll_tabela = ctk.CTkScrollableFrame(self.tabela_container, fg_color="transparent")
        self.scroll_tabela.pack(fill="both", expand=True, padx=5, pady=5)

        if self.tipo_relatorio == "OS":
            self.headers = ["Nº", "Data", "ID(s)", "Origem", "Ação", "Item", "Endereço", "Status", "Pasta", "Criador", "Ações"]
            self.col_widths = [40, 75, 80, 60, 100, 110, 160, 120, 110, 90, 190] 
        else:
            self.headers = ["Nº", "Tipo", "Origem", "Processo", "Assunto", "ID(s)", "Solicitante", "Endereço", "Data", "Criador", "Ações"]
            self.col_widths = [40, 80, 60, 90, 140, 80, 120, 160, 75, 90, 190]

        for j, h in enumerate(self.headers):
            ancora = "center" if h == "Ações" else "w"
            lbl = ctk.CTkLabel(self.header_frame, text=h, width=self.col_widths[j], font=("Arial Bold", 12), text_color="white", anchor=ancora)
            lbl.pack(side="left", padx=5, pady=6)

    def _add_filtro_grid(self, parent, label, key, row, col, width=120, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(frame, width=width, height=32, font=("Arial", 12))
        entry.pack(anchor="w")
        entry.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets[key] = entry

    def _add_combo_grid(self, parent, label, key, values, row, col, width=120, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        state = "normal" if key in ["solicitante", "assunto"] else "readonly"
        combo = ctk.CTkComboBox(frame, values=values, width=width, height=32, font=("Arial", 12), state=state)
        combo.set(values[0])
        combo.pack(anchor="w")
        combo.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets[key] = combo

    def acao_limpar(self):
        """Limpa todos os campos, desmarca a data e busca tudo de novo."""
        for key, widget in self.filtros_widgets.items():
            if hasattr(widget, "set") and isinstance(widget, ctk.CTkComboBox):
                widget.set(widget.cget("values")[0]) # Volta para "Todos"
            elif hasattr(widget, "delete"):
                widget.delete(0, "end") # Apaga o texto
                
        self.usar_data_var.set(False) # Desmarca a caixinha de data
        self.acao_buscar() # Faz a busca com tudo limpo

    def acao_buscar(self):
        filtros = {key: widget.get().strip() for key, widget in self.filtros_widgets.items() if widget.get().strip()}
        if self.usar_data_var.get():
            filtros['data_inicio'], filtros['data_fim'] = self.data_inicio.get_date(), self.data_fim.get_date()

        self.dados_completos = self.service.buscar_dados(self.tipo_relatorio, filtros)
        self.lbl_contador.configure(text=f"{len(self.dados_completos)} resultado(s) encontrados")
        self.pagina_atual = 1
        self._renderizar_pagina()

    def _renderizar_pagina(self):
        for w in self.scroll_tabela.winfo_children(): w.destroy()
        total_itens = len(self.dados_completos)
        total_paginas = math.ceil(total_itens / self.itens_por_pagina) if total_itens > 0 else 1
        self.lbl_paginacao.configure(text=f"{self.pagina_atual} / {total_paginas}")
        self.btn_ant.configure(state="normal" if self.pagina_atual > 1 else "disabled")
        self.btn_prox.configure(state="normal" if self.pagina_atual < total_paginas else "disabled")

        if total_itens == 0: 
            ctk.CTkLabel(self.scroll_tabela, text="Nenhum dado encontrado para os filtros aplicados.", text_color="gray", font=("Arial", 14)).pack(pady=20)
            return

        inicio = (self.pagina_atual - 1) * self.itens_por_pagina
        fim = inicio + self.itens_por_pagina
        dados_da_pagina = self.dados_completos[inicio:fim]

        for i, linha in enumerate(dados_da_pagina):
            bg_color = "#F9F9F9" if i % 2 == 0 else "#FFFFFF"
            linha_frame = ctk.CTkFrame(self.scroll_tabela, fg_color=bg_color, corner_radius=6)
            linha_frame.pack(fill="x", pady=2, padx=2)

            id_banco_invisivel = linha[0] 
            caminho_arquivo = linha[-1] 
            valores_exibicao = linha[1:-1]

            for j, val in enumerate(valores_exibicao):
                texto = str(val) if val is not None else "-"
                cor_txt = "#333333"
                
                if self.tipo_relatorio == "OS" and j == 7: 
                    if "Aberta" in texto: cor_txt = "#D32F2F"
                    elif "Não Aut" in texto: cor_txt = "#E67E22"
                    elif "SIM" in texto: cor_txt = "#0F8C75"

                limite = int(self.col_widths[j] / 8)
                texto_curto = texto[:limite] + ".." if len(texto) > limite else texto

                lbl = ctk.CTkLabel(linha_frame, text=texto_curto, width=self.col_widths[j], text_color=cor_txt, font=("Arial", 12), anchor="w")
                lbl.pack(side="left", padx=5, pady=6)

            frame_coluna_acoes = ctk.CTkFrame(linha_frame, width=self.col_widths[-1], height=40, fg_color="transparent")
            frame_coluna_acoes.pack_propagate(False) 
            frame_coluna_acoes.pack(side="left", padx=5, pady=2)

            frame_botoes = ctk.CTkFrame(frame_coluna_acoes, fg_color="transparent")
            frame_botoes.place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkButton(frame_botoes, text="🔍", font=("Arial", 16), fg_color="#F24822", hover_color="#FF522B", width=45, height=32, command=lambda id_reg=id_banco_invisivel: self._acao_detalhes(id_reg)).pack(side="left", padx=3)

            if caminho_arquivo and caminho_arquivo != "-":
                ctk.CTkButton(frame_botoes, text="📄", font=("Arial Bold", 16), fg_color="#0F8C75", hover_color="#0B6B59", width=75, height=32, command=lambda p=caminho_arquivo: self._abrir_word(p)).pack(side="left", padx=3)
            else:
                ctk.CTkLabel(frame_botoes, text="-", width=75, anchor="center").pack(side="left", padx=3)

            if self.is_admin:
                ctk.CTkButton(frame_botoes, text="🗑️", anchor="center", font=("Arial", 16),fg_color="#D32F2F", hover_color="#B71C1C", width=45, height=32, command=lambda id_reg=id_banco_invisivel: self._acao_excluir(id_reg)).pack(side="left", padx=3)
                
    def _proxima_pagina(self):
        self.pagina_atual += 1
        self._renderizar_pagina()

    def _pagina_anterior(self):
        self.pagina_atual -= 1
        self._renderizar_pagina()

    def _abrir_word(self, caminho):
        sucesso, msg = self.service.abrir_arquivo(caminho)
        if not sucesso: messagebox.showerror("Erro de Leitura", msg)

    # POPUP DE DETALHES (E EDIÇÃO PARA ADMIN)
    def _acao_detalhes(self, id_registro):
        dados = self.service.buscar_detalhes_para_edicao(self.tipo_relatorio, id_registro)
        if not dados:
            messagebox.showerror("Erro", "Falha ao carregar detalhes do banco.")
            return

        popup = ctk.CTkToplevel(self)
        if self.is_admin:
            popup.title(f"Modo de Edição: {self.tipo_relatorio} Nº {id_registro}")
            titulo_tela = f"Editando {self.tipo_relatorio} Nº {id_registro}"
        else:
            popup.title(f"Detalhes: {self.tipo_relatorio} Nº {id_registro}")
            titulo_tela = f"Visualizando {self.tipo_relatorio} Nº {id_registro}"
            
        popup.geometry("700x750")
        popup.grab_set()

        ctk.CTkLabel(popup, text=titulo_tela, font=("Arial Black", 20), text_color="#0F8C75").pack(pady=15)
        
        scroll = ctk.CTkScrollableFrame(popup, fg_color="#F9F9F9", corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.entradas_edicao = {}
        for chave, valor in dados.items():
            linha = ctk.CTkFrame(scroll, fg_color="transparent")
            linha.pack(fill="x", pady=6, padx=10)
            ctk.CTkLabel(linha, text=chave + ":", font=("Arial Bold", 12), width=180, anchor="w").pack(side="left")
            
            valor_texto = str(valor) if valor and str(valor) != "None" else ""

            if not self.is_admin or "Nº" in chave or "Data Criação" in chave: 
                lbl_texto = valor_texto if valor_texto else "-"
                lbl = ctk.CTkLabel(linha, text=lbl_texto, font=("Arial", 12), anchor="w", justify="left", wraplength=450)
                lbl.pack(side="left", fill="x", expand=True)
                if self.is_admin: self.entradas_edicao[chave] = valor

            elif "Origem" in chave:
                cb = ctk.CTkComboBox(linha, values=["SPU", "SISGEP"], state="readonly", height=35)
                cb.set(valor_texto.upper() if valor_texto else "SPU")
                cb.pack(side="left", fill="x", expand=True)
                self.entradas_edicao[chave] = cb
            
            elif "Status Conclusão" in chave:
                cb = ctk.CTkComboBox(linha, values=["SIM", "NÃO", "NÃO AUTORIZADA"], state="readonly", height=35)
                cb.set(valor_texto.upper() if valor_texto else "NÃO")
                cb.pack(side="left", fill="x", expand=True)
                self.entradas_edicao[chave] = cb
            
            elif "Decisão" in chave:
                cb = ctk.CTkComboBox(linha, values=["DEFERIDO", "INDEFERIDO"], state="readonly", height=35)
                cb.set(valor_texto.upper() if valor_texto else "DEFERIDO")
                cb.pack(side="left", fill="x", expand=True)
                self.entradas_edicao[chave] = cb
            
            elif "Descrição" in chave or "Motivo" in chave:
                tb = ctk.CTkTextbox(linha, height=80, font=("Arial", 12), border_width=2)
                tb.insert("1.0", valor_texto)
                tb.pack(side="left", fill="x", expand=True)
                self.entradas_edicao[chave] = tb
            
            else:
                entry = ctk.CTkEntry(linha, height=35, font=("Arial", 12))
                entry.insert(0, valor_texto)
                entry.pack(side="left", fill="x", expand=True)
                self.entradas_edicao[chave] = entry

        def salvar():
            dados_novos = {}
            for k, v in self.entradas_edicao.items():
                if isinstance(v, ctk.CTkTextbox): dados_novos[k] = v.get("1.0", "end").strip()
                elif hasattr(v, 'get'): dados_novos[k] = v.get().strip()
                else: dados_novos[k] = v

            sucesso, msg = self.service.salvar_edicao(self.tipo_relatorio, id_registro, dados_novos)
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                popup.destroy()
                self.acao_buscar() 
            else:
                messagebox.showerror("Erro", msg)

        if self.is_admin:
            ctk.CTkButton(popup, text="💾 Salvar Alterações", fg_color="#0F8C75", font=("Arial Bold", 15), height=45, command=salvar).pack(fill="x", padx=40, pady=20)
        else:
            ctk.CTkButton(popup, text="Fechar", fg_color="gray", font=("Arial Bold", 15), height=45, command=popup.destroy).pack(fill="x", padx=40, pady=20)

    def _acao_excluir(self, id_registro):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Atenção: Excluir {self.tipo_relatorio} Nº {id_registro}")
        popup.geometry("500x350")
        popup.grab_set()

        ctk.CTkLabel(popup, text="EXCLUSÃO PERMANENTE", font=("Arial Black", 18), text_color="#D32F2F").pack(pady=(20, 5))
        ctk.CTkLabel(popup, text="Esta ação apagará o arquivo físico e o registro.\nEles ficarão visíveis apenas no Histórico.", font=("Arial", 12)).pack(pady=(0, 15))

        ctk.CTkLabel(popup, text="Motivo / Justificativa da exclusão:", font=("Arial Bold", 12)).pack(anchor="w", padx=30)
        txt_motivo = ctk.CTkTextbox(popup, height=80, font=("Arial", 12))
        txt_motivo.pack(fill="x", padx=30, pady=5)

        def confirmar():
            motivo = txt_motivo.get("1.0", "end").strip()
            if len(motivo) < 5:
                messagebox.showwarning("Aviso", "Por favor, digite uma justificativa válida.")
                return
            
            sucesso, msg = self.service.excluir_registro(self.tipo_relatorio, id_registro, motivo, self.usuario_logado)
            if sucesso:
                messagebox.showinfo("Excluído", msg)
                popup.destroy()
                self.acao_buscar()
            else:
                messagebox.showerror("Erro", msg)

        ctk.CTkButton(popup, text="Confirmar Exclusão e Gravar Log", fg_color="#D32F2F", hover_color="#B71C1C", font=("Arial Bold", 14), height=45, command=confirmar).pack(fill="x", padx=30, pady=20)

def renderizar(frame_destino, usuario_logado, tipo):
    return RelatorioView(master=frame_destino, usuario_logado=usuario_logado, tipo_relatorio=tipo)