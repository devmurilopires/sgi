import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkcalendar import DateEntry
from datetime import date
import math
import json

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.modulos.quadro_horario.relatorios.service import RelatorioQuadroHorarioService, ensure_payload_list, safe_float
from src.core.shared.components.parameters_combo import CtkParametrosComboBox

# =====================================================================
# COMPONENTE HÍBRIDO: AUTOCOMPLETE MODERNO COM NAVEGAÇÃO POR TECLADO
# =====================================================================
class Autocomplete(ctk.CTkEntry):
    def __init__(self, master, values, **kwargs):
        super().__init__(master, **kwargs)
        self.lista_sugestoes = values
        self.listbox_frame = None
        self.listbox_widget = None
        self.selecao_idx = -1

        self.bind("<KeyRelease>", self.on_keyrelease)
        self.bind("<Down>", self.navegar_para_baixo)
        self.bind("<Up>", self.navegar_para_cima)
        self.bind("<Return>", self.selecionar_com_enter)
        self.bind("<FocusOut>", self.esconder_lista_com_atraso)
        self.bind("<Destroy>", lambda e: self.esconder_lista())

    def on_keyrelease(self, event):
        if event.keysym in ["Up", "Down", "Return", "Escape", "Tab"]:
            return  
        texto = self.get().strip().lower()
        if not texto:
            self.esconder_lista()
            return
        filtradas = [linha for linha in self.lista_sugestoes if texto in linha.lower()][:15]
        if filtradas: self.mostrar_lista(filtradas)
        else: self.esconder_lista()

    def mostrar_lista(self, filtradas):
        self.esconder_lista()
        toplevel = self.winfo_toplevel()
        if not toplevel.winfo_exists(): return
        
        x = self.winfo_rootx() - toplevel.winfo_rootx()
        y = self.winfo_rooty() - toplevel.winfo_rooty() + self.winfo_height() + 2
        w = self.winfo_width()
        h = min(180, len(filtradas) * 26 + 5)
        
        self.listbox_frame = ctk.CTkFrame(toplevel, fg_color="#FFFFFF", border_width=1, border_color="#10B981", corner_radius=6, width=w, height=h)
        self.listbox_frame.place(x=x, y=y)
        self.listbox_frame.pack_propagate(False)
        
        self.listbox_widget = tk.Listbox(self.listbox_frame, bg="#FFFFFF", fg="#333333", selectbackground="#10B981", selectforeground="#FFFFFF", bd=0, highlightthickness=0, font=("Arial", 11))
        self.listbox_widget.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        
        scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.listbox_widget.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox_widget.config(yscrollcommand=scrollbar.set)
        
        for item in filtradas: self.listbox_widget.insert(tk.END, item)
            
        self.selecao_idx = -1
        self.listbox_widget.bind("<<ListboxSelect>>", self.on_listbox_click)
        self.listbox_frame.lift()

    def esconder_lista(self, event=None):
        if self.listbox_frame and self.listbox_frame.winfo_exists(): self.listbox_frame.destroy()
        self.listbox_frame = None
        self.listbox_widget = None

    def esconder_lista_com_atraso(self, event):
        self.after(200, self.esconder_lista)

    def navegar_para_baixo(self, event):
        if self.listbox_widget:
            total = self.listbox_widget.size()
            if self.selecao_idx < total - 1:
                self.selecao_idx += 1
                self.listbox_widget.selection_clear(0, tk.END)
                self.listbox_widget.selection_set(self.selecao_idx)
                self.listbox_widget.see(self.selecao_idx)

    def navegar_para_cima(self, event):
        if self.listbox_widget and self.selecao_idx > 0:
            self.selecao_idx -= 1
            self.listbox_widget.selection_clear(0, tk.END)
            self.listbox_widget.selection_set(self.selecao_idx)
            self.listbox_widget.see(self.selecao_idx)

    def selecionar_com_enter(self, event):
        if self.listbox_widget and self.selecao_idx >= 0:
            try:
                selecionado = self.listbox_widget.get(self.selecao_idx)
                self.delete(0, tk.END)
                self.insert(0, selecionado)
            except Exception: pass
            self.esconder_lista()
            self.event_generate("<<AutocompleteSelected>>")
            return "break"
        return None

    def on_listbox_click(self, event):
        if not self.listbox_widget: return
        selecao = self.listbox_widget.curselection()
        if selecao:
            item = self.listbox_widget.get(selecao[0])
            self.delete(0, tk.END)
            self.insert(0, item)
            self.esconder_lista()
            self.event_generate("<<AutocompleteSelected>>")

