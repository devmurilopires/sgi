import customtkinter as ctk
import tkinter as tk
import math
from tkinter import ttk, messagebox
from src.modulos.ponto_parada.enderecos.service import EnderecoService
from src.core.shared.colors import COLOR_PRIMARY, COLOR_SECONDARY, COLOR_BG, COLOR_TEXT, COLOR_WHITE, COLOR_TERTIARY, COLOR_QUATERNARY, COLOR_HOVER
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

    def atualizar_sugestoes(self, novas_sugestoes):
        self.lista_sugestoes = novas_sugestoes

    def on_keyrelease(self, event):
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
        
        self.listbox_frame = ctk.CTkFrame(toplevel, fg_color=COLOR_WHITE, border_width=1, border_color=COLOR_PRIMARY, corner_radius=6, width=w, height=h)
        self.listbox_frame.place(x=x, y=y)
        self.listbox_frame.pack_propagate(False)
        
        self.listbox_widget = tk.Listbox(self.listbox_frame, bg=COLOR_WHITE, fg=COLOR_TEXT, selectbackground=COLOR_PRIMARY, selectforeground=COLOR_WHITE, bd=0, highlightthickness=0, font=("Arial", 11))
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


class CadastroEnderecoView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)
        
        self.usuario_logado = usuario_logado
        self.service = EnderecoService()
        
        # Variáveis de Paginação
        self.pagina_atual = 1
        self.itens_por_pagina = 50
        self.total_paginas = 1
        self.termo_busca = ""
        self.dados_atuais = []

        self._construir_interface()
        self.acao_buscar()

    def _construir_interface(self):
        # TOPO
        header = ctk.CTkFrame(self, fg_color=COLOR_WHITE, height=60, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Gestão de Ponto de Parada (Endereços)", font=("Arial Black", 20), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=15)

        btn_exportar = ctk.CTkButton(header, text="📥 EXPORTAR EXCEL", font=("Arial Bold", 12), fg_color=COLOR_SECONDARY, hover_color="#1E8449", command=self.acao_exportar)
        btn_exportar.pack(side="right", padx=20, pady=15)

        btn_padronizar = ctk.CTkButton(header, text="📝 PADRONIZAR BAIRROS", font=("Arial Bold", 12), fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, command=self.acao_abrir_modal_padronizar)
        btn_padronizar.pack(side="right", padx=(0, 0), pady=15)

        # CORPO (PANEL DUPLO)
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=20, pady=20)

        # ==========================================
        # FORMULÁRIO (ESQUERDA)
        # ==========================================
        frame_form = ctk.CTkFrame(corpo, fg_color=COLOR_WHITE, width=350, corner_radius=8)
        frame_form.pack(side="left", fill="y", padx=(0, 20))
        frame_form.pack_propagate(False)

        ctk.CTkLabel(frame_form, text="Dados do Ponto", font=("Arial Bold", 16), text_color=COLOR_TEXT).pack(pady=(20, 15))

        self.entradas = {}
        campos = [
            ("ID do Ponto *", "id_ponto"),
            ("Endereço *", "endereco"),
            ("Número", "numero"),
            ("Bairro", "bairro"),
            ("Complemento / Referência", "complemento")
        ]
        
        for label_text, key in campos:
            ctk.CTkLabel(frame_form, text=label_text, font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w", padx=20)
            entry = ctk.CTkEntry(frame_form, width=310, height=35)
            entry.pack(padx=20, pady=(0, 10))
            self.entradas[key] = entry

        ctk.CTkLabel(frame_form, text="Status", font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w", padx=20)
        
        self.cb_status = CtkParametrosComboBox(frame_form, values=["ATIVO", "INATIVO"], width=310, height=35)
        self.cb_status.pack(padx=20, pady=(0, 15))

        frame_btns = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_btns.pack(fill="x", padx=20)
        
        ctk.CTkButton(frame_btns, text="LIMPAR", fg_color="transparent", width=100, height=35, text_color=COLOR_PRIMARY, border_width=1, border_color=COLOR_PRIMARY, hover_color="#E9ECEF", command=self.limpar_form).pack(side="left")
        ctk.CTkButton(frame_btns, text="💾 SALVAR", fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, height=35, command=self.acao_salvar).pack(side="right", fill="x", expand=True, padx=(10, 0))

        ctk.CTkButton(frame_form, text="🗑️ EXCLUIR ENDEREÇO", fg_color="transparent", text_color="#D32F2F", border_width=1, border_color="#D32F2F", hover_color="#FEE2E2", height=35, command=self.acao_excluir).pack(fill="x", padx=20, pady=(15, 20))

        # ==========================================
        # TABELA DE PESQUISA (DIREITA)
        # ==========================================
        frame_lista = ctk.CTkFrame(corpo, fg_color=COLOR_WHITE, corner_radius=8)
        frame_lista.pack(side="right", fill="both", expand=True)

        frame_busca = ctk.CTkFrame(frame_lista, fg_color="transparent")
        frame_busca.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(frame_busca, text="🔍 Buscar:", font=("Arial Bold", 13), text_color=COLOR_TEXT).pack(side="left")
        
        # MUDANÇA: O botão sumiu, então o campo de busca agora expande preenchendo o espaço!
        self.entry_busca = ctk.CTkEntry(frame_busca, height=35, placeholder_text="Digite ID, Rua ou Bairro letra por letra...")
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.entry_busca.bind("<KeyRelease>", self.acao_buscar) # Ligado de volta à digitação rápida
        

        # ESTILO RELATÓRIOS (Modern.Treeview)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Modern.Treeview", background=COLOR_WHITE, fieldbackground="#FFFFFF", rowheight=38, font=("Arial", 11), borderwidth=0)
        style.configure("Modern.Treeview.Heading", font=("Arial Bold", 11), background="#E9ECEF", foreground=COLOR_TEXT, borderwidth=0, padding=(0, 5))
        style.map("Modern.Treeview", background=[('selected', COLOR_PRIMARY)], foreground=[('selected', 'white')])
        
        colunas = ("id", "endereco", "numero", "bairro", "status")
        self.tree = ttk.Treeview(frame_lista, columns=colunas, show="headings", style="Modern.Treeview")
        self.tree.tag_configure('impar', background=COLOR_WHITE)
        self.tree.tag_configure('par', background="#F9FAFB")

        self.tree.heading("id", text="ID Ponto")
        self.tree.heading("endereco", text="Endereço")
        self.tree.heading("numero", text="Nº")
        self.tree.heading("bairro", text="Bairro")
        self.tree.heading("status", text="Status")
        
        self.tree.column("id", width=100, anchor="center")
        self.tree.column("endereco", width=350)
        self.tree.column("numero", width=80, anchor="center")
        self.tree.column("bairro", width=150)
        self.tree.column("status", width=100, anchor="center")

        scroll_y = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side="top", fill="both", expand=True, padx=(20, 0), pady=(0, 10))
        scroll_y.pack(side="right", fill="y", padx=(0, 20), pady=(0, 10))

        self.tree.bind("<Double-1>", self._ao_clicar_tabela)

        # PAGINAÇÃO NO RODAPÉ
        self.frame_paginacao = ctk.CTkFrame(frame_lista, fg_color="transparent")
        self.frame_paginacao.pack(side="bottom", fill="x", padx=20, pady=(0, 15))
        
        self.btn_ant = ctk.CTkButton(self.frame_paginacao, text="< Anterior", font=("Arial Bold", 12), width=90, height=35, fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", command=self._pagina_anterior)
        self.btn_ant.pack(side="left", padx=5)
        self.lbl_pag = ctk.CTkLabel(self.frame_paginacao, text="Página 1 | Total: 0 resultados", font=("Arial Bold", 13), text_color=COLOR_PRIMARY)
        self.lbl_pag.pack(side="left", padx=15)
        self.btn_prox = ctk.CTkButton(self.frame_paginacao, text="Próxima >", font=("Arial Bold", 12), width=90, height=35, fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", command=self._pagina_proxima)
        self.btn_prox.pack(side="left", padx=5)

    # ==========================================
    # LÓGICA DE DADOS E PAGINAÇÃO
    # ==========================================
    def acao_buscar(self, event=None):
        if event and getattr(event, 'keysym', '') in ["Up", "Down", "Escape", "Tab", "Left", "Right", "Shift_L", "Shift_R", "Control_L", "Control_R", "Caps_Lock"]: 
            return
            
        self.pagina_atual = 1
        self.termo_busca = self.entry_busca.get().strip()
        self._carregar_tabela()

    def _pagina_anterior(self):
        if self.pagina_atual > 1:
            self.pagina_atual -= 1
            self._carregar_tabela()

    def _pagina_proxima(self):
        if self.pagina_atual < self.total_paginas:
            self.pagina_atual += 1
            self._carregar_tabela()

    def _carregar_tabela(self):
        offset = (self.pagina_atual - 1) * self.itens_por_pagina
        self.dados_atuais = self.service.listar_enderecos_paginados(self.termo_busca, self.itens_por_pagina, offset)
        total = self.service.contar_enderecos(self.termo_busca)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, row in enumerate(self.dados_atuais):
            tag = 'par' if i % 2 == 0 else 'impar'
            self.tree.insert("", "end", values=(row['id_ponto'], row['endereco'], row['numero'], row['bairro'], row['status']), tags=(tag,))

        self.total_paginas = math.ceil(total / self.itens_por_pagina) or 1
        self.lbl_pag.configure(text=f"Página {self.pagina_atual} de {self.total_paginas}  |  Total: {total} resultados")
        
        self.btn_ant.configure(state="normal" if self.pagina_atual > 1 else "disabled")
        self.btn_prox.configure(state="normal" if self.pagina_atual < self.total_paginas else "disabled")

    def _ao_clicar_tabela(self, event):
        item_selecionado = self.tree.focus()
        if not item_selecionado: return
        
        valores = self.tree.item(item_selecionado, "values")
        id_ponto = valores[0]
        
        linha = next((d for d in self.dados_atuais if str(d['id_ponto']) == str(id_ponto)), None)
        if not linha: return
        
        self.limpar_form()
        self.entradas["id_ponto"].insert(0, str(linha['id_ponto']))
        self.entradas["endereco"].insert(0, str(linha['endereco']))
        self.entradas["numero"].insert(0, str(linha['numero']))
        self.entradas["bairro"].insert(0, str(linha['bairro']))
        self.entradas["complemento"].insert(0, str(linha['complemento']) if linha['complemento'] else "")
        self.cb_status.set(str(linha['status']))

    def limpar_form(self):
        for entry in self.entradas.values():
            entry.delete(0, 'end')
        self.cb_status.set("ATIVO")
        self.entradas["id_ponto"].focus()

    def acao_salvar(self):
        dados = {key: entry.get() for key, entry in self.entradas.items()}
        dados['status'] = self.cb_status.get()
        
        sucesso, msg = self.service.salvar_endereco(dados, self.usuario_logado)
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            self.limpar_form()
            self._carregar_tabela()
        else:
            messagebox.showerror("Erro", msg)

    def acao_excluir(self):
        id_ponto = self.entradas["id_ponto"].get().strip()
        if not id_ponto:
            return messagebox.showwarning("Aviso", "Selecione ou digite um ID para excluir.")
        
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir permanentemente o ponto ID {id_ponto}?\n\nEsta ação não pode ser desfeita."):
            sucesso, msg = self.service.excluir_endereco(id_ponto)
            if sucesso:
                messagebox.showinfo("Sucesso", msg)
                self.limpar_form()
                self._carregar_tabela()
            else:
                messagebox.showerror("Erro", msg)

    def acao_exportar(self):
        sucesso, msg = self.service.exportar_excel()
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
        else:
            messagebox.showwarning("Atenção", msg)

    def acao_abrir_modal_padronizar(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Padronização em Massa de Endereços/Bairros")
        modal.geometry("900x650")
        modal.grab_set()

        campo_selecionado = ctk.StringVar(value="Bairro")
        
        top_frame = ctk.CTkFrame(modal, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        ctk.CTkLabel(top_frame, text="O que deseja padronizar?", font=("Arial Bold", 14), text_color=COLOR_TEXT).pack(side="left", padx=(0, 10))
        
        self.seg_campo = ctk.CTkSegmentedButton(top_frame, values=["Bairro", "Endereço"], variable=campo_selecionado, font=("Arial Bold", 12), command=lambda _: reset_e_recarregar())
        self.seg_campo.pack(side="left")

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # --- PAINEL ESQUERDO: Treeview com Paginação ---
        painel_esq = ctk.CTkFrame(container, corner_radius=8, fg_color=COLOR_WHITE)
        painel_esq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        lbl_passo1 = ctk.CTkLabel(painel_esq, text="1. Selecione os itens com erro:", font=("Arial Bold", 14), text_color=COLOR_TEXT)
        lbl_passo1.pack(pady=(15, 5), padx=15, anchor="w")
        
        busca_modal = ctk.CTkEntry(painel_esq, placeholder_text="🔍 Pesquisar letra por letra...", height=35, border_color=COLOR_PRIMARY)
        busca_modal.pack(fill="x", padx=15, pady=(0, 10))
        
        frame_tree = ctk.CTkFrame(painel_esq, fg_color="transparent")
        frame_tree.pack(fill="both", expand=True, padx=15, pady=(0, 5))
        
        colunas_modal = ("check", "valor")
        tree_modal = ttk.Treeview(frame_tree, columns=colunas_modal, show="headings", style="Modern.Treeview")
        tree_modal.heading("check", text="Sel")
        tree_modal.heading("valor", text="Valor Cadastrado (Duplo clique p/ selecionar)")
        tree_modal.column("check", width=40, anchor="center")
        tree_modal.column("valor", width=380, anchor="w")
        
        scroll_modal = ttk.Scrollbar(frame_tree, orient="vertical", command=tree_modal.yview)
        tree_modal.configure(yscrollcommand=scroll_modal.set)
        tree_modal.pack(side="left", fill="both", expand=True)
        scroll_modal.pack(side="right", fill="y")
        
        # Paginação da Modal
        frame_pag = ctk.CTkFrame(painel_esq, fg_color="transparent")
        frame_pag.pack(fill="x", padx=15, pady=(0, 10))
        
        btn_ant = ctk.CTkButton(frame_pag, text="< Ant", width=60, height=30, fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", command=lambda: mudar_pagina(-1))
        btn_ant.pack(side="left")
        lbl_pag = ctk.CTkLabel(frame_pag, text="Pág 1 de 1", font=("Arial Bold", 12), text_color=COLOR_PRIMARY)
        lbl_pag.pack(side="left", expand=True)
        btn_prox = ctk.CTkButton(frame_pag, text="Próx >", width=60, height=30, fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", command=lambda: mudar_pagina(1))
        btn_prox.pack(side="right")
        
        lbl_selecionados = ctk.CTkLabel(painel_esq, text="0 item(ns) selecionado(s)", font=("Arial Bold", 12), text_color="#EF4444")
        lbl_selecionados.pack(pady=(0, 10))

        # --- PAINEL DIREITO: Novo Nome e Ação ---
        painel_dir = ctk.CTkFrame(container, width=320, corner_radius=8, fg_color=COLOR_WHITE)
        painel_dir.pack(side="right", fill="y")
        painel_dir.pack_propagate(False)
        
        lbl_passo2 = ctk.CTkLabel(painel_dir, text="2. Nome final unificado:", font=("Arial Bold", 14), text_color=COLOR_TEXT)
        lbl_passo2.pack(pady=(15, 10), padx=15, anchor="w")
        
        entry_novo = Autocomplete(painel_dir, values=[], width=280, height=40, font=("Arial", 13), border_width=1, border_color=COLOR_PRIMARY, placeholder_text="Digite ou pesquise...")
        entry_novo.pack(padx=15, pady=5)
        
        ctk.CTkLabel(painel_dir, text="Dica: Comece a digitar para ver os\nnomes corretos ou digite um novo.", font=("Arial", 11), text_color="gray").pack(padx=15, anchor="w")
        
        # --- VARIÁVEIS DE ESTADO DA MODAL ---
        pagina_atual = 1
        itens_por_pagina = 50
        total_paginas = 1
        selecionados = set()

        def atualizar_contador():
            qtd = len(selecionados)
            lbl_selecionados.configure(text=f"{qtd} item(ns) selecionado(s)")

        def toggle_item(event):
            item_id = tree_modal.focus()
            if not item_id: return
            valor = tree_modal.item(item_id, "values")[1]
            if valor in selecionados:
                selecionados.remove(valor)
                tree_modal.item(item_id, values=("☐", valor))
            else:
                selecionados.add(valor)
                tree_modal.item(item_id, values=("☑", valor))
            atualizar_contador()

        tree_modal.bind("<Double-1>", toggle_item)
        tree_modal.bind("<space>", toggle_item) # Acessibilidade: Pode marcar com botão Espaço

        def carregar_tabela():
            nonlocal pagina_atual, total_paginas
            termo = busca_modal.get().strip().upper()
            campo = campo_selecionado.get()
            
            offset = (pagina_atual - 1) * itens_por_pagina
            dados = self.service.listar_valores_unicos_paginados(campo, termo, itens_por_pagina, offset)
            total = self.service.contar_valores_unicos(campo, termo)
            
            total_paginas = math.ceil(total / itens_por_pagina) or 1
            
            for i in tree_modal.get_children():
                tree_modal.delete(i)
                
            for i, val in enumerate(dados):
                chk = "☑" if val in selecionados else "☐"
                tag = 'par' if i % 2 == 0 else 'impar'
                tree_modal.insert("", "end", values=(chk, val), tags=(tag,))
                
            lbl_pag.configure(text=f"Pág {pagina_atual} de {total_paginas}")
            btn_ant.configure(state="normal" if pagina_atual > 1 else "disabled")
            btn_prox.configure(state="normal" if pagina_atual < total_paginas else "disabled")

        def reset_e_recarregar():
            nonlocal pagina_atual
            pagina_atual = 1
            selecionados.clear()
            atualizar_contador()
            busca_modal.delete(0, 'end')
            entry_novo.delete(0, 'end')
            
            campo = campo_selecionado.get()
            lbl_passo1.configure(text=f"1. Selecione os {campo.lower()}s com erro:")
            
            # Carrega todas as sugestões para o Autocomplete funcionar com o histórico total
            sugestoes = self.service.obter_valores_unicos(campo)
            entry_novo.atualizar_sugestoes(sugestoes)
            
            carregar_tabela()

        def buscar_letra_por_letra(event):
            nonlocal pagina_atual
            # Ignora teclas de navegação para não reativar o banco sem necessidade
            if event.keysym in ["Up", "Down", "Return", "Escape", "Tab", "Left", "Right"]: return
            pagina_atual = 1
            carregar_tabela()

        busca_modal.bind("<KeyRelease>", buscar_letra_por_letra)

        def mudar_pagina(delta):
            nonlocal pagina_atual
            nova = pagina_atual + delta
            if 1 <= nova <= total_paginas:
                pagina_atual = nova
                carregar_tabela()

        def aplicar_padronizacao():
            campo = campo_selecionado.get()
            novo = entry_novo.get()
            
            if not selecionados: return messagebox.showwarning("Atenção", f"Selecione ao menos um {campo.lower()} na lista à esquerda.")
            if not novo or not novo.strip() or novo == "– Selecione –": return messagebox.showwarning("Atenção", f"Informe o novo nome unificado do {campo.lower()}.")
            
            confirmacao = messagebox.askyesno("Confirmar Padronização", f"Tem a certeza que deseja atualizar TODOS os pontos vinculados aos {len(selecionados)} itens marcados?\n\nNovo {campo.lower()}: '{novo.strip().upper()}'")
            if confirmacao:
                sucesso, msg = self.service.padronizar_valores(campo, list(selecionados), novo)
                if sucesso:
                    messagebox.showinfo("Sucesso", msg)
                    reset_e_recarregar()
                    self.acao_buscar() # Recarrega a tabela principal lá atrás
                else: messagebox.showerror("Erro", msg)

        btn_aplicar = ctk.CTkButton(painel_dir, text="✅ APLICAR E CORRIGIR", font=("Arial Bold", 13), fg_color=COLOR_SECONDARY, hover_color="#1E8449", height=45, command=aplicar_padronizacao)
        btn_aplicar.pack(side="bottom", fill="x", padx=15, pady=20)

        # Dispara a função na abertura da tela
        reset_e_recarregar()

def renderizar(frame_destino, usuario_logado):
    return CadastroEnderecoView(master=frame_destino, usuario_logado=usuario_logado)