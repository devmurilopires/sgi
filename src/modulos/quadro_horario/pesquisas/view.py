import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import unicodedata
from src.modulos.quadro_horario.pesquisas.service import PesquisaQuadroHorarioService

HORARIOS = [f"{h:02d}:00 às {h:02d}:59" for h in range(4, 24)]

class CellEditor(tk.Entry):
    def __init__(self, master, tree, item, column, on_commit=None, **kwargs):
        super().__init__(master, **kwargs)
        self.tree, self.item, self.column, self.on_commit = tree, item, column, on_commit
        try: self.insert(0, tree.set(item, column) or ""); self.select_range(0, "end")
        except: pass
        self.focus_set()
        self.bind("<Return>", self._commit)
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<FocusOut>", self._commit)

    def _commit(self, *_):
        try: self.tree.set(self.item, self.column, self.get())
        except: pass
        finally:
            if callable(self.on_commit): self.on_commit(self.tree)
            self.destroy()

def habilitar_edicao_treeview(tree, editable_cols, on_commit=None):
    def on_double_click(event):
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            row = tree.identify_row(event.y)
            col_id = tree.identify_column(event.x)
            col = tree["columns"][int(col_id[1:]) - 1]
            if col in editable_cols:
                x, y, w, h = tree.bbox(row, col)
                parent = tree.nametowidget(tree.winfo_parent())
                editor = CellEditor(parent, tree, row, col, on_commit)
                editor.place(in_=parent, x=x, y=y, width=w, height=h)
        elif region == "heading":
            col_id = tree.identify_column(event.x)
            col = tree["columns"][int(col_id[1:]) - 1]
            if col in editable_cols:
                current = tree.heading(col, "text")
                entry = ttk.Entry(tree)
                entry.insert(0, current); entry.focus(); entry.select_range(0, "end")
                def salvar(*_): 
                    novo = entry.get().strip()
                    if novo: tree.heading(col, text=novo)
                    entry.destroy()
                    if callable(on_commit): on_commit(tree)
                entry.bind("<Return>", salvar); entry.bind("<FocusOut>", salvar)
                left = sum(int(tree.column(c, "width")) for c in tree["columns"][:tree["columns"].index(col)])
                entry.place(in_=tree, x=left, y=0, width=int(tree.column(col, "width")), height=26)
    tree.bind("<Double-1>", on_double_click)

def criar_tabela(parent, titulo, cols_sentido, bg_color, prefixo="sentido"):
    card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10)
    top = ctk.CTkFrame(card, fg_color=bg_color)
    top.pack(fill="x", padx=8, pady=8)
    ctk.CTkLabel(top, text=titulo, font=("Arial Bold", 13)).pack(side="left")
    
    body = ctk.CTkFrame(card, fg_color="white")
    body.pack(fill="both", expand=True, padx=8, pady=8)
    
    cols = ["horario"] + [f"{prefixo}{i+1}" for i in range(cols_sentido)] + ["total"]
    tree = ttk.Treeview(body, columns=cols, show="headings", height=15)
    tree.heading("horario", text="Horário")
    tree.column("horario", width=120, anchor="center")
    for i in range(cols_sentido):
        sc = f"{prefixo}{i+1}"
        tree.heading(sc, text=f"Sentido {i+1}")
        tree.column(sc, width=120, anchor="center")
    tree.heading("total", text="Total")
    tree.column("total", width=80, anchor="center")
    
    for h in HORARIOS: tree.insert("", "end", values=(h,) + ("0",) * cols_sentido + ("0",))
    
    vsb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return card, tree, top

