import math
import os
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from src.modulos.itinerario.relatorios.service import RelatorioItinerarioService

# --- ESTILIZAÇÃO MODERNA PARA DROPDOWNS NORMAIS ---
MODERN_STYLE = {
    "fg_color": "#FFFFFF",
    "text_color": "#333333",
    "border_color": "#CCCCCC",
    "button_color": "#E0E0E0",
    "button_hover_color": "#CCCCCC",
    "dropdown_fg_color": "#FFFFFF",
    "dropdown_text_color": "#333333",
    "dropdown_hover_color": "#0F8C75"
}

# =====================================================================
# COMPONENTE: AUTOCOMPLETE MODERNO COM POPUP (WEB-LIKE)
# =====================================================================
class ModernAutocomplete(ctk.CTkFrame):
    def __init__(self, master, values, width=250, **kwargs):
        super().__init__(master, fg_color="transparent", width=width, height=35, **kwargs)
        self.pack_propagate(False)
        self.values = values
        
        self.entry = ctk.CTkEntry(self, width=width, height=35, fg_color="#FFFFFF", text_color="#333333", border_color="#CCCCCC")
        self.entry.pack(fill="both", expand=True)
        self.entry.insert(0, "")

        self.listbox_frame = None

        self.entry.bind("<KeyRelease>", self._on_keyrelease)
        self.entry.bind("<FocusOut>", self._on_focusout)
        self.entry.bind("<FocusIn>", self._on_keyrelease) 
        self.entry.bind("<Button-1>", self._on_keyrelease) 

    def _on_keyrelease(self, event):
        if event and getattr(event, 'keysym', '') in ['Up', 'Down', 'Return', 'Escape', 'Tab']: return
        
        val = self.entry.get().lower()
        hits = [item for item in self.values if val in item.lower()] if val else self.values
        self._show_listbox(hits)

    def _show_listbox(self, hits):
        self._hide_listbox()
        if not hits: return

        toplevel = self.winfo_toplevel()
        x = self.entry.winfo_rootx() - toplevel.winfo_rootx()
        y = self.entry.winfo_rooty() - toplevel.winfo_rooty() + self.entry.winfo_height()

        w = self.entry.winfo_width()
        h = min(150, len(hits)*25 + 5)

        self.listbox_frame = ctk.CTkFrame(toplevel, width=w, height=h, fg_color="#FFFFFF", border_width=1, border_color="#0F8C75", corner_radius=4)
        self.listbox_frame.pack_propagate(False)
        self.listbox_frame.place(x=x, y=y)

        self.listbox = tk.Listbox(self.listbox_frame, bg="#FFFFFF", fg="#333333", selectbackground="#0F8C75", selectforeground="#FFFFFF", bd=0, highlightthickness=0, font=("Arial", 11))
        self.listbox.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        for hit in hits: self.listbox.insert("end", hit)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

    def _on_select(self, event):
        if not self.listbox: return
        selection = self.listbox.curselection()
        if selection:
            item = self.listbox.get(selection[0])
            self.entry.delete(0, "end")
            self.entry.insert(0, item)
            self.entry.event_generate("<KeyRelease>")
        self._hide_listbox()

    def _hide_listbox(self):
        if hasattr(self, 'listbox_frame') and self.listbox_frame:
            self.listbox_frame.destroy()
            self.listbox_frame = None

    def _on_focusout(self, event):
        self.after(150, self._hide_listbox)

    def get(self): return self.entry.get()
    def set(self, value):
        self.entry.delete(0, "end")
        if value: self.entry.insert(0, value)

    # CORREÇÃO: add="+" obrigatório no CustomTkinter para não apagar eventos internos
    def bind(self, sequence, func, add="+"):
        self.entry.bind(sequence, func, add=add)

