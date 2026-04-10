import math
import os
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from src.modulos.quadro_horario.relatorios.service import RelatorioQuadroHorarioService

class RelatorioQuadroHorarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado, tipo_relatorio):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = RelatorioQuadroHorarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.is_admin = usuario_logado.get('is_admin', False) if isinstance(usuario_logado, dict) else False
        
        self.tipo_relatorio = tipo_relatorio 
        self.filtros_widgets = {} 
        self.dados_completos = []
        self.pagina_atual = 1
        self.itens_por_pagina = 25

        self.lista_linhas = self.service.buscar_sugestoes_linhas()
        self.lista_solicitantes = ["Todos", "AGEFIS", "AMC", "Cidadão", "CMF", "Comunidade", "Construtoras", "Empresas Operadoras", "Sindiônibus", "Outros"]
        self.lista_assuntos = ["Todos", "Aumento de frota para concurso", "Aumento de frota", "Redução de frota", "Execesso de demanda", "Remoção de empresas", "Retorno de Linha", "Mudança de frota", "Intervalo irregular", "Diversos--Requerimentos", "Inclusão de viagens", "Outros"]
        self.lista_eventos = ["Todos", "Cultural", "Esportivo", "Religioso", "Festival Junino", "Comunitário", "Festas", "Parada da Diversidade Sexual", "Fortal", "Academia Enem", "Caminhada com Maria", "Evangelizar", "Outros"]

        self._construir_interface()
        self.acao_buscar() 

    def _construir_interface(self):
        titulo = "Relatórios de Pareceres (Quadro de Horário)" if self.tipo_relatorio == "PARECER" else "Relatórios de Pesquisas (Quadro de Horário)"
        ctk.CTkLabel(self, text=titulo, font=("Arial Black", 22), text_color="#0F8C75").pack(side="top", pady=(10, 5), anchor="w", padx=20)

        filtros_container = ctk.CTkFrame(self, fg_color="#F2F2F2", corner_radius=8)
        filtros_container.pack(side="top", fill="x", padx=20, pady=0)

        grid_frame = ctk.CTkFrame(filtros_container, fg_color="transparent")
        grid_frame.pack(padx=10, pady=8, fill="x") 

        # =========================================================================
        # LAYOUT DINÂMICO DE FILTROS
        # =========================================================================
        if self.tipo_relatorio == "PARECER":
            self._add_filtro_grid(grid_frame, "Nº Parecer", "numero_parecer", 0, 0, width=150)
            self._add_filtro_grid(grid_frame, "Nº Processo", "processo", 0, 1, width=150)
            self._add_filtro_grid(grid_frame, "Responsável", "responsavel", 0, 2, width=200)
            self._add_autocomplete_grid(grid_frame, "Linha", "linha", 250, self.lista_linhas, 0, 3)

            self._add_combo_grid(grid_frame, "Solicitante", "solicitante", self.lista_solicitantes, 1, 0, width=150)
            self._add_combo_grid(grid_frame, "Assunto", "assunto", self.lista_assuntos, 1, 1, width=150)
            self._add_combo_grid(grid_frame, "Evento", "evento", self.lista_eventos, 1, 2, width=200)
            self._add_combo_grid(grid_frame, "Situação", "tipo", ["Todos", "DEFERIDO", "INDEFERIDO"], 1, 3, width=250)
        else:
            self._add_filtro_grid(grid_frame, "ID Pesquisa", "id", 0, 0, width=150)
            self._add_combo_grid(grid_frame, "Tipo", "tipo", ["Todos", "Tempo de Viagem", "Demanda"], 0, 1, width=200)
            self._add_filtro_grid(grid_frame, "Responsável", "responsavel", 0, 2, width=250)
            self._add_autocomplete_grid(grid_frame, "Linha", "linha", 300, self.lista_linhas, 0, 3)

        # Linha Comum para ambos (Datas e Botões Exportação)
        datas_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        datas_frame.grid(row=2, column=0, columnspan=4, pady=(15, 5), sticky="w", padx=5)

        self.usar_data_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(datas_frame, text="Período", variable=self.usar_data_var, font=("Arial Bold", 12)).pack(side="left", padx=(0, 10))
        
        wrapper_ini, self.data_inicio = self._criar_date_wrapper(datas_frame, 130)
        wrapper_ini.pack(side="left", padx=2)
        ctk.CTkLabel(datas_frame, text="à", text_color="#555", font=("Arial Bold", 12)).pack(side="left", padx=5)
        
        wrapper_fim, self.data_fim = self._criar_date_wrapper(datas_frame, 130)
        wrapper_fim.pack(side="left", padx=(2, 15))

        # Botões
        ctk.CTkButton(datas_frame, text="🔍 Buscar", fg_color="#0F8C75", font=("Arial Bold", 13), width=90, height=35, command=self.acao_buscar).pack(side="left", padx=(0, 5))
        ctk.CTkButton(datas_frame, text="🧹 Limpar", fg_color="#F24822", hover_color="#FF4319", font=("Arial Bold", 13), width=90, height=35, command=self.acao_limpar).pack(side="left", padx=(0, 5))
        ctk.CTkButton(datas_frame, text="📥 Excel", fg_color="#28A745", hover_color="#218838", font=("Arial Bold", 13), width=90, height=35, command=self.acao_exportar_excel).pack(side="left", padx=(0, 5))
        ctk.CTkButton(datas_frame, text="📄 PDF", fg_color="#DC3545", hover_color="#C82333", font=("Arial Bold", 13), width=90, height=35, command=self.acao_exportar_pdf).pack(side="left")

        # =========================================================================

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(15, 5))
        self.lbl_contador = ctk.CTkLabel(info_frame, text="A carregar...", font=("Arial Bold", 14), text_color="#333333")
        self.lbl_contador.pack(side="left")
        
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
        
        self.header_frame = ctk.CTkFrame(self.tabela_container, fg_color="#0F8C75", corner_radius=6, height=40)
        self.header_frame.pack(fill="x", padx=5, pady=(5, 0))
        self.header_frame.pack_propagate(False)
        
        self.scroll_tabela = ctk.CTkScrollableFrame(self.tabela_container, fg_color="transparent")
        self.scroll_tabela.pack(fill="both", expand=True, padx=5, pady=5)

        if self.tipo_relatorio == "PARECER":
            self.headers = ["Nº", "Situação", "Processo", "Assunto", "Solicitante", "Evento", "Linha(s)", "Data Evt", "Criação", "Resp", "Ações"]
            self.col_weights = [5, 8, 8, 12, 11, 10, 10, 8, 8, 8, 12] # Total = 100
        else:
            self.headers = ["ID", "Linha / Título", "Tipo de Análise", "Datas Coletadas", "Data Criação", "Responsável", "Ações"]
            self.col_weights = [6, 25, 14, 20, 12, 13, 10] # Total = 100

        current_relx = 0.0
        for j, h in enumerate(self.headers):
            w_pct = self.col_weights[j] / 100.0
            col_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
            col_frame.place(relx=current_relx, rely=0, relwidth=w_pct, relheight=1)
            ancora = "center" if h == "Ações" else "w"
            lbl = ctk.CTkLabel(col_frame, text=h, font=("Arial Bold", 12), text_color="white", anchor=ancora)
            lbl.pack(fill="both", expand=True, padx=5)
            current_relx += w_pct

    def _criar_date_wrapper(self, parent, width):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 12), background="#0F8C75", foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _add_filtro_grid(self, parent, label, key, row, col, width=120, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(frame, width=width, height=35, font=("Arial", 12))
        entry.pack(anchor="w")
        entry.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets[key] = entry

    def _add_combo_grid(self, parent, label, key, values, row, col, width=120, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, values=values, width=width, height=35, font=("Arial", 12), state="readonly")
        combo.set(values[0])
        combo.pack(anchor="w")
        combo.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets[key] = combo

    def _add_autocomplete_grid(self, parent, label, key, width, values, row, col, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, width=width, height=35, values=values, font=("Arial", 12), state="normal")
        combo.set("")
        combo.pack(anchor="w")
        combo._valores_originais = values
        def on_key(event):
            val = combo.get().lower()
            if not val: combo.configure(values=combo._valores_originais)
            else:
                filt = [v for v in combo._valores_originais if val in v.lower()]
                combo.configure(values=filt if filt else ["- Sem resultados -"])
        combo.bind("<KeyRelease>", on_key)
        self.filtros_widgets[key] = combo

    def _obter_texto_filtros(self):
        filtros_aplicados = []
        for key, widget in self.filtros_widgets.items():
            if hasattr(widget, "get"):
                val = widget.get().strip()
                if val and val != "Todos" and val != "- Sem resultados -":
                    filtros_aplicados.append(f"{key.capitalize()}: {val}")
        if self.usar_data_var.get():
            filtros_aplicados.append(f"Período: {self.data_inicio.get()} à {self.data_fim.get()}")
        return " | ".join(filtros_aplicados) if filtros_aplicados else "Nenhum (Todos os registros)"

    def acao_limpar(self):
        for key, widget in self.filtros_widgets.items():
            if hasattr(widget, "set") and isinstance(widget, ctk.CTkComboBox):
                if widget.cget("state") == "readonly": widget.set(widget.cget("values")[0])
                else: widget.set("")
            elif hasattr(widget, "delete"):
                widget.delete(0, "end") 
                
        self.usar_data_var.set(False) 
        self.acao_buscar() 

    def acao_buscar(self):
        filtros = {key: widget.get().strip() for key, widget in self.filtros_widgets.items() if widget.get().strip()}
        if self.usar_data_var.get():
            filtros['data_inicio'], filtros['data_fim'] = self.data_inicio.get_date(), self.data_fim.get_date()

        self.dados_completos = self.service.buscar_dados(self.tipo_relatorio, filtros)
        self.lbl_contador.configure(text=f"{len(self.dados_completos)} resultado(s) encontrados")
        self.pagina_atual = 1
        self._renderizar_pagina()

    def acao_exportar_excel(self):
        if not self.dados_completos: return messagebox.showwarning("Aviso", "Não há dados para exportar.")
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not filepath: return
        
        titulo = f"Relatório Estruturado de {self.tipo_relatorio} (SPR)"
        colunas = self.headers[:-1] 
        dados = [row[1:-1] for row in self.dados_completos] 
        
        s, msg = self.service.exportar_excel(filepath, dados, colunas, titulo, self._obter_texto_filtros())
        if s: os.startfile(filepath)
        else: messagebox.showerror("Erro", msg)

    def acao_exportar_pdf(self):
        if not self.dados_completos: return messagebox.showwarning("Aviso", "Não há dados para exportar.")
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not filepath: return
        
        titulo = f"Relatório Analítico de {self.tipo_relatorio} (SPR)"
        colunas = self.headers[:-1]
        dados = [row[1:-1] for row in self.dados_completos]
        
        s, msg = self.service.exportar_pdf(filepath, dados, colunas, titulo, self._obter_texto_filtros())
        if s: os.startfile(filepath)
        else: messagebox.showwarning("Informação", msg)

    def _acao_download(self, caminho):
        if not caminho or caminho == "None" or caminho == "-": return
        nome_arquivo = os.path.basename(caminho)
        destino = filedialog.asksaveasfilename(defaultextension=".docx", initialfile=nome_arquivo, title="Salvar Documento", filetypes=[("Word", "*.docx")])
        if destino:
            s, m = self.service.baixar_arquivo(caminho, destino)
            if s: messagebox.showinfo("Sucesso", m)
            else: messagebox.showerror("Erro", m)

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
            
            linha_frame = ctk.CTkFrame(self.scroll_tabela, fg_color=bg_color, corner_radius=6, height=45)
            linha_frame.pack(fill="x", pady=2, padx=2)
            linha_frame.pack_propagate(False)

            id_banco_invisivel = linha[0] 
            caminho_arquivo = linha[-1] 
            valores_exibicao = linha[1:-1]

            current_relx = 0.0

            for j, val in enumerate(valores_exibicao):
                texto = str(val) if val is not None else "-"
                cor_txt = "#333333"
                
                if self.tipo_relatorio == "PARECER" and j == 1: 
                    if "INDEFERIDO" in texto: cor_txt = "#D32F2F"
                    else: cor_txt = "#0F8C75"
                if self.tipo_relatorio == "PESQUISA" and j == 2:
                    cor_txt = "#F24822" if "Demanda" in texto else "#17A2B8"

                w_pct = self.col_weights[j] / 100.0
                
                limite_chars = int(self.col_weights[j] * 2.0) 
                texto_curto = texto[:limite_chars] + ".." if len(texto) > limite_chars else texto

                col_frame = ctk.CTkFrame(linha_frame, fg_color="transparent")
                col_frame.place(relx=current_relx, rely=0, relwidth=w_pct, relheight=1)

                lbl = ctk.CTkLabel(col_frame, text=texto_curto, text_color=cor_txt, font=("Arial", 12), anchor="w")
                lbl.pack(side="left", fill="both", expand=True, padx=5)
                
                current_relx += w_pct

            # COLUNA DE AÇÕES COM OS BOTÕES DINÂMICOS
            w_pct_acoes = self.col_weights[-1] / 100.0
            frame_coluna_acoes = ctk.CTkFrame(linha_frame, fg_color="transparent")
            frame_coluna_acoes.place(relx=current_relx, rely=0, relwidth=w_pct_acoes, relheight=1)

            frame_botoes = ctk.CTkFrame(frame_coluna_acoes, fg_color="transparent")
            frame_botoes.place(relx=0.5, rely=0.5, anchor="center")

            if self.tipo_relatorio == "PARECER" and caminho_arquivo and caminho_arquivo != "None":
                ctk.CTkButton(frame_botoes, text="📄", font=("Arial Bold", 16), fg_color="#0F8C75", hover_color="#0B6B59", width=34, height=30, command=lambda p=caminho_arquivo: self._abrir_word(p)).pack(side="left", padx=2)
                ctk.CTkButton(frame_botoes, text="⬇️", font=("Arial Bold", 15), fg_color="#17A2B8", hover_color="#138496", width=34, height=30, command=lambda p=caminho_arquivo: self._acao_download(p)).pack(side="left", padx=2)
            else:
                # Pesquisas não têm Word, apenas JSON (para visualização futura)
                ctk.CTkLabel(frame_botoes, text="-", width=76, anchor="center").pack(side="left", padx=2)

            if self.is_admin:
                ctk.CTkButton(frame_botoes, text="🗑️", anchor="center", font=("Arial", 16),fg_color="#D32F2F", hover_color="#B71C1C", width=34, height=30, command=lambda id_reg=id_banco_invisivel: self._acao_excluir(id_reg)).pack(side="left", padx=2)
                
    def _proxima_pagina(self): self.pagina_atual += 1; self._renderizar_pagina()
    def _pagina_anterior(self): self.pagina_atual -= 1; self._renderizar_pagina()

    def _abrir_word(self, caminho):
        sucesso, msg = self.service.abrir_arquivo(caminho)
        if not sucesso: messagebox.showerror("Erro", msg)

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
            if len(motivo) < 5: return messagebox.showwarning("Aviso", "Por favor, digite uma justificativa válida.")
            
            sucesso, msg = self.service.excluir_registro(self.tipo_relatorio, id_registro, motivo, self.usuario_logado)
            if sucesso:
                messagebox.showinfo("Excluído", msg)
                popup.destroy()
                self.acao_buscar()
            else: messagebox.showerror("Erro", msg)

        ctk.CTkButton(popup, text="Confirmar Exclusão e Gravar Log", fg_color="#D32F2F", hover_color="#B71C1C", font=("Arial Bold", 14), height=45, command=confirmar).pack(fill="x", padx=30, pady=20)

def renderizar(frame_destino, usuario_logado, tipo):
    return RelatorioQuadroHorarioView(master=frame_destino, usuario_logado=usuario_logado, tipo_relatorio=tipo)