# --- MAIN VIEW ---
class PesquisasView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)
        self.service = PesquisaQuadroHorarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado

        ctk.CTkLabel(self, text="Painel de Pesquisas SPR", font=("Arial Black", 22), text_color="#0F8C75").pack(anchor="w", padx=20, pady=(10,0))

        # A MÁGICA: Uma única aba que abriga as duas pesquisas!
        self.tabs = ctk.CTkTabview(self, fg_color="#F2F2F2", corner_radius=10)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_tempo = self.tabs.add("Tempo de Viagem")
        self.tab_demanda = self.tabs.add("Demanda")

        self._construir_aba_tempo()
        self._construir_aba_demanda()

    # ==========================================
    # ABA 1: TEMPO DE VIAGEM
    # ==========================================
    def _construir_aba_tempo(self):
        container = ctk.CTkScrollableFrame(self.tab_tempo, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        self.t_cinzas = []
        for i in range(3):
            card, tree, top = criar_tabela(row1, f"Relatório {i+1}", 2, "#EDEDED", "sentido")
            card.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkButton(top, text="📥 Excel", width=80, command=lambda t=tree: self._carregar_excel(t, 'tempo')).pack(side="right")
            habilitar_edicao_treeview(tree, ["sentido1", "sentido2"], self._update_tempo_all)
            self.t_cinzas.append(tree)

        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="x", pady=10)
        _, self.t_amarela, _ = criar_tabela(row2, "Média Tempo Real", 2, "#F8D057", "s")
        _, self.t_verde, top_verde = criar_tabela(row2, "Quadro Atual", 2, "#96D37A", "s")
        _, self.t_azul, _ = criar_tabela(row2, "Diferença", 2, "#70ADE7", "s")
        
        for card in [self.t_amarela.master.master, self.t_verde.master.master, self.t_azul.master.master]:
            card.pack(side="left", fill="both", expand=True, padx=5)
            
        ctk.CTkButton(top_verde, text="📥 Excel", width=80, command=lambda: self._carregar_excel(self.t_verde, 'verde')).pack(side="right")
        
        habilitar_edicao_treeview(self.t_amarela, ["s1", "s2"], self._update_tempo_all)
        habilitar_edicao_treeview(self.t_verde, ["s1", "s2"], self._update_tempo_all)

        ctk.CTkButton(container, text="💾 Salvar Pesquisa de Tempo", fg_color="#0F8C75", height=40, command=lambda: self._salvar_banco("tempo")).pack(pady=15)

    def _update_tempo_all(self, trigger_tree=None):
        # 1. Totaliza Cinzas
        for t in self.t_cinzas: self._somar_linha(t)
        # 2. Calcula Média Amarela
        for item in self.t_amarela.get_children():
            h_int = int(self.t_amarela.set(item, "horario").split(":")[0])
            for i in range(1, 3):
                vals = [float(t.set(it, f"sentido{i}") or 0) for t in self.t_cinzas for it in t.get_children() if int(t.set(it, "horario").split(":")[0]) == h_int and float(t.set(it, f"sentido{i}") or 0) > 0]
                media = math.ceil(sum(vals)/len(vals)) if vals else 0
                self.t_amarela.set(item, f"s{i}", str(media))
        self._somar_linha(self.t_amarela)
        # 3. Calcula Diferença Azul (Verde - Amarela)
        for item in self.t_azul.get_children():
            h_int = int(self.t_azul.set(item, "horario").split(":")[0])
            item_a = next(i for i in self.t_amarela.get_children() if int(self.t_amarela.set(i, "horario").split(":")[0]) == h_int)
            item_v = next(i for i in self.t_verde.get_children() if int(self.t_verde.set(i, "horario").split(":")[0]) == h_int)
            for i in range(1, 3):
                diff = int(float(self.t_verde.set(item_v, f"s{i}") or 0)) - int(float(self.t_amarela.set(item_a, f"s{i}") or 0))
                self.t_azul.set(item, f"s{i}", str(diff))
        self._somar_linha(self.t_azul)

    # ==========================================
    # ABA 2: DEMANDA
    # ==========================================
    def _construir_aba_demanda(self):
        container = ctk.CTkScrollableFrame(self.tab_demanda, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        self.d_cinzas = []
        for i in range(3):
            card, tree, top = criar_tabela(row1, f"Relatório Demanda {i+1}", 2, "#EDEDED", "sentido")
            card.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkButton(top, text="📥 Excel", width=80, command=lambda t=tree: self._carregar_excel(t, 'demanda')).pack(side="right")
            habilitar_edicao_treeview(tree, ["sentido1", "sentido2"], self._update_demanda_all)
            self.d_cinzas.append(tree)

        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="x", pady=10)
        _, self.d_amarela, _ = criar_tabela(row2, "Média Demanda", 2, "#F8D057", "s")
        _, self.d_viagens, top_viagens = criar_tabela(row2, "Nº de Viagens", 2, "#70ADE7", "s")
        _, self.d_pass, _ = criar_tabela(row2, "Passageiro/Viagem", 2, "#96D37A", "s")
        
        for card in [self.d_amarela.master.master, self.d_viagens.master.master, self.d_pass.master.master]:
            card.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkButton(top_viagens, text="📥 Excel", width=80, command=lambda: self._carregar_excel(self.d_viagens, 'viagens')).pack(side="right")
        habilitar_edicao_treeview(self.d_viagens, ["s1", "s2"], self._update_demanda_all)

        ctk.CTkButton(container, text="💾 Salvar Pesquisa de Demanda", fg_color="#0F8C75", height=40, command=lambda: self._salvar_banco("demanda")).pack(pady=15)

    def _update_demanda_all(self, trigger_tree=None):
        for t in self.d_cinzas: self._somar_linha(t)
        # Media Amarela
        for item in self.d_amarela.get_children():
            h_int = int(self.d_amarela.set(item, "horario").split(":")[0])
            for i in range(1, 3):
                vals = [float(t.set(it, f"sentido{i}") or 0) for t in self.d_cinzas for it in t.get_children() if int(t.set(it, "horario").split(":")[0]) == h_int and float(t.set(it, f"sentido{i}") or 0) > 0]
                self.d_amarela.set(item, f"s{i}", str(math.ceil(sum(vals)/len(vals)) if vals else 0))
        self._somar_linha(self.d_amarela)
        self._somar_linha(self.d_viagens)
        # Pass/Viagem
        for item in self.d_pass.get_children():
            h_int = int(self.d_pass.set(item, "horario").split(":")[0])
            item_a = next(i for i in self.d_amarela.get_children() if int(self.d_amarela.set(i, "horario").split(":")[0]) == h_int)
            item_v = next(i for i in self.d_viagens.get_children() if int(self.d_viagens.set(i, "horario").split(":")[0]) == h_int)
            for i in range(1, 3):
                v_viag = int(float(self.d_viagens.set(item_v, f"s{i}") or 0))
                v_amar = int(float(self.d_amarela.set(item_a, f"s{i}") or 0))
                self.d_pass.set(item, f"s{i}", str(math.ceil(v_amar/v_viag) if v_viag > 0 else 0))
        self._somar_linha(self.d_pass)

    # ==========================================
    # UTILITÁRIOS GERAIS
    # ==========================================
    def _somar_linha(self, tree):
        cols = [c for c in tree["columns"] if c.startswith("s")]
        for item in tree.get_children():
            tree.set(item, "total", str(math.ceil(sum(float(tree.set(item, c) or 0) for c in cols))))

    def _obter_nomes_sentidos(self, tree):
        return {unicodedata.normalize("NFD", tree.heading(c, "text").lower().strip()).encode("ascii", "ignore").decode("utf-8").replace(" ", ""): c for c in tree["columns"] if c.startswith("s")}

    def _carregar_excel(self, tree, tipo_processamento):
        caminho = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not caminho: return
        
        ns = self._obter_nomes_sentidos(tree)
        sucesso, dados = False, {}
        
        if tipo_processamento == 'tempo': sucesso, dados = self.service.processar_excel_tempo(caminho, ns)
        elif tipo_processamento == 'verde': sucesso, dados = self.service.processar_excel_verde(caminho, ns)
        elif tipo_processamento == 'demanda': sucesso, dados = self.service.processar_excel_demanda(caminho, ns)
        elif tipo_processamento == 'viagens': sucesso, dados = self.service.processar_excel_viagens(caminho, ns)

        if not sucesso: return messagebox.showerror("Erro", dados)

        for item in tree.get_children():
            h_int = int(tree.set(item, "horario").split(":")[0])
            for col, vals in dados.items():
                if h_int in vals: tree.set(item, col, str(vals[h_int]))

        if tipo_processamento in ['tempo', 'verde']: self._update_tempo_all()
        else: self._update_demanda_all()

    def _salvar_banco(self, tipo_pesquisa):
        dialog = ctk.CTkInputDialog(text="Digite um Título para a Pesquisa:", title="Salvar Pesquisa")
        titulo = dialog.get_input()
        if not titulo: return
        
        # Serializa tabelas da aba ativa
        tabelas = []
        trees = [self.t_amarela, self.t_verde, self.t_azul] if tipo_pesquisa == "tempo" else [self.d_amarela, self.d_viagens, self.d_pass]
        
        for idx, t in enumerate(trees):
            rows = []
            for item in t.get_children():
                rows.append([t.set(item, c) for c in t["columns"]])
            tabelas.append({
                "tabela": f"Resumo {idx+1}",
                "colunas": [t.heading(c, "text") for c in t["columns"]],
                "linhas": rows
            })
            
        ok, msg = self.service.salvar_dados(titulo, tipo_pesquisa, tabelas, self.usuario_logado)
        messagebox.showinfo("Resultado", msg)

def renderizar(frame_destino, usuario_logado):
    return PesquisasView(master=frame_destino, usuario_logado=usuario_logado)