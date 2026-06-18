import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import unicodedata
from tkcalendar import DateEntry
from src.modulos.quadro_horario.pesquisas.service import PesquisaQuadroHorarioService
from src.core.shared.colors import COLOR_PRIMARY, COLOR_BG, COLOR_TEXT, COLOR_WHITE,COLOR_HOVER


HORARIOS = [f"{h:02d}:00 às {h:02d}:59" for h in range(4, 24)]

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

        # Busca inteligente: funciona para "052", "Grande" ou "Circular"
        filtradas = [linha for linha in self.lista_sugestoes if texto in linha.lower()][:15]
        if filtradas:
            self.mostrar_lista(filtradas)
        else:
            self.esconder_lista()

    def mostrar_lista(self, filtradas):
        self.esconder_lista()
        toplevel = self.winfo_toplevel()
        if not toplevel.winfo_exists(): return
        
        x = self.winfo_rootx() - toplevel.winfo_rootx()
        y = self.winfo_rooty() - toplevel.winfo_rooty() + self.winfo_height() + 2
        w = self.winfo_width()
        h = min(180, len(filtradas) * 26 + 5)
        
        self.listbox_frame = ctk.CTkFrame(toplevel, fg_color=COLOR_BG, border_width=1, border_color=COLOR_PRIMARY, corner_radius=6, width=w, height=h)
        self.listbox_frame.place(x=x, y=y)
        self.listbox_frame.pack_propagate(False)
        
        self.listbox_widget = tk.Listbox(self.listbox_frame, bg=COLOR_BG, fg=COLOR_TEXT, selectbackground=COLOR_PRIMARY, selectforeground=COLOR_WHITE, bd=0, highlightthickness=0, font=("Arial", 11))
        self.listbox_widget.pack(side="left", fill="both", expand=True, padx=3, pady=3)
        
        scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.listbox_widget.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox_widget.config(yscrollcommand=scrollbar.set)
        
        for item in filtradas:
            self.listbox_widget.insert(tk.END, item)
            
        self.selecao_idx = -1
        self.listbox_widget.bind("<<ListboxSelect>>", self.on_listbox_click)
        self.listbox_frame.lift()

    def esconder_lista(self, event=None):
        if self.listbox_frame and self.listbox_frame.winfo_exists():
            self.listbox_frame.destroy()
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

def habilitar_edicao_treeview(tree, view_instance, on_commit=None):
    def on_double_click(event):
        region = tree.identify("region", event.x, event.y)
        if region == "cell":
            row = tree.identify_row(event.y)
            col_id = tree.identify_column(event.x)
            col = tree["columns"][int(col_id[1:]) - 1]
            
            if col.startswith("s"):
                num_col = int(col.replace("s", ""))
                if num_col <= view_instance.num_sentidos:
                    x, y, w, h = tree.bbox(row, col)
                    parent = tree.nametowidget(tree.winfo_parent())
                    editor = CellEditor(parent, tree, row, col, on_commit)
                    editor.place(in_=parent, x=x, y=y, width=w, height=h)
        
        elif region == "heading":
            col_id = tree.identify_column(event.x)
            col = tree["columns"][int(col_id[1:]) - 1]
            
            if col.startswith("s"):
                num_col = int(col.replace("s", ""))
                if num_col <= view_instance.num_sentidos:
                    current = tree.heading(col, "text")
                    entry = ttk.Entry(tree)
                    entry.insert(0, current); entry.focus(); entry.select_range(0, "end")
                    
                    def salvar(*_): 
                        novo = entry.get().strip()
                        if novo: 
                            for t in view_instance.all_trees:
                                t.heading(col, text=novo)
                        entry.destroy()
                        if callable(on_commit): on_commit(tree)
                        
                    entry.bind("<Return>", salvar)
                    entry.bind("<FocusOut>", salvar)
                    
                    left = sum(int(tree.column(c, "width")) for c in tree["columns"][:tree["columns"].index(col)])
                    entry.place(in_=tree, x=left, y=0, width=int(tree.column(col, "width")), height=26)
                    
    tree.bind("<Double-1>", on_double_click)


