import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import date
import math
from src.modulos.itinerario.relatorios.service import RelatoriosItinerarioService
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
        if self.cget("state") == "disabled": return
        if event.keysym in ["Up", "Down", "Return", "Escape", "Tab"]: return  
        
        texto = self.get().strip().lower()
        if not texto:
            self.esconder_lista(); return
            
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
            selecionado = self.listbox_widget.get(self.selecao_idx)
            self.delete(0, tk.END)
            self.insert(0, selecionado)
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

    def set(self, value):
        self.delete(0, "end")
        if value: self.insert(0, value)


class RelatoriosItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado, tipo_doc):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)
        
        self.service = RelatoriosItinerarioService()
        self.usuario = usuario_logado
        self.is_admin = usuario_logado.get("is_admin", False)
        self.tipo_doc = tipo_doc.upper()
        
        self.pagina_atual = 1
        self.itens_por_pagina = 50
        self.total_paginas = 1
        self.entradas_filtros = {}
        self.dados_atuais = []

        self.lista_empresas = self.service.obter_empresas()
        self.lista_linhas = self.service.obter_linhas()

        if self.tipo_doc == "OS":
            self.colunas_config = {
                "id": "ID", "numero_os": "N° OS", "processo": "Processo", "solicitante": "Solicitante",
                "tipo": "Tipo", "origem": "Origem", "empresa": "Empresa", 
                "linhas": "Linhas", "responsavel": "Responsável", 
                "data_criacao": "Data Criação", "endereco": "Endereço"
            }
        else:
            self.colunas_config = {
                "id": "ID", "numero_completo": "N° Parecer", "processo": "Processo", 
                "origem": "Origem", "assunto": "Assunto", "decisao": "Decisão", 
                "solicitante": "Solicitante", "endereco": "Endereço", 
                "evento": "Evento", "data_criacao": "Data Criação", "responsavel": "Responsável"
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

    def _criar_date_wrapper(self, parent, width=150):
        # Container com borda e tamanho fixo para o visual moderno
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
        
        ctk.CTkButton(header_filtro, text="📄 PDF", width=90, fg_color="#D32F2F", hover_color="#B71C1C", command=self.acao_pdf).pack(side="right", padx=5)
        ctk.CTkButton(header_filtro, text="📊 Excel", width=90, fg_color="#1D6F42", hover_color="#145431", command=self.acao_excel).pack(side="right", padx=5)

        self.grid_filtros = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        self.grid_filtros.pack(fill="x", padx=15, pady=5)
        
        campos_ignorar = ["id", "data_criacao"]
        row, col = 0, 0
        
        # GERAÇÃO INTELIGENTE ZERO HARDCODE
        for key, label in self.colunas_config.items():
            if key in campos_ignorar: continue
            
            f = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
            f.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
            self.grid_filtros.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(f, text=label, font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
            
            if key == "tipo":
                widget = CtkParametrosComboBox(f, setor="Itinerário", campo="TIPO_OS", incluir_todos=True, height=35)
            elif key == "origem":
                widget = CtkParametrosComboBox(f, setor="Itinerário", campo="ORIGEM", incluir_todos=True, height=35)
            elif key == "decisao":
                widget = CtkParametrosComboBox(f, setor="Itinerário", campo="DECISAO_PARECER", incluir_todos=True, height=35)
            elif key in ["solicitante", "assunto", "evento"]:
                campo_map = {
                    "solicitante": "SOLICITANTE_PARECER", 
                    "assunto": "ASSUNTO_ITINERARIO", 
                    "evento": "EVENTO"
                }
                widget = CtkParametrosComboBox(f, setor="Itinerário", campo=campo_map[key], incluir_todos=True, height=35)
            elif key == "empresa":
                widget = Autocomplete(f, values=self.lista_empresas, height=35, placeholder_text="Pesquise o nome...")
            elif key == "linhas":
                widget = Autocomplete(f, values=self.lista_linhas, height=35, placeholder_text="Código ou Nome...")
            else:
                widget = ctk.CTkEntry(f, height=35, placeholder_text=f"Digite {label.lower()}...")

            widget.pack(fill="x")
            self.entradas_filtros[key] = widget
            
            col += 1
            if col > 3: col = 0; row += 1

        f_data = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
        f_data.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(f_data, text="Período (Início - Fim)", font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
        
        f_data_inner = ctk.CTkFrame(f_data, fg_color="transparent")
        f_data_inner.pack(fill="x")
        
        # Substitua a criação direta do DateEntry pelo wrapper
        container_ini, self.date_ini = self._criar_date_wrapper(f_data_inner, 150)
        container_ini.pack(side="left")
        
        ctk.CTkLabel(f_data_inner, text=" até ").pack(side="left", padx=5)
        
        container_fim, self.date_fim = self._criar_date_wrapper(f_data_inner, 150)
        container_fim.pack(side="left")

        self.date_ini.set_date(date(date.today().year, 1, 1))
        self.date_fim.set_date(date.today())

        btn_busca = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        btn_busca.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkButton(btn_busca, text="🔍 Buscar Registros", font=("Arial Bold", 13), width=150, height=35, fg_color="#0F8C75", command=self.acao_buscar).pack(side="left", padx=(5, 10))
        ctk.CTkButton(btn_busca, text="Limpar Filtros", font=("Arial", 13), width=120, height=35, fg_color="transparent", text_color="#666666", hover_color="#F3F4F6", border_width=1, border_color="#D1D5DB", command=self._limpar_filtros).pack(side="left")

        # --- 2. RODAPÉ (AÇÕES E PAGINAÇÃO) ---
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
            # A MÁGICA AQUI: Reconhecendo corretamente os dois componentes criados por você!
            if isinstance(widget, CtkParametrosComboBox):
                widget.set("Todos")
            elif isinstance(widget, Autocomplete):
                widget.set("")
            else:
                widget.delete(0, 'end')
                
        self.date_ini.set_date(date(date.today().year, 1, 1))
        self.date_fim.set_date(date.today())
        self.acao_buscar()

def renderizar(frame_destino, usuario_logado, tipo_doc):
    return RelatoriosItinerarioView(master=frame_destino, usuario_logado=usuario_logado, tipo_doc=tipo_doc)