# =====================================================================
# VIEW PRINCIPAL 
# =====================================================================
class RelatorioItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado, tipo_relatorio):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = RelatorioItinerarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.is_admin = usuario_logado.get('is_admin', False) if isinstance(usuario_logado, dict) else False
        
        self.tipo_relatorio = tipo_relatorio 
        self.filtros_widgets = {} 
        self.dados_completos = []
        self.pagina_atual = 1
        self.itens_por_pagina = 25

        self._construir_interface()
        self.after(200, self.acao_buscar) 

    def _construir_interface(self):
        titulo = "Relatórios de Ordens de Serviço (Itinerário)" if self.tipo_relatorio == "OS" else "Relatórios de Pareceres (Itinerário)"
        ctk.CTkLabel(self, text=titulo, font=("Arial Black", 22), text_color="#0F8C75").pack(side="top", pady=(10, 5), anchor="w", padx=20)

        filtros_container = ctk.CTkFrame(self, fg_color="#F2F2F2", corner_radius=8)
        filtros_container.pack(side="top", fill="x", padx=20, pady=0)
        grid_frame = ctk.CTkFrame(filtros_container, fg_color="transparent")
        grid_frame.pack(padx=10, pady=8, fill="x") 

        self.lista_linhas = self.service.buscar_sugestoes("LINHAS")
        self.lista_empresas = self.service.buscar_sugestoes("EMPRESAS")
        self.lista_assuntos = ["Alteração de itinerário", "Desvio temporário de itinerário para Obra" , "Desvio temporário de itinerário para Evento", "Desvio temporário de itinerário para Corrida", "Implantação de linha", "Outros"]

        # =========================================================================
        # LAYOUT DE FILTROS COM OS NOVOS COMPONENTES
        # =========================================================================
        if self.tipo_relatorio == "OS":
            self._add_filtro_grid(grid_frame, "Nº OS", "numero_os", 0, 0, width=90)
            self._add_filtro_grid(grid_frame, "Nº Processo", "processo", 0, 1, width=120)
            self._add_combo_grid(grid_frame, "Tipo", "tipo_os", ["Todos", "Eventos", "Corrida", "Obras"], 0, 2, width=120)
            self._add_combo_grid(grid_frame, "Origem", "origem", ["Todos", "SISGEP", "SPU"], 0, 3, width=100)
            self._add_autocomplete_grid(grid_frame, "Empresa", "empresa", 180, self.lista_empresas, 0, 4)
            self._add_autocomplete_grid(grid_frame, "Linhas", "linha", 180, self.lista_linhas, 0, 5)
            self._add_filtro_grid(grid_frame, "Responsável", "responsavel", 0, 6, width=140)

            datas_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
            datas_frame.grid(row=1, column=0, columnspan=7, pady=(15,5), sticky="w", padx=5)

        else:
            self._add_filtro_grid(grid_frame, "Nº Processo", "processo", 0, 0, width=200)
            self._add_filtro_grid(grid_frame, "Nº Parecer", "numero_parecer", 0, 1, width=130)
            self._add_autocomplete_grid(grid_frame, "Linha", "linha", 270, self.lista_linhas, 0, 2)
            self._add_filtro_grid(grid_frame, "Responsável", "responsavel", 0, 3, width=260)
            self._add_combo_grid(grid_frame, "Origem", "origem", ["Todos", "SISGEP", "SPU"], 0, 4, width=110)

            self._add_filtro_grid(grid_frame, "Solicitante", "solicitante", 1, 0, width=200)
            self._add_combo_grid(grid_frame, "Situação", "tipo", ["Todos", "DEFERIDO", "INDEFERIDO"], 1, 1, width=130)
            self._add_filtro_grid(grid_frame, "Endereço", "endereco", 1, 2, width=270)
            self._add_autocomplete_grid(grid_frame, "Assunto", "assunto", 260, self.lista_assuntos, 1, 3)

            datas_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
            datas_frame.grid(row=2, column=0, columnspan=5, pady=(15,5), sticky="w", padx=5)

        # --- DATAS E BOTÕES ---
        self.usar_data_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(datas_frame, text="Filtrar por Período", variable=self.usar_data_var, font=("Arial Bold", 12)).pack(side="left", padx=(0, 15))
        
        wrapper_ini, self.data_inicio = self._criar_date_wrapper(datas_frame, 150)
        wrapper_ini.pack(side="left", padx=2)
        ctk.CTkLabel(datas_frame, text="à", text_color="#555", font=("Arial Bold", 12)).pack(side="left", padx=5)
        wrapper_fim, self.data_fim = self._criar_date_wrapper(datas_frame, 150)
        wrapper_fim.pack(side="left", padx=(2, 15))

        ctk.CTkButton(datas_frame, text="🔍 Buscar", fg_color="#0F8C75", font=("Arial Bold", 13), width=90, height=35, command=self.acao_buscar).pack(side="left", padx=(0, 5))
        ctk.CTkButton(datas_frame, text="🧹 Limpar", fg_color="#F24822", hover_color="#FF4319", font=("Arial Bold", 13), width=90, height=35, command=self.acao_limpar).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(datas_frame, text="📥 Excel", fg_color="#28A745", hover_color="#218838", font=("Arial Bold", 13), width=90, height=35, command=self.acao_exportar_excel).pack(side="left", padx=(0, 5))
        ctk.CTkButton(datas_frame, text="📄 PDF", fg_color="#DC3545", hover_color="#C82333", font=("Arial Bold", 13), width=90, height=35, command=self.acao_exportar_pdf).pack(side="left")

        # CONTADORES E PAGINAÇÃO
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

        # TABELA RESPONSIVA
        self.tabela_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        self.tabela_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        self.header_frame = ctk.CTkFrame(self.tabela_container, fg_color="#0F8C75", corner_radius=6, height=40)
        self.header_frame.pack(fill="x", padx=5, pady=(5, 0))
        self.header_frame.pack_propagate(False)
        
        self.scroll_tabela = ctk.CTkScrollableFrame(self.tabela_container, fg_color="transparent")
        self.scroll_tabela.pack(fill="both", expand=True, padx=5, pady=5)

        if self.tipo_relatorio == "OS":
            self.headers = ["Nº OS", "Processo", "Tipo", "Origem", "Empresa", "Linhas", "Criador", "Data", "Ações"]
            self.col_weights = [6, 9, 8, 7, 16, 14, 11, 10, 19] # Total: 100%
        else:
            self.headers = ["Nº Par", "Processo", "Situação", "Origem", "Assunto", "Solicitante", "Linha", "Endereço", "Criador", "Ações"]
            self.col_weights = [5, 8, 8, 7, 12, 12, 8, 14, 10, 16] # Total: 100%

        current_relx = 0.0
        for j, h in enumerate(self.headers):
            w_pct = self.col_weights[j] / 100.0
            col_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
            col_frame.place(relx=current_relx, rely=0, relwidth=w_pct, relheight=1)
            
            ancora = "center" if h == "Ações" else "w"
            lbl = ctk.CTkLabel(col_frame, text=h, font=("Arial Bold", 12), text_color="white", anchor=ancora)
            lbl.pack(fill="both", expand=True, padx=5)
            current_relx += w_pct

    # --- HELPERS UI MODERNOS ---
    def _add_filtro_grid(self, parent, label, key, row, col, width=120, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(frame, width=width, height=35, font=("Arial", 12), fg_color="#FFFFFF", text_color="#333333", border_color="#CCCCCC")
        entry.pack(anchor="w")
        entry.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets[key] = entry

    def _add_combo_grid(self, parent, label, key, values, row, col, width=120, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, values=values, width=width, height=35, font=("Arial", 12), state="readonly", **MODERN_STYLE)
        combo.set(values[0])
        combo.pack(anchor="w")
        self.filtros_widgets[key] = combo

    def _add_autocomplete_grid(self, parent, label, key, width, values, row, col, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        
        # APLICA O AUTOCOMPLETE MODERNO AQUI TAMBÉM
        autocomplete = ModernAutocomplete(frame, values=values, width=width)
        autocomplete.pack(anchor="w")
        autocomplete.bind("<Return>", lambda e: self.acao_buscar())
        
        self.filtros_widgets[key] = autocomplete

    def _criar_date_wrapper(self, parent, width):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 12), background="#0F8C75", foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _obter_texto_filtros(self):
        filtros_aplicados = []
        for key, widget in self.filtros_widgets.items():
            val = widget.get().strip()
            if val and val != "Todos" and val != "- Sem resultados -":
                filtros_aplicados.append(f"{key.capitalize()}: {val}")
        if self.usar_data_var.get():
            filtros_aplicados.append(f"Período: {self.data_inicio.get()} à {self.data_fim.get()}")
        return " | ".join(filtros_aplicados) if filtros_aplicados else "Nenhum (Todos os registros)"

    def acao_limpar(self):
        for key, widget in self.filtros_widgets.items():
            if isinstance(widget, ctk.CTkComboBox):
                if widget.cget("state") == "readonly": widget.set(widget.cget("values")[0])
                else: widget.set("")
            elif isinstance(widget, ModernAutocomplete):
                widget.set("")
            elif isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
        self.usar_data_var.set(False)
        self.acao_buscar()

    def acao_buscar(self):
        filtros = {key: widget.get().strip() for key, widget in self.filtros_widgets.items() if widget.get().strip()}
        if self.usar_data_var.get():
            filtros['data_inicio'], filtros['data_fim'] = self.data_inicio.get_date(), self.data_fim.get_date()
        
        self.dados_completos = self.service.buscar_dados(self.tipo_relatorio, filtros)
        self.lbl_contador.configure(text=f"{len(self.dados_completos)} resultado(s)")
        self.pagina_atual = 1
        self._renderizar_pagina()

    def acao_exportar_excel(self):
        if not self.dados_completos: return messagebox.showwarning("Aviso", "Não há dados para exportar.")
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not filepath: return
        
        titulo = f"Relatório Estruturado de {self.tipo_relatorio} (Itinerário)"
        colunas = self.headers[:-1]
        dados = [row[1:-1] for row in self.dados_completos]
        
        sucesso, msg = self.service.exportar_excel(filepath, dados, colunas, titulo, self._obter_texto_filtros())
        if sucesso: os.startfile(filepath)
        else: messagebox.showerror("Erro", msg)

    def acao_exportar_pdf(self):
        if not self.dados_completos: return messagebox.showwarning("Aviso", "Não há dados para exportar.")
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not filepath: return
        
        titulo = f"Relatório Analítico de {self.tipo_relatorio} (Itinerário)"
        colunas = self.headers[:-1]
        dados = [row[1:-1] for row in self.dados_completos]
        
        sucesso, msg = self.service.exportar_pdf(filepath, dados, colunas, titulo, self._obter_texto_filtros())
        if sucesso: os.startfile(filepath)
        else: messagebox.showwarning("Informação", msg) 

    def _acao_download(self, caminho):
        if not caminho or caminho == "None": return
        nome_arquivo = os.path.basename(caminho)
        destino = filedialog.asksaveasfilename(defaultextension=".docx", initialfile=nome_arquivo, title="Salvar Ficheiro", filetypes=[("Word", "*.docx")])
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
            ctk.CTkLabel(self.scroll_tabela, text="Nenhum dado encontrado para os filtros ativos.", text_color="gray", font=("Arial", 14)).pack(pady=20)
            return

        inicio = (self.pagina_atual - 1) * self.itens_por_pagina
        for i, linha in enumerate(self.dados_completos[inicio : inicio + self.itens_por_pagina]):
            linha_frame = ctk.CTkFrame(self.scroll_tabela, fg_color="#F9F9F9" if i % 2 == 0 else "#FFFFFF", corner_radius=6, height=45)
            linha_frame.pack(fill="x", pady=2, padx=2)
            linha_frame.pack_propagate(False)

            id_banco_invisivel, caminho_arquivo = linha[0], linha[-1] 
            valores_exibicao = linha[1:-1] 

            current_relx = 0.0
            
            for j, val in enumerate(valores_exibicao):
                texto = str(val) if val and str(val) != "None" else "-"
                cor_txt = "#333333"
                
                if self.tipo_relatorio == "PARECER" and j == 2: 
                    cor_txt = "#D32F2F" if "INDEFERIDO" in texto else "#0F8C75"
                if self.tipo_relatorio == "OS" and j == 2: 
                    texto = texto.upper()

                w_pct = self.col_weights[j] / 100.0
                limite_chars = int(self.col_weights[j] * 1.8) 
                texto_curto = texto[:limite_chars] + ".." if len(texto) > limite_chars else texto

                col_frame = ctk.CTkFrame(linha_frame, fg_color="transparent")
                col_frame.place(relx=current_relx, rely=0, relwidth=w_pct, relheight=1)

                lbl = ctk.CTkLabel(col_frame, text=texto_curto, text_color=cor_txt, font=("Arial", 12), anchor="w")
                lbl.pack(side="left", fill="both", expand=True, padx=5)
                
                current_relx += w_pct

            w_pct_acoes = self.col_weights[-1] / 100.0
            frame_acoes = ctk.CTkFrame(linha_frame, fg_color="transparent")
            frame_acoes.place(relx=current_relx, rely=0, relwidth=w_pct_acoes, relheight=1)

            fb = ctk.CTkFrame(frame_acoes, fg_color="transparent")
            fb.place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkButton(fb, text="🔍", font=("Arial", 16), fg_color="#F24822", hover_color="#FF522B", width=30, height=28, command=lambda id_reg=id_banco_invisivel: self._acao_detalhes(id_reg)).pack(side="left", padx=2)
            
            if caminho_arquivo and caminho_arquivo != "None":
                ctk.CTkButton(fb, text="📄", font=("Arial Bold", 16), fg_color="#0F8C75", hover_color="#0B6B59", width=30, height=28, command=lambda p=caminho_arquivo: self._abrir_word(p)).pack(side="left", padx=2)
                ctk.CTkButton(fb, text="⬇️", font=("Arial Bold", 14), fg_color="#17A2B8", hover_color="#138496", width=30, height=28, command=lambda p=caminho_arquivo: self._acao_download(p)).pack(side="left", padx=2)
            else:
                ctk.CTkLabel(fb, text="-", width=64).pack(side="left", padx=2)
            
            if self.is_admin:
                ctk.CTkButton(fb, text="🗑️", font=("Arial", 16), fg_color="#D32F2F", hover_color="#B71C1C", width=30, height=28, command=lambda id_reg=id_banco_invisivel: self._acao_excluir(id_reg)).pack(side="left", padx=2)

    def _proxima_pagina(self): self.pagina_atual += 1; self._renderizar_pagina()
    def _pagina_anterior(self): self.pagina_atual -= 1; self._renderizar_pagina()
    
    def _abrir_word(self, caminho):
        s, m = self.service.abrir_arquivo(caminho)
        if not s: messagebox.showerror("Erro", m)

    def _acao_detalhes(self, id_registro):
        dados = self.service.buscar_detalhes(self.tipo_relatorio, id_registro)
        if not dados: return
        popup = ctk.CTkToplevel(self)
        popup.title(f"Detalhes {self.tipo_relatorio} Nº {id_registro}")
        popup.geometry("700x700")
        popup.grab_set()
        ctk.CTkLabel(popup, text=f"Detalhes: {self.tipo_relatorio} Nº {id_registro}", font=("Arial Black", 20), text_color="#0F8C75").pack(pady=15)
        scroll = ctk.CTkScrollableFrame(popup, fg_color="#F9F9F9", corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        for k, v in dados.items():
            linha = ctk.CTkFrame(scroll, fg_color="transparent")
            linha.pack(fill="x", pady=6, padx=10)
            ctk.CTkLabel(linha, text=k + ":", font=("Arial Bold", 12), width=180, anchor="w").pack(side="left")
            valor = str(v) if v and str(v) != "None" else "-"
            
            if "Motivo" in k or "Linhas" in k or "Empresas" in k:
                tb = ctk.CTkTextbox(linha, height=70, font=("Arial", 12))
                tb.insert("1.0", valor); tb.configure(state="disabled")
                tb.pack(side="left", fill="x", expand=True)
            else:
                ctk.CTkLabel(linha, text=valor, font=("Arial", 12), anchor="w", justify="left", wraplength=450).pack(side="left", fill="x", expand=True)
                
        ctk.CTkButton(popup, text="Fechar", fg_color="gray", font=("Arial Bold", 15), height=45, command=popup.destroy).pack(fill="x", padx=40, pady=20)

    def _acao_excluir(self, id_registro):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Excluir {self.tipo_relatorio}")
        popup.geometry("500x350")
        popup.grab_set()
        ctk.CTkLabel(popup, text="EXCLUSÃO PERMANENTE", font=("Arial Black", 18), text_color="#D32F2F").pack(pady=(20, 5))
        ctk.CTkLabel(popup, text="Esta ação moverá o documento para a Lixeira Global.", font=("Arial", 12)).pack(pady=(0, 15))
        ctk.CTkLabel(popup, text="Motivo da exclusão:", font=("Arial Bold", 12)).pack(anchor="w", padx=30)
        txt = ctk.CTkTextbox(popup, height=80, font=("Arial", 12))
        txt.pack(fill="x", padx=30, pady=5)

        def confirmar():
            motivo = txt.get("1.0", "end").strip()
            if len(motivo) < 5: return messagebox.showwarning("Aviso", "Digite uma justificativa.")
            s, m = self.service.excluir_registro(self.tipo_relatorio, id_registro, motivo, self.usuario_logado)
            if s:
                messagebox.showinfo("Sucesso", m)
                popup.destroy()
                self.acao_buscar()
            else: messagebox.showerror("Erro", m)
        ctk.CTkButton(popup, text="Excluir e Gravar Log", fg_color="#D32F2F", height=45, command=confirmar).pack(fill="x", padx=30, pady=20)

def renderizar(frame_destino, usuario_logado, tipo):
    return RelatorioItinerarioView(master=frame_destino, usuario_logado=usuario_logado, tipo_relatorio=tipo)