def criar_tabela(parent, titulo, bg_color, is_cinza=False):
    card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10)
    top = ctk.CTkFrame(card, fg_color=bg_color)
    top.pack(fill="x", padx=8, pady=8)
    ctk.CTkLabel(top, text=titulo, font=("Arial Bold", 13), text_color=COLOR_TEXT).pack(side="left")
    
    date_entry_widget = None
    if is_cinza:
        data_frame = ctk.CTkFrame(top, width=110, height=28, fg_color=COLOR_BG, border_width=1, border_color=COLOR_TEXT, corner_radius=6)
        data_frame.pack_propagate(False)
        data_frame.pack(side="left", padx=10)
        date_entry_widget = DateEntry(data_frame, date_pattern="dd/mm/yyyy", font=("Arial", 10), background=COLOR_PRIMARY, foreground=COLOR_WHITE, borderwidth=0)
        date_entry_widget.pack(fill="both", expand=True, padx=2, pady=2)
    
    body = ctk.CTkFrame(card, fg_color=COLOR_BG)
    body.pack(fill="both", expand=True, padx=8, pady=8)
    
    cols = ["horario", "s1", "s2", "s3", "s4", "total"]
    tree = ttk.Treeview(body, columns=cols, show="headings", height=12)
    
    tree.heading("horario", text="Horário")
    tree.column("horario", width=90, minwidth=10, stretch=True, anchor="center")
    
    for i in range(1, 5):
        sc = f"s{i}"
        tree.heading(sc, text=f"Sentido {i}")
        w = 80 if i <= 2 else 0
        stretch = True if i <= 2 else False
        tree.column(sc, width=w, minwidth=(10 if stretch else 0), stretch=stretch, anchor="center")
        
    tree.heading("total", text="Total")
    tree.column("total", width=60, minwidth=10, stretch=True, anchor="center")
    
    for h in HORARIOS: tree.insert("", "end", values=(h, "0", "0", "0", "0", "0"))
    
    vsb = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    
    return card, tree, top, date_entry_widget

