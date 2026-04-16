import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import math
from src.modulos.itinerario.relatorios.service import RelatoriosItinerarioService

class RelatoriosItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado, tipo_doc):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)
        
        self.service = RelatoriosItinerarioService()
        self.usuario = usuario_logado
        self.is_admin = usuario_logado.get("is_admin", False)
        self.tipo_doc = tipo_doc.upper()
        
        self.pagina_atual = 1
        self.itens_por_pagina = 20
        self.entradas_filtros = {}
        self.dados_atuais = []

        if self.tipo_doc == "OS":
            self.colunas_config = {
                "id": "ID", "numero_os": "N° OS", "processo": "Processo", 
                "tipo": "Tipo", "origem": "Origem", "empresa": "Empresa", 
                "linhas": "Linhas", "responsavel": "Responsável", 
                "data_criacao": "Data Criação", "endereco": "Endereço"
            }
        else:
            self.colunas_config = {
                "id": "ID", "numero_parecer_ano": "N° Parecer", "processo": "Processo", 
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
        # Visual Moderno da Tabela
        style.configure("Modern.Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", 
                        rowheight=38, font=("Arial", 11), borderwidth=0)
        style.configure("Modern.Treeview.Heading", font=("Arial Bold", 11), 
                        background="#E9ECEF", foreground="#333333", borderwidth=0, padding=(0, 5))
        style.map("Modern.Treeview", background=[('selected', '#0F8C75')], foreground=[('selected', 'white')])
        style.map("Modern.Treeview.Heading", background=[('active', '#D1D5DB')])

    def _construir_interface(self):
        # --- CONTAINER DE FILTROS (Card Moderno) ---
        self.frame_top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.frame_top.pack(fill="x", padx=20, pady=(20, 10))
        
        # Cabeçalho do Card
        header_filtro = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        header_filtro.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header_filtro, text=f"Filtros de Pesquisa - {self.tipo_doc}", font=("Arial Black", 16), text_color="#0F8C75").pack(side="left")
        
        # Ações de Exportação no Topo
        ctk.CTkButton(header_filtro, text="📄 PDF", width=90, fg_color="#D32F2F", hover_color="#B71C1C", command=self.acao_pdf).pack(side="right", padx=5)
        ctk.CTkButton(header_filtro, text="📊 Excel", width=90, fg_color="#1D6F42", hover_color="#145431", command=self.acao_excel).pack(side="right", padx=5)

        # Grid Dinâmico
        self.grid_filtros = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        self.grid_filtros.pack(fill="x", padx=15, pady=5)
        
        campos_ignorar = ["id", "data_criacao"]
        row, col = 0, 0
        for key, label in self.colunas_config.items():
            if key in campos_ignorar: continue
            
            f = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
            f.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
            self.grid_filtros.grid_columnconfigure(col, weight=1) # Distribuição igual
            
            ctk.CTkLabel(f, text=label, font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
            entry = ctk.CTkEntry(f, height=35, placeholder_text=f"Digite {label.lower()}...", border_color="#D1D5DB", fg_color="#F9FAFB")
            entry.pack(fill="x")
            self.entradas_filtros[key] = entry
            
            col += 1
            if col > 3: col = 0; row += 1

        # Filtros de Data
        f_data = ctk.CTkFrame(self.grid_filtros, fg_color="transparent")
        f_data.grid(row=row, column=col, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(f_data, text="Período (Início - Fim)", font=("Arial Bold", 11), text_color="#666666").pack(anchor="w")
        
        f_data_inner = ctk.CTkFrame(f_data, fg_color="transparent")
        f_data_inner.pack(fill="x")
        self.date_ini = DateEntry(f_data_inner, width=12, background='#0F8C75', locale='pt_BR')
        self.date_ini.pack(side="left")
        ctk.CTkLabel(f_data_inner, text=" até ").pack(side="left", padx=5)
        self.date_fim = DateEntry(f_data_inner, width=12, background='#0F8C75', locale='pt_BR')
        self.date_fim.pack(side="left")

        # Botões de Busca
        btn_busca = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        btn_busca.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkButton(btn_busca, text="🔍 Buscar Registros", font=("Arial Bold", 13), width=150, height=35, fg_color="#0F8C75", command=self.acao_buscar).pack(side="left", padx=(5, 10))
        ctk.CTkButton(btn_busca, text="Limpar Filtros", font=("Arial", 13), width=120, height=35, fg_color="transparent", text_color="#666666", hover_color="#F3F4F6", border_width=1, border_color="#D1D5DB", command=self._limpar_filtros).pack(side="left")

        # --- CONTAINER DA TABELA (Card Moderno) ---
        self.frame_tabela = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.frame_tabela.pack(fill="both", expand=True, padx=20, pady=5)

        cols = list(self.colunas_config.keys())
        self.tree = ttk.Treeview(self.frame_tabela, columns=cols, show="headings", style="Modern.Treeview")
        
        # Tags para Zebrar a tabela
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

        # --- RODAPÉ ---
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bottom.pack(fill="x", padx=20, pady=(5, 20))
        
        self.lbl_pag = ctk.CTkLabel(self.frame_bottom, text="Página 1 de 1", font=("Arial Bold", 12), text_color="#555555")
        self.lbl_pag.pack(side="left", padx=10)
        
        # Ações principais
        ctk.CTkButton(self.frame_bottom, text="👁️ Ver Detalhes", font=("Arial Bold", 13), width=140, height=35, fg_color="#374151", hover_color="#1F2937", command=self.acao_detalhes).pack(side="right", padx=5)
        ctk.CTkButton(self.frame_bottom, text="📂 Abrir Documento", font=("Arial Bold", 13), width=160, height=35, fg_color="#0F8C75", hover_color="#0B6B59", command=self.acao_abrir).pack(side="right", padx=5)
        
        if self.is_admin:
            ctk.CTkButton(self.frame_bottom, text="🗑️ Excluir", font=("Arial Bold", 13), width=120, height=35, fg_color="transparent", border_width=1, border_color="#D32F2F", text_color="#D32F2F", hover_color="#FEE2E2", command=self.acao_excluir).pack(side="right", padx=(5, 20))

    def _get_filtros_formatados(self):
        filtros = {k: v.get().strip() for k, v in self.entradas_filtros.items()}
        filtros["data_inicio"] = self.date_ini.get_date()
        filtros["data_fim"] = self.date_fim.get_date()
        return filtros

    def acao_buscar(self):
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
            
        total_pags = math.ceil(total / self.itens_por_pagina) or 1
        self.lbl_pag.configure(text=f"Página {self.pagina_atual} de {total_pags} (Total: {total} registros)")

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

        # Container de Dados Pessoais/Gerais
        info_frame = ctk.CTkFrame(scroll, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E5E7EB")
        info_frame.pack(fill="x", pady=10)

        row_idx = 0
        grid = ctk.CTkFrame(info_frame, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=15)
        
        # Filtra os dados vazios para não poluir
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

        # Caminho do Arquivo (Destacado)
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
        for e in self.entradas_filtros.values(): e.delete(0, 'end')
        self.acao_buscar()

def renderizar(frame_destino, usuario_logado, tipo_doc):
    return RelatoriosItinerarioView(master=frame_destino, usuario_logado=usuario_logado, tipo_doc=tipo_doc)