# ==========================================================
# JANELA DE DETALHES AVANÇADA (PESQUISAS E GRÁFICOS)
# ==========================================================
class RelatorioDetalhesPesquisa(ctk.CTkToplevel):
    def __init__(self, master, dado, service):
        super().__init__(master)
        self.title(f"Detalhes Avançados - {dado.get('titulo', 'Pesquisa')}")
        self.geometry("1200x800")
        self.resizable(True, True)
        self.after(100, lambda: self.state('zoomed')) 
        
        self.service = service
        self.nome = dado.get("titulo", "Pesquisa")
        self.tipo = dado.get("tipo", "tempo")
        self.payload = ensure_payload_list(dado.get("payload"))
        
        container = ctk.CTkScrollableFrame(self, fg_color="#F9FAFB")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text=self.nome, font=("Arial Bold", 28), text_color="#10B981").pack(side="left", padx=10)
        
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        ctk.CTkButton(btn_frame, text="Exportar PDF", fg_color="#EF4444", hover_color="#DC2626", command=self.acao_exportar_pdf).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Exportar Excel", fg_color="#059669", hover_color="#047857", command=self.acao_exportar_excel).pack(side="left", padx=5)

        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="x", pady=10)

        for i, tabela in enumerate(self.payload):
            parent_row = row1 if i < 3 else row2
            if i < 3: color = "#D1D5DB"
            else: 
                idx_cor = i - 3
                if self.tipo == "demanda": map_colors = ["#F8D057", "#3498DB", "#5DADE2"]
                else: map_colors = ["#F8D057", "#58D68D", "#3498db"]
                color = map_colors[idx_cor] if idx_cor < len(map_colors) else "#F0F0F0"
            self._criar_tabela_card(parent_row, tabela, color)

        if len(self.payload) >= 6:
            self._criar_grafico(container, self.payload[3], custom_title_prefix="Média por sentido")
            self._criar_grafico(container, self.payload[5])
        
        ctk.CTkButton(container, text="Fechar Detalhes", width=200, height=40, fg_color="#6B7280", hover_color="#4B5563", command=self.destroy).pack(pady=30)
        
    def _criar_grafico(self, parent, tabela, custom_title_prefix=None):
        if not tabela or not isinstance(tabela, dict) or not tabela.get("rows"): return
        cols = tabela.get("columns") or []
        headings = tabela.get("headings") or {}
        rows = tabela.get("rows") or []

        idx_h = cols.index("HORARIO") if "HORARIO" in cols else 0
        sentidos = [c for c in cols if c.upper() not in ["HORARIO", "TOTAL"] and "GERAL" not in c.upper()]
        if not sentidos: return

        horarios = [str(r[idx_h]) for r in rows]
        PALETTE = ["#FFD92E", "#58D68D", "#3498DB", "#E74C3C"]

        for i, sc in enumerate(sentidos):
            try: idx = cols.index(sc)
            except ValueError: continue

            valores = [safe_float(r[idx]) for r in rows]
            fig = Figure(figsize=(10, 4), dpi=100)
            ax = fig.add_subplot(111)

            pos = list(range(len(valores)))
            bars = ax.bar(pos, valores, color=PALETTE[i % len(PALETTE)])

            nome_coluna = headings.get(sc, sc) if isinstance(headings, dict) else sc
            base_titulo = custom_title_prefix if custom_title_prefix else tabela.get("nome", "Análise")
            ax.set_title(f"{base_titulo}: {nome_coluna}", fontdict={'fontweight': 'bold', 'color': '#374151'})
            
            ax.set_xticks(pos)
            ax.set_xticklabels(horarios, rotation=45, ha="right", fontsize=8)
            ax.grid(axis="y", linestyle=":", alpha=0.4)

            for bar in bars:
                h = bar.get_height()
                txt = f"{int(h)}" if float(h).is_integer() else f"{h:.2f}"
                ax.annotate(txt, xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

    def _criar_tabela_card(self, parent, tabela, color):
        card = ctk.CTkFrame(parent, corner_radius=8, border_width=1, border_color="#E5E7EB", fg_color="#FFFFFF")
        card.pack(side="left", expand=True, fill="both", padx=6)

        header = ctk.CTkFrame(card, fg_color=color, corner_radius=6)
        header.pack(fill="x")
        nome_tab = tabela.get("nome", "Tabela")
        text_col = "#FFFFFF" if color not in ["#D1D5DB", "#F8D057", "#F0F0F0"] else "#333333"
        ctk.CTkLabel(header, text=str(nome_tab), font=("Arial Bold", 13), text_color=text_col).pack(anchor="center", pady=6)

        tbl_frame = tk.Frame(card, bg="white", height=240)
        tbl_frame.pack(fill="both", expand=False, padx=6, pady=6)
        tbl_frame.pack_propagate(False)

        cols = tabela.get("columns") or []
        headings = tabela.get("headings") or {}
        rows = tabela.get("rows") or []

        tv = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=10)
        vsb = ttk.Scrollbar(tbl_frame, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=vsb.set)

        for i, c in enumerate(cols):
            text = headings.get(c, c) if isinstance(headings, dict) else (headings[i] if isinstance(headings, list) and i < len(headings) else c)
            tv.heading(c, text=text)
            tv.column(c, width=100, anchor="center")

        for r in rows:
            try: tv.insert("", "end", values=r)
            except: pass

        vsb.pack(side="right", fill="y")
        tv.pack(side="left", fill="both", expand=True)

    def acao_exportar_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile=f"Pesquisa_{self.nome}.xlsx")
        if path:
            s, m = self.service.exportar_pesquisa_excel(self.nome, self.tipo, self.payload, path)
            messagebox.showinfo("Sucesso" if s else "Erro", m)

    def acao_exportar_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=f"Pesquisa_{self.nome}.pdf")
        if path:
            s, m = self.service.exportar_pesquisa_pdf(self.nome, self.tipo, self.payload, path)
            messagebox.showinfo("Sucesso" if s else "Erro", m)