class PesquisasView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)
        self.service = PesquisaQuadroHorarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        
        self.num_sentidos = 2 
        self.all_trees = [] 
        self.date_widgets_tempo = []
        self.date_widgets_demanda = []

        self._construir_interface()

    def _construir_interface(self):
        top_bar = ctk.CTkFrame(self, fg_color=COLOR_WHITE, height=70, corner_radius=0)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        action_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        action_frame.pack(side="left", fill="y", padx=20, pady=15)
        
        ctk.CTkButton(action_frame, text="➕ Sentido", font=("Arial Bold", 12), fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, width=90, height=35, command=self._add_sentido).pack(side="left", padx=(0, 5))
        ctk.CTkButton(action_frame, text="➖ Sentido", font=("Arial Bold", 12), fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, width=90, height=35, command=self._rem_sentido).pack(side="left", padx=(0, 15))
        ctk.CTkButton(action_frame, text="🔄 Zerar Grade", font=("Arial Bold", 12), fg_color=COLOR_TEXT, hover_color=COLOR_HOVER, width=100, height=35, command=self._resetar).pack(side="left", padx=(0, 5))
        ctk.CTkButton(action_frame, text="💾 Salvar Pesquisa", font=("Arial Bold", 13), fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, width=130, height=35, command=self._abrir_popup_salvar).pack(side="left")

        self.modo_view = ctk.StringVar(value="Tempo de Viagem")
        tabs = ctk.CTkSegmentedButton(top_bar, values=["Tempo de Viagem", "Demanda"], variable=self.modo_view, font=("Arial Bold", 13), height=35, selected_color=COLOR_PRIMARY, selected_hover_color=COLOR_HOVER, command=self._trocar_aba)
        tabs.pack(side="right", padx=20, pady=17)

        self.container_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.container_principal.pack(fill="both", expand=True, padx=15, pady=10)

        self.frame_tempo = ctk.CTkFrame(self.container_principal, fg_color="transparent")
        self.frame_demanda = ctk.CTkFrame(self.container_principal, fg_color="transparent")

        self._construir_aba_tempo()
        self._construir_aba_demanda()
        self.frame_tempo.pack(fill="both", expand=True) 

    def _trocar_aba(self, value):
        self.frame_tempo.pack_forget()
        self.frame_demanda.pack_forget()
        if value == "Tempo de Viagem": self.frame_tempo.pack(fill="both", expand=True)
        else: self.frame_demanda.pack(fill="both", expand=True)

    def _add_sentido(self):
        if self.num_sentidos < 4:
            self.num_sentidos += 1
            col_id = f"s{self.num_sentidos}"
            for t in self.all_trees:
                t.column(col_id, width=70, minwidth=10, stretch=True)
            self._recalcular_tudo()

    def _rem_sentido(self):
        if self.num_sentidos > 2:
            col_id = f"s{self.num_sentidos}"
            for t in self.all_trees:
                t.column(col_id, width=0, minwidth=0, stretch=False)
            self.num_sentidos -= 1
            self._recalcular_tudo()
            
    def _recalcular_tudo(self):
        self._update_tempo_all()
        self._update_demanda_all()

    def _resetar(self):
        if not messagebox.askyesno("Confirmar", "Deseja realmente zerar todos os dados?"): return
        self.num_sentidos = 2
        for t in self.all_trees:
            t.column("s3", width=0, minwidth=0, stretch=False); t.heading("s3", text="Sentido 3")
            t.column("s4", width=0, minwidth=0, stretch=False); t.heading("s4", text="Sentido 4")
            for item in t.get_children():
                t.set(item, "s1", "0"); t.set(item, "s2", "0")
                t.set(item, "s3", "0"); t.set(item, "s4", "0")
                t.set(item, "total", "0")

    def _abrir_popup_salvar(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Salvar Pesquisa")
        popup.geometry("450x250")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Selecione a Linha da Pesquisa", font=("Arial Black", 16), text_color=COLOR_PRIMARY).pack(pady=(20, 10))

        # Agora as sugestões virão no formato "Código - Nome"
        linhas = self.service.buscar_sugestoes_linhas()
        
        cb_linha = Autocomplete(popup, values=linhas, width=320, height=40, placeholder_text="Digite o código ou nome da linha...")
        cb_linha.pack(pady=10)
        cb_linha.focus_set()

        def confirmar():
            linha_sel = cb_linha.get().strip()
            if not linha_sel: return messagebox.showwarning("Aviso", "Selecione uma linha.")
            
            tipo = "tempo" if self.modo_view.get() == "Tempo de Viagem" else "demanda"
            
            if tipo == "tempo":
                trees = self.t_cinzas + [self.t_amarela, self.t_verde, self.t_azul]
                nomes_tabelas = ["Relatório 1", "Relatório 2", "Relatório 3", "Média Tempo Real", "Quadro Atual", "Diferença"]
                date_widgets = self.date_widgets_tempo
            else:
                trees = self.d_cinzas + [self.d_amarela, self.d_viagens, self.d_pass]
                nomes_tabelas = ["Relatório Demanda 1", "Relatório Demanda 2", "Relatório Demanda 3", "Média Demanda", "Nº de Viagens", "Passageiro/Viagem"]
                date_widgets = self.date_widgets_demanda
            
            datas_selecionadas = [d.get() for d in date_widgets]
            colunas_visiveis = ["horario"] + [f"s{i}" for i in range(1, self.num_sentidos + 1)] + ["total"]
            
            tabelas = []
            for idx, t in enumerate(trees):
                rows = []
                for item in t.get_children():
                    rows.append([t.set(item, c) for c in colunas_visiveis])
                tabelas.append({
                    "tabela": nomes_tabelas[idx],
                    "colunas": [t.heading(c, "text") for c in colunas_visiveis],
                    "linhas": rows
                })

            dados_completos = {"datas": datas_selecionadas, "tabelas": tabelas}
            ok, msg = self.service.salvar_dados(linha_sel, tipo, dados_completos, self.usuario_logado)
            if ok:
                messagebox.showinfo("Sucesso", msg)
                popup.destroy()
            else:
                messagebox.showerror("Erro", msg)

        # Atalho: Selecionou na lista ou deu Enter -> Valida a pesquisa
        cb_linha.bind("<<AutocompleteSelected>>", lambda e: confirmar())
        
        ctk.CTkButton(popup, text="Salvar no Banco de Dados", fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, font=("Arial Bold", 14), height=45, command=confirmar).pack(pady=(15,0))
        
    def _construir_aba_tempo(self):
        row1 = ctk.CTkFrame(self.frame_tempo, fg_color="transparent")
        row1.pack(fill="both", expand=True, pady=5)
        self.t_cinzas = []
        for i in range(3):
            card, tree, top, date_entry = criar_tabela(row1, f"Relatório {i+1}",COLOR_BG, is_cinza=True)
            card.pack(side="left", fill="both", expand=True, padx=5)
            self.date_widgets_tempo.append(date_entry)
            ctk.CTkButton(top, text="📥 Excel", width=70, height=28, fg_color=COLOR_TEXT, text_color=COLOR_WHITE, hover_color=COLOR_HOVER, command=lambda t=tree: self._carregar_excel(t, 'tempo')).pack(side="right")
            habilitar_edicao_treeview(tree, self, self._update_tempo_all)
            self.t_cinzas.append(tree)
            self.all_trees.append(tree)

        row2 = ctk.CTkFrame(self.frame_tempo, fg_color="transparent")
        row2.pack(fill="both", expand=True, pady=10)
        card_a, self.t_amarela, _, _ = criar_tabela(row2, "Média Tempo Real", "#F8D057")
        card_v, self.t_verde, top_verde, _ = criar_tabela(row2, "Quadro Atual", "#96D37A")
        card_az, self.t_azul, _, _ = criar_tabela(row2, "Diferença", "#70ADE7")
        for card in [card_a, card_v, card_az]: card.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkButton(top_verde, text="📥 Excel", width=70, height=28, fg_color=COLOR_TEXT, text_color=COLOR_WHITE, hover_color=COLOR_HOVER, command=lambda: self._carregar_excel(self.t_verde, 'verde')).pack(side="right")
        habilitar_edicao_treeview(self.t_amarela, self, self._update_tempo_all)
        habilitar_edicao_treeview(self.t_verde, self, self._update_tempo_all)
        self.all_trees.extend([self.t_amarela, self.t_verde, self.t_azul])

    def _update_tempo_all(self, trigger_tree=None):
        for t in self.t_cinzas: self._somar_linha(t)
        for item in self.t_amarela.get_children():
            h_int = int(self.t_amarela.set(item, "horario").split(":")[0])
            for i in range(1, self.num_sentidos + 1):
                vals = [float(t.set(it, f"s{i}") or 0) for t in self.t_cinzas for it in t.get_children() if int(t.set(it, "horario").split(":")[0]) == h_int and float(t.set(it, f"s{i}") or 0) > 0]
                media = math.ceil(sum(vals)/len(vals)) if vals else 0
                self.t_amarela.set(item, f"s{i}", str(media))
        self._somar_linha(self.t_amarela)
        for item in self.t_azul.get_children():
            h_int = int(self.t_azul.set(item, "horario").split(":")[0])
            item_a = next(i for i in self.t_amarela.get_children() if int(self.t_amarela.set(i, "horario").split(":")[0]) == h_int)
            item_v = next(i for i in self.t_verde.get_children() if int(self.t_verde.set(i, "horario").split(":")[0]) == h_int)
            for i in range(1, self.num_sentidos + 1):
                diff = int(float(self.t_verde.set(item_v, f"s{i}") or 0)) - int(float(self.t_amarela.set(item_a, f"s{i}") or 0))
                self.t_azul.set(item, f"s{i}", str(diff))
        self._somar_linha(self.t_azul)

    def _construir_aba_demanda(self):
        row1 = ctk.CTkFrame(self.frame_demanda, fg_color="transparent")
        row1.pack(fill="both", expand=True, pady=5)
        self.d_cinzas = []
        for i in range(3):
            card, tree, top, date_entry = criar_tabela(row1, f"Relatório Demanda {i+1}", COLOR_BG, is_cinza=True)
            card.pack(side="left", fill="both", expand=True, padx=5)
            self.date_widgets_demanda.append(date_entry)
            ctk.CTkButton(top, text="📥 Excel", width=70, height=28, fg_color=COLOR_TEXT, text_color=COLOR_WHITE ,hover_color=COLOR_HOVER, command=lambda t=tree: self._carregar_excel(t, 'demanda')).pack(side="right")
            habilitar_edicao_treeview(tree, self, self._update_demanda_all)
            self.d_cinzas.append(tree)
            self.all_trees.append(tree)

        row2 = ctk.CTkFrame(self.frame_demanda, fg_color="transparent")
        row2.pack(fill="both", expand=True, pady=10)
        card_a, self.d_amarela, _, _ = criar_tabela(row2, "Média Demanda", "#F8D057")
        card_v, self.d_viagens, top_viagens, _ = criar_tabela(row2, "Nº de Viagens", "#96D37A")
        card_p, self.d_pass, _, _ = criar_tabela(row2, "Passageiro/Viagem", "#70ADE7")
        for card in [card_a, card_v, card_p]: card.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkButton(top_viagens, text="📥 Excel", width=70, height=28, text_color=COLOR_WHITE, fg_color=COLOR_TEXT, hover_color=COLOR_HOVER, command=lambda: self._carregar_excel(self.d_viagens, 'viagens')).pack(side="right")
        habilitar_edicao_treeview(self.d_viagens, self, self._update_demanda_all)
        self.all_trees.extend([self.d_amarela, self.d_viagens, self.d_pass])

    def _update_demanda_all(self, trigger_tree=None):
        for t in self.d_cinzas: self._somar_linha(t)
        for item in self.d_amarela.get_children():
            h_int = int(self.d_amarela.set(item, "horario").split(":")[0])
            for i in range(1, self.num_sentidos + 1):
                vals = [float(t.set(it, f"s{i}") or 0) for t in self.d_cinzas for it in t.get_children() if int(t.set(it, "horario").split(":")[0]) == h_int and float(t.set(it, f"s{i}") or 0) > 0]
                self.d_amarela.set(item, f"s{i}", str(math.ceil(sum(vals)/len(vals)) if vals else 0))
        self._somar_linha(self.d_amarela)
        self._somar_linha(self.d_viagens)
        for item in self.d_pass.get_children():
            h_int = int(self.d_pass.set(item, "horario").split(":")[0])
            item_a = next(i for i in self.d_amarela.get_children() if int(self.d_amarela.set(i, "horario").split(":")[0]) == h_int)
            item_v = next(i for i in self.d_viagens.get_children() if int(self.d_viagens.set(i, "horario").split(":")[0]) == h_int)
            for i in range(1, self.num_sentidos + 1):
                v_viag = int(float(self.d_viagens.set(item_v, f"s{i}") or 0))
                v_amar = int(float(self.d_amarela.set(item_a, f"s{i}") or 0))
                self.d_pass.set(item, f"s{i}", str(math.ceil(v_amar/v_viag) if v_viag > 0 else 0))
        self._somar_linha(self.d_pass)

    def _somar_linha(self, tree):
        cols = [f"s{i}" for i in range(1, self.num_sentidos + 1)]
        for item in tree.get_children():
            tree.set(item, "total", str(math.ceil(sum(float(tree.set(item, c) or 0) for c in cols))))

    def _obter_nomes_sentidos(self, tree):
        return {unicodedata.normalize("NFD", tree.heading(f"s{i}", "text").lower().strip()).encode("ascii", "ignore").decode("utf-8").replace(" ", ""): f"s{i}" for i in range(1, self.num_sentidos + 1)}

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
                num_col = int(col.replace("s", ""))
                if num_col <= self.num_sentidos:
                    if h_int in vals: tree.set(item, col, str(vals[h_int]))
        if tipo_processamento in ['tempo', 'verde']: self._update_tempo_all()
        else: self._update_demanda_all()

def renderizar(frame_destino, usuario_logado):
    return PesquisasView(master=frame_destino, usuario_logado=usuario_logado)