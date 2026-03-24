import customtkinter as ctk
from tkinter import ttk, messagebox
from src.enderecos.service import EnderecoService

COLOR_BG = "#F4F6F9"
COLOR_WHITE = "#FFFFFF"
COLOR_PRIMARY = "#0F8C75"

class CadastroEnderecoView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)
        
        self.usuario_logado = usuario_logado
        self.service = EnderecoService()
        self.df_atual = None

        self._construir_interface()
        self._carregar_tabela()

    def _construir_interface(self):
        # TOPO
        header = ctk.CTkFrame(self, fg_color=COLOR_WHITE, height=60, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Gestão de Ponto de Parada (Endereços)", font=("Arial Black", 20), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=15)

        btn_exportar = ctk.CTkButton(header, text="📥 EXPORTAR EXCEL", font=("Arial Bold", 12), fg_color="#27AE60", hover_color="#1E8449", command=self.acao_exportar)
        btn_exportar.pack(side="right", padx=20, pady=15)

        # CORPO (PANEL DUPLO)
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=20, pady=20)

        # Formulário
        frame_form = ctk.CTkFrame(corpo, fg_color=COLOR_WHITE, width=350, corner_radius=8)
        frame_form.pack(side="left", fill="y", padx=(0, 20))
        frame_form.pack_propagate(False)

        ctk.CTkLabel(frame_form, text="Dados do Ponto", font=("Arial Bold", 16), text_color="#333").pack(pady=(20, 15))

        self.entradas = {}
        campos = [
            ("ID do Ponto *", "id_ponto"),
            ("Endereço *", "endereco"),
            ("Número", "numero"),
            ("Bairro", "bairro"),
            ("Complemento / Referência", "complemento")
        ]
        # Gerar os campos dinamicamente a partir da lista acima, armazenando as referências em um dicionário para fácil acesso depois
        for label_text, key in campos:
            ctk.CTkLabel(frame_form, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w", padx=20)
            entry = ctk.CTkEntry(frame_form, width=310, height=35)
            entry.pack(padx=20, pady=(0, 10))
            self.entradas[key] = entry

        ctk.CTkLabel(frame_form, text="Status", font=("Arial Bold", 12), text_color="#555").pack(anchor="w", padx=20)
        self.cb_status = ctk.CTkComboBox(frame_form, values=["ATIVO", "INATIVO", "EM MANUTENÇÃO"], width=310, height=35)
        self.cb_status.pack(padx=20, pady=(0, 25))

        # Botões do Form
        frame_btns = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_btns.pack(fill="x", padx=20)
        
        ctk.CTkButton(frame_btns, text="LIMPAR", fg_color="#95A5A6", hover_color="#7F8C8D", width=100, height=35, command=self.limpar_form).pack(side="left")
        ctk.CTkButton(frame_btns, text="💾 SALVAR", fg_color=COLOR_PRIMARY, hover_color="#0B6B59", height=35, command=self.acao_salvar).pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Tabela de Pesquisa
        frame_lista = ctk.CTkFrame(corpo, fg_color=COLOR_WHITE, corner_radius=8)
        frame_lista.pack(side="right", fill="both", expand=True)

        frame_busca = ctk.CTkFrame(frame_lista, fg_color="transparent")
        frame_busca.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(frame_busca, text="🔍 Buscar:", font=("Arial Bold", 13), text_color="#333").pack(side="left")
        self.entry_busca = ctk.CTkEntry(frame_busca, width=300, height=35, placeholder_text="Digite ID, Rua ou Bairro...")
        self.entry_busca.pack(side="left", padx=10)
        self.entry_busca.bind("<KeyRelease>", self._filtrar_tabela) # Filtra ao digitar

        # Estilo da Tabela
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview.Heading", font=("Arial Bold", 11), background="#E0E4E8", foreground="#333")
        style.configure("Treeview", font=("Arial", 11), rowheight=30)
        
        colunas = ("id", "endereco", "numero", "bairro", "status")
        self.tree = ttk.Treeview(frame_lista, columns=colunas, show="headings")
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
        self.tree.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 20))
        scroll_y.pack(side="right", fill="y", padx=(0, 20), pady=(0, 20))

        # Evento de clique na tabela
        self.tree.bind("<Double-1>", self._ao_clicar_tabela)

    def _carregar_tabela(self):
        self.df_atual = self.service.listar_enderecos()
        self._preencher_treeview(self.df_atual)

    def _preencher_treeview(self, df):
        # Limpa a tabela antes de preencher com os novos dados
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if df is None or df.empty: return

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(row['id_ponto'], row['endereco'], row['numero'], row['bairro'], row['status']))

    def _filtrar_tabela(self, event=None):
        termo = self.entry_busca.get().upper()
        if self.df_atual is None or self.df_atual.empty: return
        
        # Filtra o dataframe Pandas procurando o termo no ID, Endereço ou Bairro
        df_filtrado = self.df_atual[
            self.df_atual['id_ponto'].astype(str).str.contains(termo, na=False) |
            self.df_atual['endereco'].astype(str).str.contains(termo, na=False) |
            self.df_atual['bairro'].astype(str).str.contains(termo, na=False)
        ]
        self._preencher_treeview(df_filtrado)

    def _ao_clicar_tabela(self, event):
        item_selecionado = self.tree.focus()
        if not item_selecionado: return
        
        valores = self.tree.item(item_selecionado, "values")
        id_ponto = valores[0]
        
        # Busca os dados completos no dataframe carregado
        linha = self.df_atual[self.df_atual['id_ponto'] == id_ponto].iloc[0]
        
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
            self.entry_busca.delete(0, 'end')
        else:
            messagebox.showerror("Erro", msg)

    def acao_exportar(self):
        sucesso, msg = self.service.exportar_excel()
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
        else:
            messagebox.showwarning("Atenção", msg)

def renderizar(frame_destino, usuario_logado):
    return CadastroEnderecoView(master=frame_destino, usuario_logado=usuario_logado)