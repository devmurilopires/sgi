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

        # Definição de Colunas SIGP
        if self.tipo_doc == "OS":
            self.colunas_config = {
                "id": "ID", "numero_os": "N° OS", "id_ponto": "ID Ponto", 
                "origem": "Origem", "acao": "Ação", "item": "Item", 
                "status": "Status", "bairro": "Bairro", "responsavel": "Responsável", 
                "data_criacao": "Data Criação"
            }
        else:
            self.colunas_config = {
                "id": "ID", "numero_parecer_ano": "N° Parecer", "processo": "Processo", 
                "origem": "Origem", "assunto": "Assunto", "decisao": "Decisão", 
                "solicitante": "Solicitante", "responsavel": "Responsável", 
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

    def _construir_interface(self):
        # --- 1. TOPO (FILTROS) ---
        self.frame_top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.frame_top.pack(side="top", fill="x", padx=20, pady=(20, 10))
        
        header_filtro = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        header_filtro.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header_filtro, text=f"Filtros de Pesquisa - {self.tipo_doc} (Pontos de Parada)", font=("Arial Black", 16), text_color="#0F8C75").pack(side="left")
        
        ctk.CTkButton(header_filtro, text="📄 PDF", width=90, fg_color="#D32F2F", hover_color="#B71C1C", command=self.acao_pdf).pack(side="right", padx=5)
        ctk.CTkButton(header_filtro, text="📊 Excel", width=90, fg_color="#1D6F42", hover_color="#145431", command=self.acao_excel).pack(side="right", padx=5)

        self.grid_filtros = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        self.grid_filtros.pack(fill="x", padx=15, pady=5)
        
        campos_ignorar = ["id", "data_criacao"]
        row, col = 0, 0
        
        # Filtros Inteligentes Específicos para Ponto de Parada
        for key, label in self.colunas_config.items():
            if key in campos_ignorar: continue
            
            f = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
            f.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
            self.grid_filtros.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(f, text=label, font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
            
            # COMBOS DINÂMICOS
            if key == "origem":
                widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="ORIGEM", height=35, fg_color="#F9FAFB")
                vals = ["Todos"] + [v for v in widget.cget("values") if v != "Nenhuma opção cadastrada"]
                widget.configure(values=vals)
                widget.set("Todos")
                
            elif key == "acao":
                widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="ACAO_OS", height=35, fg_color="#F9FAFB")
                vals = ["Todos"] + [v for v in widget.cget("values") if v != "Nenhuma opção cadastrada"]
                widget.configure(values=vals)
                widget.set("Todos")
                
            elif key == "item":
                widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="TIPO_ITEM", height=35, fg_color="#F9FAFB")
                vals = ["Todos"] + [v for v in widget.cget("values") if v != "Nenhuma opção cadastrada"]
                widget.configure(values=vals)
                widget.set("Todos")
                
            elif key == "solicitante":
                widget = CtkParametrosComboBox(f, setor="Ponto de Parada", campo="SOLICITANTE", height=35, fg_color="#F9FAFB")
                vals = ["Todos"] + [v for v in widget.cget("values") if v != "Nenhuma opção cadastrada"]
                widget.configure(values=vals)
                widget.set("Todos")

            elif key == "status" and self.tipo_doc == "OS":
                widget = ctk.CTkComboBox(f, values=["Todos", "PENDENTE", "CONCLUÍDO", "CANCELADO"], height=35, fg_color="#F9FAFB")
                widget.set("Todos")
            elif key == "bairro":
                widget = ctk.CTkComboBox(f, values=self.lista_bairros[:20] if self.lista_bairros else [""], height=35, fg_color="#F9FAFB")
                widget.set("") 
                def on_key_bairro(event, cb=widget):
                    txt = cb.get().lower()
                    sugestoes = [b for b in self.lista_bairros if txt in b.lower()][:20]
                    cb.configure(values=sugestoes)
                widget.bind("<KeyRelease>", on_key_bairro)
            
            # COMBOS - PARECER
            elif key == "decisao":
                widget = ctk.CTkComboBox(f, values=["Todos", "DEFERIDO", "INDEFERIDO"], height=35, fg_color="#F9FAFB")
                widget.set("Todos")
            elif key == "assunto" and self.tipo_doc == "PARECER":
                assuntos = ["Todos", "Solicitação de Implantação de Abrigo Metálico", "Solicitação de Implantação de Placa/Barrote", "Solicitação de Implantação de Placa/Poste", "Solicitação de Implantação de Parada Segura", "Solicitação de Implantação de Abrigo Concreto", "Solicitação de Transferência de Abrigo Metálico", "Solicitação de Transferência de Placa/Barrote", "Solicitação de Recolhimento de Abrigo Metálico"]
                widget = ctk.CTkComboBox(f, values=assuntos, height=35, fg_color="#F9FAFB")
                widget.set("Todos")
            
            # ENTRADAS DE TEXTO
            else:
                widget = ctk.CTkEntry(f, height=35, placeholder_text=f"Digite {label.lower()}...", border_color="#D1D5DB", fg_color="#F9FAFB")
            
            widget.pack(fill="x")
            self.entradas_filtros[key] = widget
            
            col += 1
            if col > 3: col = 0; row += 1

        f_data = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
        f_data.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(f_data, text="Período (Início - Fim)", font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
        
        f_data_inner = ctk.CTkFrame(f_data, fg_color="transparent")
        f_data_inner.pack(fill="x")
        self.date_ini = DateEntry(f_data_inner, width=12, background='#0F8C75', locale='pt_BR')
        self.date_ini.set_date(date(date.today().year, 1, 1))
        self.date_ini.pack(side="left")
        ctk.CTkLabel(f_data_inner, text=" até ").pack(side="left", padx=5)
        self.date_fim = DateEntry(f_data_inner, width=12, background='#0F8C75', locale='pt_BR')
        self.date_fim.pack(side="left")

        btn_busca = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        btn_busca.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkButton(btn_busca, text="🔍 Buscar Registros", font=("Arial Bold", 13), width=150, height=35, fg_color="#0F8C75", command=self.acao_buscar).pack(side="left", padx=(5, 10))
        ctk.CTkButton(btn_busca, text="Limpar Filtros", font=("Arial", 13), width=120, height=35, fg_color="transparent", text_color="#666666", hover_color="#F3F4F6", border_width=1, border_color="#D1D5DB", command=self._limpar_filtros).pack(side="left")


        # --- 2. RODAPÉ ---
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


        # --- 3. TABELA ---
        self.frame_tabela = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.frame_tabela.pack(side="top", fill="both", expand=True, padx=20, pady=5)

        cols = list(self.colunas_config.keys())
        self.tree = ttk.Treeview(self.frame_tabela, columns=cols, show="headings", style="Modern.Treeview")
        self.tree.tag_configure('impar', background="#FFFFFF")
        self.tree.tag_configure('par', background="#F9FAFB")
        
        for k, v in self.colunas_config.items():
            self.tree.heading(k, text=v)
            if k == "assunto":
                self.tree.column(k, width=250, anchor="w") # Mais largo para Assunto longo
            else:
                self.tree.column(k, width=100, anchor="center")
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
        filtros["data_inicio"] = self.date_ini.get_date()
        filtros["data_fim"] = self.date_fim.get_date()
        return filtros

    def _executar_busca_banco(self):
        filtros = self._get_filtros_formatados()
        offset = (self.pagina_atual - 1) * self.itens_por_pagina
        
        self.dados_atuais = self.service.repo.buscar_dados_paginados(self.tipo_doc, filtros, self.itens_por_pagina, offset)
        total = self.service.repo.contar_total(self.tipo_doc, filtros)
        
        self.tree.delete(*self.tree.get_children())
        for i, d in enumerate(self.dados_atuais):
            if d.get("data_criacao"): d["data_criacao"] = d["data_criacao"].strftime("%d/%m/%Y")
            
            # Tratamento visual especial para OS Ponto (Ponto Principal vs Adicionais)
            if self.tipo_doc == "OS":
                d["id_ponto"] = str(d.get("ponto_principal_id") or "")
                if d.get("pontos_adicionais"):
                    d["id_ponto"] += f" (+{str(d.get('pontos_adicionais'))})"

            valores = [d.get(k, "") for k in self.colunas_config.keys()]
            tag = 'par' if i % 2 == 0 else 'impar'
            self.tree.insert("", "end", values=valores, iid=d['id'], tags=(tag,))
            
        self.total_paginas = math.ceil(total / self.itens_por_pagina) or 1
        self.lbl_pag.configure(text=f"Página {self.pagina_atual} de {self.total_paginas}  |  Total: {total} resultados")
        
        self.btn_ant.configure(state="normal" if self.pagina_atual > 1 else "disabled")
        self.btn_prox.configure(state="normal" if self.pagina_atual < self.total_paginas else "disabled")

    def acao_detalhes(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Por favor, selecione um registro na tabela.")
        
        dado = next((x for x in self.dados_atuais if str(x['id']) == sel[0]), None)
        if not dado: return

        modal = ctk.CTkToplevel(self)
        titulo_num = dado.get('numero_os') if self.tipo_doc == "OS" else dado.get('numero_parecer_ano')
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

        row_idx = 0
        grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=15)
        
        campos_exibir = [(k, v) for k, v in dado.items() if k not in ['id', 'caminho_arquivo'] and v]
        
        for i in range(0, len(campos_exibir), 2):
            lbl_key1 = str(campos_exibir[i][0]).replace("_", " ").title()
            ctk.CTkLabel(grid, text=f"{lbl_key1}:", font=("Arial Bold", 12), text_color="#4B5563").grid(row=row_idx, column=0, sticky="w", pady=8, padx=(0, 5))
            ctk.CTkLabel(grid, text=str(campos_exibir[i][1]), font=("Arial", 12), wraplength=250, justify="left").grid(row=row_idx, column=1, sticky="w", pady=8, padx=(0, 20))

            if i + 1 < len(campos_exibir):
                lbl_key2 = str(campos_exibir[i+1][0]).replace("_", " ").title()
                ctk.CTkLabel(grid, text=f"{lbl_key2}:", font=("Arial Bold", 12), text_color="#4B5563").grid(row=row_idx, column=2, sticky="w", pady=8, padx=(0, 5))
                ctk.CTkLabel(grid, text=str(campos_exibir[i+1][1]), font=("Arial", 12), wraplength=250, justify="left").grid(row=row_idx, column=3, sticky="w", pady=8)
            row_idx += 1

        if dado.get('caminho_arquivo'):
            ctk.CTkLabel(scroll, text="Localização na Rede:", font=("Arial Bold", 12)).pack(anchor="w", pady=(15, 0))
            path_box = ctk.CTkEntry(scroll, fg_color="#F3F4F6", text_color="#6B7280", border_width=0)
            path_box.pack(fill="x", pady=5)
            path_box.insert(0, dado.get('caminho_arquivo'))
            path_box.configure(state="readonly")

        ctk.CTkButton(scroll, text="Fechar", width=150, height=40, fg_color="#6B7280", hover_color="#4B5563", command=modal.destroy).pack(pady=30)

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
        if messagebox.askyesno("Atenção Crítica", "Esta ação apagará permanentemente o documento do banco de dados.\nDeseja prosseguir?"):
            sucesso, msg = self.service.excluir(self.tipo_doc, sel[0])
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
            if isinstance(widget, ctk.CTkComboBox):
                if key == "bairro": widget.set("")
                else: widget.set("Todos")
            else:
                widget.delete(0, 'end')
        self.date_ini.set_date(date(date.today().year, 1, 1))
        self.date_fim.set_date(date.today())
        self.acao_buscar()

def renderizar(frame_destino, usuario_logado, tipo_relatorio):
    return RelatorioView(master=frame_destino, usuario_logado=usuario_logado, tipo_relatorio=tipo_relatorio)
