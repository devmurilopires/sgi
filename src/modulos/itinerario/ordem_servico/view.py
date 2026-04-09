import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
import re
from src.modulos.itinerario.ordem_servico.service import OSItinerarioService

class OSItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = OSItinerarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        
        self.empresas_add = []
        self.linhas_add = []
        self.anexos_add = []
        self.datas_isoladas_add = [] 

        self._construir_interface()

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#F8F9FA")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- CABEÇALHO ---
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header_frame, text="Gerador de Ordem de Serviço (Itinerário)", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        # =====================================================================
        # FORMULÁRIO PRINCIPAL (Grelha Matemática: Base 250px)
        # =====================================================================
        form_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        form_frame.pack(fill="x", pady=10, padx=10)

        linha_fixa = ctk.CTkFrame(form_frame, fg_color="transparent")
        linha_fixa.pack(fill="x", pady=(15, 0), padx=15)

        self.tipo_os_var = ctk.StringVar(value="EVENTOS")
        # Coluna 0
        cb_tipo = self._criar_combo_grid(linha_fixa, "Tipo de OS", 250, ["EVENTOS", "CORRIDA", "OBRAS"], 0, 0)
        cb_tipo.configure(variable=self.tipo_os_var, command=self._on_tipo_change)
        
        # Coluna 1
        self.processo_entry = self._criar_campo_grid(linha_fixa, "Nº Processo (Opcional)", 250, 0, 1)
        self.processo_entry.bind("<KeyRelease>", lambda e: self.processo_entry.delete(0, "end") or self.processo_entry.insert(0, self.processo_entry.get().upper()))

        # Coluna 2 (NOVO CAMPO ORIGEM AO LADO DO PROCESSO)
        self.origem_combo = self._criar_combo_grid(linha_fixa, "Origem", 250, ["SISGEP", "SPU"], 0, 2)

        # Container Dinâmico onde as Datas e Empresas ficarão alinhadas
        self.container_dinamico = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.container_dinamico.pack(fill="x", pady=0, padx=15)

        # --- Container de Listas (Dedicado EXCLUSIVAMENTE às Linhas) ---
        self.container_listas = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.container_listas.pack(fill="x", pady=(0, 15), padx=15)

        self.frame_linhas_master = ctk.CTkFrame(self.container_listas, fg_color="transparent")
        self.frame_linhas_master.pack(fill="x", anchor="w")
        
        add_lin_row = ctk.CTkFrame(self.frame_linhas_master, fg_color="transparent")
        add_lin_row.pack(fill="x")
        
        self.lista_linhas = self.service.buscar_sugestoes("LINHAS")
        # Alinhado com as colunas superiores: 250px
        self.linha_combo = self._criar_autocomplete_grid(add_lin_row, "Pesquise a Linha de Ônibus", 250, self.lista_linhas, 0, 0)
        ctk.CTkButton(add_lin_row, text="➕ Add", width=80, height=35, font=("Arial Bold", 12), fg_color="#0F8C75", command=self._add_linha).grid(row=0, column=1, sticky="s", pady=(0,10), padx=10)
        
        self.frame_chips_linhas = ctk.CTkFrame(self.frame_linhas_master, fg_color="transparent")
        self.frame_chips_linhas.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self._on_tipo_change() 

        # =====================================================================
        # SESSÃO DE ANEXOS E CROQUIS
        # =====================================================================
        anexos_container = ctk.CTkFrame(self.scroll_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        anexos_container.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(anexos_container, text="Anexos, Imagens e Croquis", font=("Arial Bold", 16), text_color="#333333").pack(anchor="w", padx=15, pady=(15,5))
        
        botoes_anexos = ctk.CTkFrame(anexos_container, fg_color="transparent")
        botoes_anexos.pack(fill="x", padx=15)
        ctk.CTkButton(botoes_anexos, text="📄 Selecionar Imagem/Anexo", fg_color="#0F8C75", font=("Arial Bold", 12), height=35, command=self._add_anexo).pack(side="left", padx=(0,10))
        ctk.CTkButton(botoes_anexos, text="📝 Add Bloco de Texto (Sem Imagem)", fg_color="gray", font=("Arial Bold", 12), height=35, command=lambda: self._add_anexo(vazio=True)).pack(side="left")
        
        self.lista_anexos_frame = ctk.CTkFrame(anexos_container, fg_color="transparent")
        self.lista_anexos_frame.pack(fill="x", padx=15, pady=10)

        # --- RODAPÉ ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)
        ctk.CTkLabel(footer_frame, text=f"Responsável pelo Documento: {self.usuario_logado}", font=("Arial Bold", 12), text_color="#777").pack(side="left", padx=10)
        ctk.CTkButton(footer_frame, text="✅ GERAR ORDEM DE SERVIÇO", fg_color="#0F8C75", hover_color="#0B6B59", font=("Arial Black", 16), height=50, width=320, command=self.acao_criar_os).pack(side="right", padx=10)

    # --- HELPERS DE GRID UI/UX ---
    def _criar_campo_grid(self, parent, label, width, row, col, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(frame, width=width, height=35, font=("Arial", 12))
        entry.pack(anchor="w", pady=(2,0))
        return entry
        
    def _criar_combo_grid(self, parent, label, width, values, row, col, columnspan=1, state="readonly"):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, width=width, height=35, values=values, font=("Arial", 12), state=state)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    def _criar_autocomplete_grid(self, parent, label, width, values, row, col, columnspan=1):
        combo = self._criar_combo_grid(parent, label, width, values, row, col, columnspan, state="normal")
        combo._valores_originais = values
        
        def on_key(event):
            valor_digitado = combo.get().lower()
            if not valor_digitado:
                combo.configure(values=combo._valores_originais)
            else:
                filtrados = [v for v in combo._valores_originais if valor_digitado in v.lower()]
                combo.configure(values=filtrados if filtrados else ["- Sem resultados -"])
                
        combo.bind("<KeyRelease>", on_key)
        return combo

    def _criar_date_wrapper(self, parent, width):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 12), background="#0F8C75", foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    # --- DINÂMICA DE CAMPOS ---
    def _on_tipo_change(self, *args):
        for w in self.container_dinamico.winfo_children(): w.destroy()
        tipo = self.tipo_os_var.get()
        self.campos_dinamicos = {}

        if tipo == "EVENTOS":
            self.campos_dinamicos['evento'] = self._criar_combo_grid(self.container_dinamico, "Nome do Evento", 250, ["Obras", "Corrida", "Pré Carnaval", "Outros"], 0, 0)
            self.campos_dinamicos['endereco'] = self._criar_campo_grid(self.container_dinamico, "Endereço/Logradouro", 520, 0, 1, columnspan=2)
            self.container_listas.pack(fill="x", pady=(0, 15), padx=15)
        elif tipo == "CORRIDA":
            self.campos_dinamicos['nome_corrida'] = self._criar_campo_grid(self.container_dinamico, "Nome da Corrida", 250, 0, 0)
            self.campos_dinamicos['km'] = self._criar_campo_grid(self.container_dinamico, "Quilometragem (KM)", 250, 0, 1)
            self.campos_dinamicos['solicitante'] = self._criar_campo_grid(self.container_dinamico, "Solicitante", 250, 0, 2)
            self.container_listas.pack_forget() 
        elif tipo == "OBRAS":
            self.campos_dinamicos['tipo_obra'] = self._criar_campo_grid(self.container_dinamico, "Tipo de Obra", 250, 0, 0)
            self.campos_dinamicos['endereco'] = self._criar_campo_grid(self.container_dinamico, "Endereço/Logradouro", 520, 0, 1, columnspan=2)
            self.container_listas.pack(fill="x", pady=(0, 15), padx=15)

        HORARIOS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]

        self.modo_data_var = ctk.StringVar(value="Período (Início-Fim)")
        modo_combo = self._criar_combo_grid(self.container_dinamico, "Seleção de Datas", 250, ["Período (Início-Fim)", "Dias Isolados"], 1, 0)
        modo_combo.configure(variable=self.modo_data_var, command=self._on_modo_data_change)

        self.campos_dinamicos['hr_inicio'] = self._criar_combo_grid(self.container_dinamico, "Hora Início", 250, HORARIOS, 1, 1)
        self.campos_dinamicos['hr_fim'] = self._criar_combo_grid(self.container_dinamico, "Hora Fim", 250, HORARIOS, 1, 2)

        self.container_datas = ctk.CTkFrame(self.container_dinamico, fg_color="transparent")
        self.container_datas.grid(row=2, column=0, columnspan=2, sticky="nw", padx=0, pady=0)
        self._on_modo_data_change()

        self.frame_empresas = ctk.CTkFrame(self.container_dinamico, fg_color="transparent")
        self.frame_empresas.grid(row=2, column=2, sticky="nw", padx=0, pady=0)
        
        add_emp_row = ctk.CTkFrame(self.frame_empresas, fg_color="transparent")
        add_emp_row.pack(fill="x")
        
        self.lista_empresas = self.service.buscar_sugestoes("EMPRESAS")
        self.empresa_combo = self._criar_autocomplete_grid(add_emp_row, "Pesquise a Empresa", 190, self.lista_empresas, 0, 0)
        
        ctk.CTkButton(add_emp_row, text="➕ Add", width=50, height=35, font=("Arial Bold", 12), fg_color="#0F8C75", command=self._add_empresa).grid(row=0, column=1, sticky="s", pady=(0, 10), padx=(0, 10))
        
        self.frame_chips_empresas = ctk.CTkFrame(self.frame_empresas, fg_color="transparent")
        self.frame_chips_empresas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._render_empresas_chips()

    # --- MÓDULO DE DATAS ---
    def _on_modo_data_change(self, *args):
        for w in self.container_datas.winfo_children(): w.destroy()
        modo = self.modo_data_var.get()

        if "Período" in modo:
            f_ini = ctk.CTkFrame(self.container_datas, fg_color="transparent")
            f_ini.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(f_ini, text="Data Inicial:", font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
            wrapper_ini, self.data_inicio = self._criar_date_wrapper(f_ini, 250)
            wrapper_ini.pack(anchor="w", pady=(2,0))

            f_fim = ctk.CTkFrame(self.container_datas, fg_color="transparent")
            f_fim.grid(row=0, column=1, padx=10, pady=10, sticky="w")
            ctk.CTkLabel(f_fim, text="Data Final:", font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
            wrapper_fim, self.data_fim = self._criar_date_wrapper(f_fim, 250)
            wrapper_fim.pack(anchor="w", pady=(2,0))

        else:
            f_iso = ctk.CTkFrame(self.container_datas, fg_color="transparent")
            f_iso.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
            
            input_row = ctk.CTkFrame(f_iso, fg_color="transparent")
            input_row.pack(side="top", fill="x")

            col1 = ctk.CTkFrame(input_row, fg_color="transparent")
            col1.pack(side="left", padx=(0, 15))
            ctk.CTkLabel(col1, text="Selecionar Dia:", font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
            wrapper_iso, self.data_isolada = self._criar_date_wrapper(col1, 250)
            wrapper_iso.pack(anchor="w", pady=(2,0))

            btn_add = ctk.CTkButton(input_row, text="➕ Add Data", width=80, height=35, fg_color="#0F8C75", font=("Arial Bold", 12), command=self._add_data_isolada)
            btn_add.pack(side="left", anchor="s", pady=(0,2))

            self.frame_chips_datas = ctk.CTkFrame(f_iso, fg_color="transparent")
            self.frame_chips_datas.pack(side="top", fill="both", expand=True, pady=(15,0))
            self._render_datas_chips()

    def _add_data_isolada(self):
        d = self.data_isolada.get()
        if d and d not in self.datas_isoladas_add:
            self.datas_isoladas_add.append(d)
            self._render_datas_chips()

    def _remove_data_isolada(self, dt):
        if dt in self.datas_isoladas_add:
            self.datas_isoladas_add.remove(dt)
            self._render_datas_chips()

    def _render_datas_chips(self):
        for w in self.frame_chips_datas.winfo_children(): w.destroy()
        if not self.datas_isoladas_add:
            ctk.CTkLabel(self.frame_chips_datas, text="Nenhuma data adicionada.", text_color="gray", font=("Arial", 11)).pack(anchor="w", padx=10)
            return
            
        for d in self.datas_isoladas_add:
            chip = ctk.CTkFrame(self.frame_chips_datas, fg_color="#F1F3F5", corner_radius=6, height=32)
            chip.pack(side="top", fill="x", pady=3)
            chip.pack_propagate(False)

            ctk.CTkLabel(chip, text=d, text_color="#333", font=("Arial Bold", 12)).pack(side="left", padx=10)
            ctk.CTkButton(chip, text="X", width=24, height=24, fg_color="#F24822", hover_color="#B71C1C", font=("Arial Black", 10), command=lambda date=d: self._remove_data_isolada(date)).pack(side="right", padx=5)

    # --- SISTEMA DE CHIPS (EMPRESAS E LINHAS) ---
    def _add_empresa(self):
        emp = self.empresa_combo.get().strip()
        if emp and emp != "- Sem resultados -" and emp not in self.empresas_add:
            self.empresas_add.append(emp)
            self._render_empresas_chips()
            
    def _remove_empresa(self, emp):
        self.empresas_add.remove(emp)
        self._render_empresas_chips()

    def _render_empresas_chips(self):
        for w in self.frame_chips_empresas.winfo_children(): w.destroy()
        if not self.empresas_add:
            ctk.CTkLabel(self.frame_chips_empresas, text="Nenhuma empresa.", text_color="gray", font=("Arial", 11)).pack(anchor="w", padx=10)
            return
        for emp in self.empresas_add:
            chip = ctk.CTkFrame(self.frame_chips_empresas, fg_color="#F1F3F5", corner_radius=6, height=32)
            chip.pack(side="top", fill="x", pady=3)
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=emp, text_color="#333", font=("Arial Bold", 12)).pack(side="left", padx=10)
            ctk.CTkButton(chip, text="X", width=24, height=24, fg_color="#F24822", hover_color="#B71C1C", font=("Arial Black", 10), command=lambda e=emp: self._remove_empresa(e)).pack(side="right", padx=5)

    def _add_linha(self):
        lin = self.linha_combo.get().strip()
        if lin and lin != "- Sem resultados -" and lin not in self.linhas_add:
            self.linhas_add.append(lin)
            self._render_linhas_chips()

    def _remove_linha(self, lin):
        self.linhas_add.remove(lin)
        self._render_linhas_chips()

    def _render_linhas_chips(self):
        for w in self.frame_chips_linhas.winfo_children(): w.destroy()
        if not self.linhas_add:
            ctk.CTkLabel(self.frame_chips_linhas, text="Nenhuma linha.", text_color="gray", font=("Arial", 11)).pack(anchor="w", padx=10)
            return
        for lin in self.linhas_add:
            chip = ctk.CTkFrame(self.frame_chips_linhas, fg_color="#F1F3F5", corner_radius=6, height=32)
            chip.pack(side="top", fill="x", pady=3)
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=lin, text_color="#333", font=("Arial Bold", 12)).pack(side="left", padx=10)
            ctk.CTkButton(chip, text="X", width=24, height=24, fg_color="#F24822", hover_color="#B71C1C", font=("Arial Black", 10), command=lambda l=lin: self._remove_linha(l)).pack(side="right", padx=5)

    # --- GESTÃO DE ANEXOS (CARTÕES COM GRID) ---
    def _add_anexo(self, vazio=False):
        caminho = ""
        if not vazio:
            caminho = filedialog.askopenfilename(title="Selecione a Imagem", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
            if not caminho: return

        ref_obj = {"caminho": caminho, "widgets": {}}

        card = ctk.CTkFrame(self.lista_anexos_frame, fg_color="#F8F9FA", corner_radius=8, border_width=1, border_color="#DDDDDD")
        card.pack(fill="x", pady=10)

        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=15, pady=10)
        
        titulo = caminho.split("/")[-1] if caminho else "Bloco de Texto/Legenda (Sem Imagem)"
        ctk.CTkLabel(header_row, text=f"📎 {titulo}", font=("Arial Bold", 14), text_color="#0F8C75").pack(side="left")
        ctk.CTkButton(header_row, text="🗑️ Remover Anexo", font=("Arial Bold", 12), fg_color="#D32F2F", hover_color="#B71C1C", height=32, width=140, command=lambda c=card, r=ref_obj: self._remover_anexo(c, r)).pack(side="right")

        grid_row = ctk.CTkFrame(card, fg_color="transparent")
        grid_row.pack(fill="x", padx=5, pady=(0, 15))
        
        campos = {}
        campos['ida'] = self._criar_campo_grid(grid_row, "Linhas Específicas Ida (Ex: 015,021)", 250, 0, 0)
        campos['r_ida'] = self._criar_campo_grid(grid_row, "Descrição Ruas - Ida", 520, 0, 1)
        campos['volta'] = self._criar_campo_grid(grid_row, "Linhas Específicas Volta (Ex: 015,021)", 250, 1, 0)
        campos['r_volta'] = self._criar_campo_grid(grid_row, "Descrição Ruas - Volta", 520, 1, 1)

        ref_obj["widgets"] = campos
        self.anexos_add.append(ref_obj)

    def _remover_anexo(self, frame_card, ref_obj):
        frame_card.destroy()
        if ref_obj in self.anexos_add:
            self.anexos_add.remove(ref_obj)

    # --- PROCESSAMENTO PRINCIPAL ---
    def acao_criar_os(self):
        form_dados = {}
        for k, v in self.campos_dinamicos.items():
            if hasattr(v, 'get'): form_dados[k] = v.get().strip()

        form_dados['processo'] = self.processo_entry.get().strip()
        form_dados['origem'] = self.origem_combo.get().strip() # <-- NOVO CAMPO RECOLHIDO
        
        # Processamento das Datas
        modo_data = self.modo_data_var.get()
        if "Período" in modo_data:
            d_ini = self.data_inicio.get()
            d_fim = self.data_fim.get()
            form_dados['datas'] = [d_ini] if d_ini == d_fim else [d_ini, d_fim]
            form_dados['modo_data'] = "PERIODO"
        else:
            if not self.datas_isoladas_add:
                messagebox.showwarning("Aviso", "Por favor, adicione pelo menos uma data isolada.")
                return
            form_dados['datas'] = sorted(self.datas_isoladas_add.copy())
            form_dados['modo_data'] = "ISOLADOS"

        anexos_formatados = []
        for an in self.anexos_add:
            w = an["widgets"]
            anexos_formatados.append({
                "image_path": an["caminho"],
                "linhas_ida": [i.strip() for i in w['ida'].get().split(',') if i.strip()],
                "linhas_volta": [v.strip() for v in w['volta'].get().split(',') if v.strip()],
                "ruas_ida": w['r_ida'].get().strip(),
                "ruas_volta": w['r_volta'].get().strip()
            })

        sucesso, msg = self.service.processar_criacao_os(
            tipo_os=self.tipo_os_var.get(),
            form_dados=form_dados,
            empresas=self.empresas_add,
            linhas=self.linhas_add,
            anexos_raw=anexos_formatados,
            usuario=self.usuario_logado
        )

        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            self._on_tipo_change() 
            self.processo_entry.delete(0, "end")
            self.datas_isoladas_add.clear()
            self.empresas_add.clear()
            self._render_empresas_chips()
            self.linhas_add.clear()
            self._render_linhas_chips()
            for w in self.lista_anexos_frame.winfo_children(): w.destroy()
            self.anexos_add.clear()
        else:
            messagebox.showerror("Erro ao Gerar OS", msg)

def renderizar(frame_destino, usuario_logado):
    return OSItinerarioView(master=frame_destino, usuario_logado=usuario_logado)