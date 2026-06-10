import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import date
import math
from src.modulos.ponto_parada.relatorios.service import RelatorioService
from src.core.shared.components.parameters_combo import CtkParametrosComboBox

class RelatorioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado, tipo_relatorio):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)
        
        self.service = RelatorioService()
        self.usuario = usuario_logado
        self.is_admin = usuario_logado.get("is_admin", False) if isinstance(usuario_logado, dict) else False
        self.tipo_doc = tipo_relatorio.upper()
        
        self.pagina_atual = 1
        self.itens_por_pagina = 50
        self.total_paginas = 1
        self.entradas_filtros = {}
        self.dados_atuais = []

        self.lista_bairros = self.service.obter_bairros()
        self.lista_itens = self.service.obter_todos_itens()

        if self.tipo_doc == "OS":
            self.colunas_config = {
                "id": "ID", "numero_os": "N° OS", "id_ponto": "ID Ponto", 
                "origem": "Origem", "acao": "Ação", "item": "Item", 
                "status": "Status", "bairro": "Bairro", "responsavel": "Responsável", 
                "data_criacao": "Data Criação"
            }
        else:
            # MODIFICAÇÃO: Nova ordem requisitada
            self.colunas_config = {
                "id": "ID", 
                "numero_completo": "N° Parecer", 
                "processo": "N° Processo", 
                "assunto": "Assunto",  
                "decisao": "Decisão", 
                "origem": "Origem",
                "solicitante": "Solicitante", 
                "responsavel": "Responsável", 
                "data_criacao": "Data Criação"
            }

        self._configurar_estilos()
        self._construir_interface()
        self.acao_buscar()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Modern.Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", 
                        rowheight=38, font=("Arial", 11), borderwidth=0)
        style.configure("Modern.Treeview.Heading", font=("Arial Bold", 11), 
                        background="#E9ECEF", foreground="#333333", borderwidth=0, padding=(0, 5))
        style.map("Modern.Treeview", background=[('selected', '#0F8C75')], foreground=[('selected', 'white')])
        style.map("Modern.Treeview.Heading", background=[('active', '#D1D5DB')])

    def _criar_date_wrapper(self, parent, width):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 12), background="#0F8C75", foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _construir_interface(self):
        self.frame_top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.frame_top.pack(side="top", fill="x", padx=20, pady=(20, 10))
        
        header_filtro = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        header_filtro.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header_filtro, text=f"Filtros de Pesquisa - {self.tipo_doc} (Pontos de Parada)", font=("Arial Black", 16), text_color="#0F8C75").pack(side="left")
        
        ctk.CTkButton(header_filtro, text="📄 PDF", width=90, fg_color="#D32F2F", hover_color="#B71C1C", command=self.acao_pdf).pack(side="right", padx=5)
        ctk.CTkButton(header_filtro, text="📊 Excel", width=90, fg_color="#1D6F42", hover_color="#145431", command=self.acao_excel).pack(side="right", padx=5)

        self.grid_filtros = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        self.grid_filtros.pack(fill="x", padx=15, pady=5)
        
        for i in range(6):
            self.grid_filtros.grid_columnconfigure(i, weight=1)
            
        campos_ignorar = ["id", "data_criacao"]
        row, col = 0, 0
        
        for key, label in self.colunas_config.items():
            if key in campos_ignorar: continue
            
            colspan = 1
            if self.tipo_doc == "PARECER" and key in ["assunto", "solicitante", "origem"]: colspan = 2
            elif self.tipo_doc == "OS" and key in ["item", "bairro"]: colspan = 2
            
            f = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
            f.grid(row=row, column=col, columnspan=colspan, padx=10, pady=8, sticky="ew")
            ctk.CTkLabel(f, text=label, font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
            
            if key == "origem": widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="ORIGEM", incluir_todos=True, height=35)
            elif key == "acao": widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="ACAO_OS", incluir_todos=True, height=35)
            elif key == "item": widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="ITENS", incluir_todos=True, height=35)
            elif key == "solicitante": widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="SOLICITANTE_PARECER", incluir_todos=True, height=35)
            elif key == "status": widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="STATUS_OS", incluir_todos=True, height=35)
            elif key == "decisao": widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="DECISAO_PARECER", incluir_todos=True, height=35)
            elif key == "assunto": widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="ASSUNTO_PARECER", incluir_todos=True, height=35)
            else: widget = ctk.CTkEntry(f, height=35, placeholder_text=f"Digite {label.lower()}...", border_color="#D1D5DB", fg_color="#F9FAFB")
            
            widget.pack(fill="x")
            self.entradas_filtros[key] = widget
            
            col += colspan
            if col >= 6: 
                col = 0; row += 1

        date_inicio = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
        date_inicio.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(date_inicio, text="Data Inicial:", font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
        wrapper_ini, self.data_inicio = self._criar_date_wrapper(date_inicio, 150)
        wrapper_ini.pack(fill="x", pady=(2,0))
        self.data_inicio.set_date(date(date.today().year, 1, 1))

        col += 1
        if col >= 6: col = 0; row += 1

        date_fim = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
        date_fim.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(date_fim, text="Data Final:", font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
        wrapper_fim, self.data_fim = self._criar_date_wrapper(date_fim, 150)
        wrapper_fim.pack(fill="x", pady=(2,0))

        btn_busca = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        btn_busca.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkButton(btn_busca, text="🔍 Buscar Registros", font=("Arial Bold", 13), width=150, height=35, fg_color="#0F8C75", command=self.acao_buscar).pack(side="left", padx=(5, 10))
        ctk.CTkButton(btn_busca, text="Limpar Filtros", font=("Arial", 13), width=120, height=35, fg_color="transparent", text_color="#666666", hover_color="#F3F4F6", border_width=1, border_color="#D1D5DB", command=self._limpar_filtros).pack(side="left")

        # --- RODAPÉ ---
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bottom.pack(side="bottom", fill="x", padx=20, pady=(5, 20))
        
        self.frame_paginacao = ctk.CTkFrame(self.frame_bottom, fg_color="transparent")
        self.frame_paginacao.pack(side="left")
        
        self.btn_ant = ctk.CTkButton(self.frame_paginacao, text="< Anterior", font=("Arial Bold", 12), width=90, height=35, fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", command=self._pagina_anterior)
        self.btn_ant.pack(side="left", padx=5)
        self.lbl_pag = ctk.CTkLabel(self.frame_paginacao, text="Página 1 | Total: 0 resultados", font=("Arial Bold", 13), text_color="#0F8C75")
        self.lbl_pag.pack(side="left", padx=15)
        self.btn_prox = ctk.CTkButton(self.frame_paginacao, text="Próxima >", font=("Arial Bold", 12), width=90, height=35, fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", command=self._pagina_proxima)
        self.btn_prox.pack(side="left", padx=5)

        self.frame_acoes = ctk.CTkFrame(self.frame_bottom, fg_color="transparent")
        self.frame_acoes.pack(side="right")
        ctk.CTkButton(self.frame_acoes, text="👁️ Ver Detalhes", font=("Arial Bold", 13), width=140, height=35, fg_color="#374151", hover_color="#1F2937", command=self.acao_detalhes).pack(side="left", padx=5)
        ctk.CTkButton(self.frame_acoes, text="📂 Abrir Documento", font=("Arial Bold", 13), width=160, height=35, fg_color="#0F8C75", hover_color="#0B6B59", command=self.acao_abrir).pack(side="left", padx=5)
        if self.is_admin:
            ctk.CTkButton(self.frame_acoes, text="🗑️ Excluir", font=("Arial Bold", 13), width=120, height=35, fg_color="transparent", border_width=1, border_color="#D32F2F", text_color="#D32F2F", hover_color="#FEE2E2", command=self.acao_excluir).pack(side="left", padx=(5, 0))

        # --- TABELA ---
        self.frame_tabela = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.frame_tabela.pack(side="top", fill="both", expand=True, padx=20, pady=5)

        cols = list(self.colunas_config.keys())
        self.tree = ttk.Treeview(self.frame_tabela, columns=cols, show="headings", style="Modern.Treeview")
        self.tree.tag_configure('impar', background="#FFFFFF")
        self.tree.tag_configure('par', background="#F9FAFB")
        
        for k, v in self.colunas_config.items():
            self.tree.heading(k, text=v)
            if k == "assunto": self.tree.column(k, width=280, anchor="w") 
            elif k == "solicitante": self.tree.column(k, width=200, anchor="w")
            else: self.tree.column(k, width=100, anchor="center")
        self.tree.column("id", width=0, stretch=False) 
        
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=15)
        scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=15)
        self.tree.bind("<Double-1>", lambda e: self.acao_detalhes())

    def _pagina_anterior(self):
        if self.pagina_atual > 1:
            self.pagina_atual -= 1
            self._executar_busca_banco()

    def _pagina_proxima(self):
        if self.pagina_atual < self.total_paginas:
            self.pagina_atual += 1
            self._executar_busca_banco()

    def acao_buscar(self):
        self.pagina_atual = 1
        self._executar_busca_banco()

    def _get_filtros_formatados(self):
        filtros = {}
        for k, v in self.entradas_filtros.items():
            val = v.get().strip()
            if val == "Todos": val = "" 
            filtros[k] = val
        filtros["data_inicio"] = self.data_inicio.get_date()
        filtros["data_fim"] = self.data_fim.get_date()
        return filtros

    def _executar_busca_banco(self):
        filtros = self._get_filtros_formatados()
        offset = (self.pagina_atual - 1) * self.itens_por_pagina
        
        self.dados_atuais = self.service.repo.buscar_dados_paginados(self.tipo_doc, filtros, self.itens_por_pagina, offset)
        total = self.service.repo.contar_total(self.tipo_doc, filtros)
        
        self.tree.delete(*self.tree.get_children())
        for i, d in enumerate(self.dados_atuais):
            if d.get("data_criacao"): d["data_criacao"] = d["data_criacao"].strftime("%d/%m/%Y")
        
            if self.tipo_doc == "OS":
                p_principal = str(d.get("ponto_principal_id") or "").strip()
                p_adicionais = str(d.get("pontos_adicionais") or "").strip()
                if p_adicionais: d["id_ponto"] = f"{p_principal} (+ {p_adicionais})"
                else: d["id_ponto"] = p_principal

            # BLINDAGEM: Converte valores vazios/None para "-"
            valores = []
            for k in self.colunas_config.keys():
                val = d.get(k)
                if val is None or str(val).strip() == "" or str(val).strip().lower() == "none":
                    valores.append("-")
                else:
                    valores.append(str(val))

            tag = 'par' if i % 2 == 0 else 'impar'
            self.tree.insert("", "end", values=valores, iid=d['id'], tags=(tag,))
            
        self.total_paginas = math.ceil(total / self.itens_por_pagina) or 1
        self.lbl_pag.configure(text=f"Página {self.pagina_atual} de {self.total_paginas}  |  Total: {total} resultados")
        
        self.btn_ant.configure(state="normal" if self.pagina_atual > 1 else "disabled")
        self.btn_prox.configure(state="normal" if self.pagina_atual < self.total_paginas else "disabled")

    # 1. Função Dinâmica: Sem campos bloqueados! Tudo é editável.
    def _add_detail_field_dinamico(self, parent, key, value, row, col, pad_x, editando):
        label_text = str(key).replace("_", " ").title()
        ctk.CTkLabel(parent, text=f"{label_text}:", font=("Arial Bold", 12), text_color="#4B5563").grid(row=row, column=col, sticky="nw", pady=8, padx=(0, 5))
        
        val_str = str(value).strip() if value is not None else ""
        if not val_str or val_str.lower() == "none": val_str = "-"

        if not editando:
            linhas = max(1, len(val_str) // 35)
            linhas = max(linhas, val_str.count('\n') + 1)
            altura = linhas * 20 + 10
            
            box = ctk.CTkTextbox(parent, font=("Arial", 12), width=250, height=altura, fg_color="transparent", border_width=0, wrap="word")
            box.insert("1.0", val_str)
            box.configure(state="disabled") 
            box.grid(row=row, column=col+1, sticky="nw", pady=8, padx=pad_x)
            if editando: self.modal_edit_widgets[key] = box
        else:
            # Renderiza Comboboxes Inteligentes no Modo Edição
            if key == "origem":
                w = CtkParametrosComboBox(parent, setor="Ponto de Parada", campo="ORIGEM", width=250, height=35)
                w.set(val_str if val_str != "-" else "– Selecione –")
            elif key == "acao":
                w = CtkParametrosComboBox(parent, setor="Ponto de Parada", campo="ACAO_OS", width=250, height=35)
                w.set(val_str if val_str != "-" else "– Selecione –")
            elif key == "item":
                w = CtkParametrosComboBox(parent, setor="Ponto de Parada", campo="ITENS", width=250, height=35)
                w.set(val_str if val_str != "-" else "– Selecione –")
            elif key == "status":
                w = CtkParametrosComboBox(parent, setor="Ponto de Parada", campo="STATUS_OS", width=250, height=35)
                w.set(val_str if val_str != "-" else "– Selecione –")
            elif key == "decisao":
                w = CtkParametrosComboBox(parent, setor="Ponto de Parada", campo="DECISAO_PARECER", width=250, height=35)
                w.set(val_str if val_str != "-" else "– Selecione –")
            elif key == "assunto":
                w = CtkParametrosComboBox(parent, setor="Ponto de Parada", campo="ASSUNTO_PARECER", width=250, height=35)
                w.set(val_str if val_str != "-" else "– Selecione –")
            elif key == "solicitante":
                w = CtkParametrosComboBox(parent, setor="Ponto de Parada", campo="SOLICITANTE_PARECER", width=250, height=35)
                w.set(val_str if val_str != "-" else "– Selecione –")
            else:
                # Demais campos: Data, Processo, Número, Endereço, Responsável...
                w = ctk.CTkEntry(parent, width=250, height=35, font=("Arial", 12))
                w.insert(0, val_str if val_str != "-" else "")
            
            w.grid(row=row, column=col+1, sticky="nw", pady=8, padx=pad_x)
            self.modal_edit_widgets[key] = w

    # 2. Tela de Detalhes Modificada
    def acao_detalhes(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Por favor, selecione um registro na tabela.")
        
        dado_bruto = next((x for x in self.dados_atuais if str(x['id']) == sel[0]), None)
        if not dado_bruto: return
        dado = dado_bruto.copy()
        
        if self.tipo_doc == "OS":
            p_principal = str(dado.get("ponto_principal_id", "")).strip()
            if "id_ponto" in dado: dado['id_ponto'] = p_principal

        modal = ctk.CTkToplevel(self)
        titulo_num = dado.get('numero_os') if self.tipo_doc == "OS" else dado.get('numero_completo')
        modal.title(f"Visualização Detalhada - {self.tipo_doc} Nº {titulo_num}")
        modal.geometry("800x650")
        modal.grab_set()

        scroll = ctk.CTkScrollableFrame(modal, fg_color="#F9FAFB")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header_frame, text=f"Detalhes Completos do Documento", font=("Arial Black", 20), text_color="#0F8C75").pack(side="left")

        info_frame = ctk.CTkFrame(scroll, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E5E7EB")
        info_frame.pack(fill="x", pady=10)

        grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=15)
        
        campos_exibir = [(k, v) for k, v in dado.items() if k not in ['id', 'caminho_arquivo', 'pontos_adicionais', 'ponto_principal_id']]
        self.modal_edit_widgets = {}

        def desenhar_grid(editando=False):
            for w in grid.winfo_children(): w.destroy()
            self.modal_edit_widgets.clear()
            row_idx = 0
            for i in range(0, len(campos_exibir), 2):
                key1, val1 = campos_exibir[i]
                self._add_detail_field_dinamico(grid, key1, val1, row_idx, 0, (0, 20), editando)

                if i + 1 < len(campos_exibir):
                    key2, val2 = campos_exibir[i+1]
                    self._add_detail_field_dinamico(grid, key2, val2, row_idx, 2, (0, 0), editando)
                row_idx += 1

        desenhar_grid(editando=False) # Inicia no modo visualização

        if dado.get('caminho_arquivo'):
            ctk.CTkLabel(scroll, text="Localização na Rede:", font=("Arial Bold", 12)).pack(anchor="w", pady=(15, 0))
            path_box = ctk.CTkEntry(scroll, fg_color="#F3F4F6", text_color="#6B7280", border_width=0)
            path_box.pack(fill="x", pady=5)
            path_box.insert(0, dado.get('caminho_arquivo'))
            path_box.configure(state="readonly")

        # --- BOTÕES DO MODAL ---
        frame_botoes = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_botoes.pack(pady=30)
        
        if self.is_admin:
            def alternar_edicao():
                if btn_editar.cget("text") == "✏️ Editar":
                    btn_editar.configure(text="💾 Salvar", fg_color="#10B981", hover_color="#059669")
                    desenhar_grid(editando=True)
                else:
                    novos_dados = {}
                    for k, widget in self.modal_edit_widgets.items():
                        if isinstance(widget, CtkParametrosComboBox):
                            v = widget.get()
                            novos_dados[k] = "" if v == "– Selecione –" else v
                        elif isinstance(widget, ctk.CTkTextbox): pass
                        else:
                            novos_dados[k] = widget.get().strip()
                    
                    sucesso, msg = self.service.atualizar_registro(self.tipo_doc, dado['id'], novos_dados)
                    if sucesso:
                        messagebox.showinfo("Sucesso", msg)
                        modal.destroy()
                        self.acao_buscar()
                    else:
                        messagebox.showerror("Erro", msg)

            btn_editar = ctk.CTkButton(frame_botoes, text="✏️ Editar", width=140, height=40, fg_color="#F59E0B", hover_color="#D97706", command=alternar_edicao)
            btn_editar.pack(side="left", padx=10)

        ctk.CTkButton(frame_botoes, text="Fechar", width=140, height=40, fg_color="#6B7280", hover_color="#4B5563", command=modal.destroy).pack(side="left", padx=10)

    def acao_abrir(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um registro para abrir o arquivo.")
        item = next((x for x in self.dados_atuais if str(x['id']) == sel[0]), None)
        if item:
            sucesso, msg = self.service.abrir_documento(item.get('caminho_arquivo'))
            if not sucesso: messagebox.showerror("Erro", msg)

    def acao_excluir(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um registro para excluir.")
        
        # 1. Abre a caixinha solicitando o motivo obrigatório da exclusão
        dialog = ctk.CTkInputDialog(text="Motivo para a exclusão do registro:", title="Auditoria de Exclusão")
        motivo = dialog.get_input()
        
        if motivo is None: 
            return # Se clicar em cancelar, interrompe
        if not motivo.strip():
            return messagebox.showwarning("Aviso", "A exclusão foi abortada. O motivo é obrigatório.")
            
        if messagebox.askyesno("Atenção Crítica", "Esta ação enviará o documento para o Histórico/Lixeira do sistema.\nDeseja prosseguir?"):
            # 2. Captura o nome do usuário de forma segura
            usr_nome = self.usuario.get('nome') if isinstance(self.usuario, dict) else self.usuario
            
            # 3. Envia os novos parâmetros para o service
            sucesso, msg = self.service.excluir(self.tipo_doc, sel[0], motivo.strip(), usr_nome)
            if sucesso:
                self.acao_buscar()
                messagebox.showinfo("Sucesso", msg)
            else: messagebox.showerror("Erro", msg)

    def acao_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if path:
            s, m = self.service.exportar_excel(self.tipo_doc, self._get_filtros_formatados(), path)
            messagebox.showinfo("Resultado", m) if s else messagebox.showerror("Erro", m)

    def acao_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if path:
            s, m = self.service.exportar_pdf(self.tipo_doc, self._get_filtros_formatados(), path)
            messagebox.showinfo("Resultado", m) if s else messagebox.showerror("Erro", m)

    def _limpar_filtros(self):
        for key, widget in self.entradas_filtros.items():
            if isinstance(widget, CtkParametrosComboBox): widget.set("Todos")
            else: widget.delete(0, 'end')
                
        self.data_inicio.set_date(date(date.today().year, 1, 1))
        self.data_fim.set_date(date.today())
        self.acao_buscar()

def renderizar(frame_destino, usuario_logado, tipo_relatorio):
    return RelatorioView(master=frame_destino, usuario_logado=usuario_logado, tipo_relatorio=tipo_relatorio)