# ==========================================================
# VIEW PRINCIPAL (TELA DE RELATÓRIOS E LISTAGEM)
# ==========================================================
class RelatorioQuadroHorarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado, tipo_relatorio):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)
        
        self.service = RelatorioQuadroHorarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.is_admin = usuario_logado.get('is_admin', False) if isinstance(usuario_logado, dict) else False
        self.tipo_doc = tipo_relatorio.upper()
        
        self.pagina_atual = 1
        self.itens_por_pagina = 50
        self.total_paginas = 1
        self.entradas_filtros = {}
        self.dados_atuais = []

        self.lista_linhas = self.service.obter_linhas()
        
        # MODIFICAÇÃO: Ordem Perfeita para PARECER
        if self.tipo_doc == "PESQUISA":
            self.colunas_config = {
                "id": "ID", "titulo": "Linha", "responsavel": "Criador",  
                "relatorios": "Relatórios Utilizados", "tipo": "Tipo",
                "data_criacao": "Data Criação"
            }
        else:
            self.colunas_config = {
                "id": "ID", "numero_completo": "N° Parecer", "processo": "Processo", 
                "solicitante": "Solicitante", "assunto": "Assunto","decisao": "Decisão", 
                "origem": "Origem", "responsavel": "Responsável", "data_criacao": "Data Criação"
            }

        self._configurar_estilos()
        self._construir_interface()
        self.acao_buscar()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Modern.Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", rowheight=40, font=("Arial", 11), borderwidth=0)
        style.configure("Modern.Treeview.Heading", font=("Arial Bold", 11), background="#E9ECEF", foreground="#333333", borderwidth=0, padding=(0, 5))
        style.map("Modern.Treeview", background=[('selected', '#0F8C75')], foreground=[('selected', 'white')])

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
        ctk.CTkLabel(header_filtro, text=f"Filtros de Pesquisa - {self.tipo_doc}", font=("Arial Black", 16), text_color="#0F8C75").pack(side="left")
        
        ctk.CTkButton(header_filtro, text="📄 PDF Geral", width=110, fg_color="#D32F2F", command=self.acao_pdf).pack(side="right", padx=5)
        ctk.CTkButton(header_filtro, text="📊 Excel Geral", width=110, fg_color="#1D6F42", command=self.acao_excel).pack(side="right", padx=5)

        self.grid_filtros = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        self.grid_filtros.pack(fill="x", padx=15, pady=5)
        
        campos_ignorar = ["id", "data_criacao", "responsavel"]
        row, col = 0, 0
        
        for key, label in self.colunas_config.items():
            if key in campos_ignorar: continue
            
            f = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
            f.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
            self.grid_filtros.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(f, text=label, font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
            
            if key == "tipo":
                widget = CtkParametrosComboBox(f, setor="Quadro de Horário", campo="PESQUISA", incluir_todos=True, height=35)
            elif key == "origem": 
                widget = CtkParametrosComboBox(f, setor="Quadro de Horário", campo="ORIGEM", incluir_todos=True, height=35)
            elif key == "decisao":
                widget = CtkParametrosComboBox(f, setor="Quadro de Horário", campo="DECISAO_PARECER", incluir_todos=True, height=35)
            elif key == "assunto":
                widget = CtkParametrosComboBox(f, setor="Quadro de Horário", campo="ASSUNTO_QUADRO_HORARIO", incluir_todos=True, height=35) 
            elif key == "solicitante":
                widget = CtkParametrosComboBox(f, setor="Quadro de Horário", campo="SOLICITANTE_PARECER", incluir_todos=True, height=35)
            elif key in ["titulo"]: 
                widget = Autocomplete(f, values=self.lista_linhas, width=430)
                widget.bind("<<AutocompleteSelected>>", lambda e: self.acao_buscar())
                widget.bind("<Return>", lambda e: self.acao_buscar())
            else:
                widget = ctk.CTkEntry(f, height=35, placeholder_text=f"Digite...")
            
            widget.pack(fill="x")
            self.entradas_filtros[key] = widget
            col += 1
            if col > 3: col = 0; row += 1

        date_inicio = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
        date_inicio.grid(row=row, column=col, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(date_inicio, text="Data Inicial:", font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
        wrapper_ini, self.date_ini = self._criar_date_wrapper(date_inicio, 450)
        wrapper_ini.pack(anchor="w", pady=(2,0))
        self.date_ini.set_date(date(date.today().year, 1, 1))

        date_fim = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
        date_fim.grid(row=row, column=col+1, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(date_fim, text="Data Final:", font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
        wrapper_fim, self.date_fim = self._criar_date_wrapper(date_fim, 450)
        wrapper_fim.pack(anchor="w", pady=(2,0))

        btn_busca = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        btn_busca.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkButton(btn_busca, text="🔍 Buscar", font=("Arial Bold", 13), width=120, height=35, fg_color="#0F8C75", command=self.acao_buscar).pack(side="left", padx=5)
        ctk.CTkButton(btn_busca, text="🧹 Limpar Filtros", font=("Arial", 13), width=120, height=35, fg_color="transparent", text_color="#666", border_width=1, command=self._limpar_filtros).pack(side="left")

        # MODIFICAÇÃO: Padronização completa do rodapé com Paginação e Ações Integradas
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
        
        if self.tipo_doc == "PARECER":
            ctk.CTkButton(self.frame_acoes, text="📂 Abrir Documento", font=("Arial Bold", 13), width=160, height=35, fg_color="#0F8C75", hover_color="#0B6B59", command=self.acao_abrir).pack(side="left", padx=5)
            
        if self.is_admin:
            ctk.CTkButton(self.frame_acoes, text="🗑️ Excluir", font=("Arial Bold", 13), width=120, height=35, fg_color="transparent", border_width=1, border_color="#D32F2F", text_color="#D32F2F", hover_color="#FEE2E2", command=self.acao_excluir).pack(side="left", padx=(5, 0))

        self.frame_tabela = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.frame_tabela.pack(side="top", fill="both", expand=True, padx=20, pady=5)

        cols = list(self.colunas_config.keys())
        self.tree = ttk.Treeview(self.frame_tabela, columns=cols, show="headings", style="Modern.Treeview")
        self.tree.tag_configure('impar', background="#FFFFFF")
        self.tree.tag_configure('par', background="#F9FAFB")
        
        for k, v in self.colunas_config.items():
            self.tree.heading(k, text=v)
            if k in ["titulo", "assunto", "solicitante"]: self.tree.column(k, width=190, anchor="w")
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
            if val != "Todos" and val != "":
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
            
            payload = d.get("payload")
            if isinstance(payload, str):
                try: payload = json.loads(payload)
                except: payload = {}
            if isinstance(payload, dict):
                datas_list = payload.get("datas", [])
                d["relatorios"] = "\n".join([f"  • {dt.strip()}" for dt in datas_list]) if datas_list else "-"
            else:
                d["relatorios"] = "-"

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
        if hasattr(self, 'btn_ant'):
            self.btn_ant.configure(state="normal" if self.pagina_atual > 1 else "disabled")
            self.btn_prox.configure(state="normal" if self.pagina_atual < self.total_paginas else "disabled")

    # MODIFICAÇÃO: Helper para Campos do Parecer copiáveis
    def _add_detail_field(self, parent, label, value, row, col, pad_x):
        ctk.CTkLabel(parent, text=f"{label}:", font=("Arial Bold", 12), text_color="#4B5563").grid(row=row, column=col, sticky="nw", pady=8, padx=(0, 5))
        val_str = str(value).strip()
        if not val_str or val_str.lower() == "none": val_str = "-"
        
        linhas = max(1, len(val_str) // 35)
        linhas = max(linhas, val_str.count('\n') + 1)
        altura = linhas * 20 + 10
        
        box = ctk.CTkTextbox(parent, font=("Arial", 12), width=250, height=altura, fg_color="transparent", border_width=0, wrap="word")
        box.insert("1.0", val_str)
        box.configure(state="disabled")
        box.grid(row=row, column=col+1, sticky="nw", pady=8, padx=pad_x)

    def acao_detalhes(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um registro.")
        dado = next((x for x in self.dados_atuais if str(x['id']) == sel[0]), None)
        if not dado: return
        
        if self.tipo_doc == "PESQUISA":
            RelatorioDetalhesPesquisa(self, dado, self.service)
        else: # PARECER
            modal = ctk.CTkToplevel(self)
            modal.title(f"Visualização Detalhada - Parecer Nº {dado.get('numero_completo', '')}")
            modal.geometry("800x650")
            modal.grab_set()

            scroll = ctk.CTkScrollableFrame(modal, fg_color="#F9FAFB")
            scroll.pack(fill="both", expand=True, padx=20, pady=20)

            header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            header_frame.pack(fill="x", pady=(0, 15))
            ctk.CTkLabel(header_frame, text="Detalhes Completos do Documento", font=("Arial Black", 20), text_color="#0F8C75").pack(side="left")

            info_frame = ctk.CTkFrame(scroll, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E5E7EB")
            info_frame.pack(fill="x", pady=10)

            grid = ctk.CTkFrame(info_frame, fg_color="transparent")
            grid.pack(fill="x", padx=15, pady=15)
            
            campos_exibir = [(k, v) for k, v in dado.items() if k not in ['id', 'caminho_arquivo', 'payload']]
            
            row_idx = 0
            for i in range(0, len(campos_exibir), 2):
                lbl_key1 = str(campos_exibir[i][0]).replace("_", " ").title()
                self._add_detail_field(grid, lbl_key1, campos_exibir[i][1], row_idx, 0, (0, 20))

                if i + 1 < len(campos_exibir):
                    lbl_key2 = str(campos_exibir[i+1][0]).replace("_", " ").title()
                    self._add_detail_field(grid, lbl_key2, campos_exibir[i+1][1], row_idx, 2, (0, 0))
                row_idx += 1

            if dado.get('caminho_arquivo'):
                ctk.CTkLabel(scroll, text="Localização na Rede:", font=("Arial Bold", 12)).pack(anchor="w", pady=(15, 0))
                path_box = ctk.CTkEntry(scroll, fg_color="#F3F4F6", text_color="#6B7280", border_width=0)
                path_box.pack(fill="x", pady=5)
                path_box.insert(0, dado.get('caminho_arquivo'))
                path_box.configure(state="readonly")

            ctk.CTkButton(scroll, text="Fechar Janela", width=150, height=40, fg_color="#6B7280", hover_color="#4B5563", command=modal.destroy).pack(pady=30)

    # MODIFICAÇÃO: Ação Abrir Documento
    def acao_abrir(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um registro para abrir o arquivo.")
        item = next((x for x in self.dados_atuais if str(x['id']) == sel[0]), None)
        if item:
            sucesso, msg = self.service.abrir_documento(item.get('caminho_arquivo'))
            if not sucesso: messagebox.showerror("Erro", msg)

    # MODIFICAÇÃO: Ação Excluir com requisição do Motivo de forma elegante
    def acao_excluir(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um registro para excluir.")
        
        dialog = ctk.CTkInputDialog(text="Motivo para a exclusão do registro:", title="Auditoria de Exclusão")
        motivo = dialog.get_input()
        
        if motivo is None: return # Clicou em cancelar
        if not motivo.strip():
            return messagebox.showwarning("Aviso", "A exclusão foi cancelada pois o motivo é obrigatório.")
            
        if messagebox.askyesno("Atenção Crítica", "Esta ação enviará o registro para a Lixeira do Sistema.\\nDeseja prosseguir?"):
            usr = self.usuario_logado.get('nome') if isinstance(self.usuario_logado, dict) else self.usuario_logado
            sucesso, msg = self.service.excluir_registro(self.tipo_doc, sel[0], motivo.strip(), usr)
            if sucesso:
                self.acao_buscar()
                messagebox.showinfo("Sucesso", msg)
            else: messagebox.showerror("Erro", msg)

    def acao_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if path: self.service.exportar_excel(self.tipo_doc, self._get_filtros_formatados(), path)

    def acao_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if path: self.service.exportar_pdf(self.tipo_doc, self._get_filtros_formatados(), path)

    def _limpar_filtros(self):
        for key, widget in self.entradas_filtros.items():
            if isinstance(widget, Autocomplete):  
                widget.set("")
            elif isinstance(widget, CtkParametrosComboBox): 
                widget.set("Todos")
            else: 
                widget.delete(0, 'end')
        self.date_ini.set_date(date(date.today().year, 1, 1))
        self.date_fim.set_date(date.today())
        self.acao_buscar()

def renderizar(frame_destino, usuario_logado, tipo_relatorio):
    return RelatorioQuadroHorarioView(master=frame_destino, usuario_logado=usuario_logado, tipo_relatorio=tipo_relatorio)