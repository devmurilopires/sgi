import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
import re
from src.modulos.quadro_horario.parecer.service import ParecerQuadroHorarioService

class ParecerQuadroHorarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerQuadroHorarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        
        self.linhas_add = []
        self.datas_isoladas_add = []
        self._construir_listas_padrao()
        self._construir_interface()

    def _construir_listas_padrao(self):
        self.lista_solicitantes = ["AGEFIS", "AMC", "Cidadão", "CMF", "Comunidade", "Construtoras", "Empresas Operadoras", "Sindiônibus", "Outros"]
        self.lista_assuntos = ["Aumento de frota para concurso", "Aumento de frota", "Redução de frota", "Execesso de demanda", "Remoção de empresas", "Retorno de Linha", "Mudança de frota", "Intervalo irregular", "Diversos--Requerimentos", "Inclusão de viagens", "Outros"]
        self.lista_eventos = ["Cultural", "Esportivo", "Religioso", "Festival Junino", "Comunitário", "Festas", "Parada da Diversidade Sexual", "Fortal", "Academia Enem", "Caminhada com Maria", "Evangelizar", "Outros"]

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#F8F9FA")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- CABEÇALHO ---
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header_frame, text="Gerador de Parecer Técnico (Quadro de Horário)", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        # =====================================================================
        # FORMULÁRIO PRINCIPAL (Layout Grid Duplo: Base 380px)
        # =====================================================================
        form_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        form_frame.pack(fill="x", pady=10, padx=10)

        grid_master = ctk.CTkFrame(form_frame, fg_color="transparent")
        grid_master.pack(fill="x", pady=15, padx=15)

        # --- LINHA 0: Decisão, Processo e evento---
        self.tipo_var = ctk.StringVar(value="DEFERIDO")
        cb_tipo = self._criar_combo_grid(grid_master, "Decisão do Parecer", 280, ["DEFERIDO", "INDEFERIDO"], 0, 0)
        cb_tipo.configure(variable=self.tipo_var, command=self._on_tipo_change)
        
        self.processo_entry = self._criar_campo_grid(grid_master, "Nº Processo", 280, 0, 1)
        self.processo_entry.bind("<KeyRelease>", lambda e: self.processo_entry.delete(0, "end") or self.processo_entry.insert(0, self.processo_entry.get().upper()))
        
        self.evento_combo = self._criar_autocomplete_grid(grid_master, "Evento (Deixe em branco se for apenas Linha)", 280, self.lista_eventos, 0, 2)
        self.evento_combo.set("")
        self.evento_combo.bind("<KeyRelease>", self._aplicar_regras_negocio, add="+")
        self.evento_combo.configure(command=self._aplicar_regras_negocio)

        # --- LINHA 1: Solicitante e Assunto ---
        self.solicitante_combo = self._criar_autocomplete_grid(grid_master, "Solicitante", 280, self.lista_solicitantes, 1, 0)
        self.assunto_combo = self._criar_autocomplete_grid(grid_master, "Assunto", 280, self.lista_assuntos, 1, 1)

        # --- LINHA 2: Datas (Modo de Seleção + Inputs + Chips) ---
        self.modo_data_var = ctk.StringVar(value="Período (Início-Fim)")
        self.modo_combo = self._criar_combo_grid(grid_master, "Seleção de Datas", 280, ["Período (Início-Fim)", "Dias Isolados"], 2, 0)
        self.modo_combo.configure(variable=self.modo_data_var, command=self._on_modo_data_change)

        self.master_datas_frame = ctk.CTkFrame(grid_master, fg_color="transparent")
        self.master_datas_frame.grid(row=2, column=1, sticky="nw", padx=10, pady=10)
        
        self.container_datas_input = ctk.CTkFrame(self.master_datas_frame, fg_color="transparent")
        self.container_datas_input.pack(fill="x")
        
        self.frame_chips_datas = ctk.CTkFrame(self.master_datas_frame, fg_color="transparent")
        self.frame_chips_datas.pack(fill="x", pady=(5,0))

        # Removido _on_modo_data_change() daqui!

        # --- LINHA 3: Linhas (Input + Botão + Chips) ---
        self.master_linhas_frame = ctk.CTkFrame(grid_master, fg_color="transparent")
        self.master_linhas_frame.grid(row=1, column=2, columnspan=2, sticky="nw", padx=10, pady=10)

        ctk.CTkLabel(self.master_linhas_frame, text="Linha afetada", font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        row_linha = ctk.CTkFrame(self.master_linhas_frame, fg_color="transparent")
        row_linha.pack(fill="x", pady=(2,0))

        self.lista_linhas_banco = self.service.buscar_sugestoes_linhas()
        self.linha_combo = ctk.CTkComboBox(row_linha, width=300, height=35, values=self.lista_linhas_banco, font=("Arial", 12))
        self.linha_combo.set("")
        self.linha_combo.pack(side="left")
        
        def on_key_linha(event):
            val = self.linha_combo.get().lower()
            if not val: self.linha_combo.configure(values=self.lista_linhas_banco)
            else:
                filt = [v for v in self.lista_linhas_banco if val in v.lower()]
                self.linha_combo.configure(values=filt if filt else ["- Sem resultados -"])
        self.linha_combo.bind("<KeyRelease>", on_key_linha)

        self.btn_add_linha = ctk.CTkButton(row_linha, text="➕ Add Linha", width=110, height=35, fg_color="#0F8C75", font=("Arial Bold", 12), command=self._add_linha)
        self.btn_add_linha.pack(side="left", padx=(10,0))

        self.frame_chips_linhas = ctk.CTkFrame(self.master_linhas_frame, fg_color="transparent")
        self.frame_chips_linhas.pack(fill="x", pady=(10,0))

        # =====================================================================
        # GATILHO DE INICIALIZAÇÃO E CONTAINER DINÂMICO
        # (Agora sim, todos os elementos visuais já foram criados na memória)
        # =====================================================================
        self._on_modo_data_change()
        self._aplicar_regras_negocio()

        self.container_dinamico = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.container_dinamico.pack(fill="x", pady=(0, 15), padx=15)
        self._on_tipo_change()

        # --- RODAPÉ ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)
        ctk.CTkLabel(footer_frame, text=f"Responsável pelo Documento: {self.usuario_logado}", font=("Arial Bold", 12), text_color="#777").pack(side="left", padx=10)
        ctk.CTkButton(footer_frame, text="✅ GERAR PARECER TÉCNICO", fg_color="#0F8C75", hover_color="#0B6B59", font=("Arial Black", 16), height=50, width=320, command=self.acao_gerar).pack(side="right", padx=10)

    # --- REGRAS DE NEGÓCIO BLINDADAS (Evento vs Linha) ---
    def _aplicar_regras_negocio(self, *args):
        evento_val = self.evento_combo.get().strip()
        has_linhas = len(self.linhas_add) > 0

        if has_linhas:
            self.evento_combo.set("")
            self.evento_combo.configure(state="disabled")
            self.modo_combo.configure(state="disabled")
            if hasattr(self, 'data_inicio') and self.data_inicio.winfo_exists(): self.data_inicio.configure(state="disabled")
            if hasattr(self, 'data_fim') and self.data_fim.winfo_exists(): self.data_fim.configure(state="disabled")
            if hasattr(self, 'data_isolada') and self.data_isolada.winfo_exists(): self.data_isolada.configure(state="disabled")
            if hasattr(self, 'btn_add_data') and self.btn_add_data.winfo_exists(): self.btn_add_data.configure(state="disabled")
        else:
            self.evento_combo.configure(state="normal")
            self.modo_combo.configure(state="readonly")
            if hasattr(self, 'data_inicio') and self.data_inicio.winfo_exists(): self.data_inicio.configure(state="normal")
            if hasattr(self, 'data_fim') and self.data_fim.winfo_exists(): self.data_fim.configure(state="normal")
            if hasattr(self, 'data_isolada') and self.data_isolada.winfo_exists(): self.data_isolada.configure(state="normal")
            if hasattr(self, 'btn_add_data') and self.btn_add_data.winfo_exists(): self.btn_add_data.configure(state="normal")

            if evento_val != "" and evento_val != "- Sem resultados -":
                self.linha_combo.set("")
                self.linha_combo.configure(state="disabled")
                self.btn_add_linha.configure(state="disabled")
            else:
                self.linha_combo.configure(state="normal")
                self.btn_add_linha.configure(state="normal")

    # --- HELPERS DE GRID UI/UX (CORRIGIDOS COM STICKY 'nw') ---
    def _criar_campo_grid(self, parent, label, width, row, col, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="nw")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(frame, width=width, height=35, font=("Arial", 12))
        entry.pack(anchor="w", pady=(2,0))
        return entry
        
    def _criar_combo_grid(self, parent, label, width, values, row, col, columnspan=1, state="readonly"):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="nw")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, width=width, height=35, values=values, font=("Arial", 12), state=state)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    def _criar_autocomplete_grid(self, parent, label, width, values, row, col, columnspan=1):
        combo = self._criar_combo_grid(parent, label, width, values, row, col, columnspan, state="normal")
        combo._valores_originais = values
        def on_key(event):
            valor_digitado = combo.get().lower()
            if not valor_digitado: combo.configure(values=combo._valores_originais)
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

    # --- MÓDULO DE DATAS ---
    def _on_modo_data_change(self, *args):
        for w in self.container_datas_input.winfo_children(): w.destroy()
        modo = self.modo_data_var.get()

        if "Período" in modo:
            f_ini = ctk.CTkFrame(self.container_datas_input, fg_color="transparent")
            f_ini.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(f_ini, text="Data Inicial:", font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
            wrapper_ini, self.data_inicio = self._criar_date_wrapper(f_ini, 140)
            wrapper_ini.pack(anchor="w", pady=(2,0))

            f_fim = ctk.CTkFrame(self.container_datas_input, fg_color="transparent")
            f_fim.pack(side="left")
            ctk.CTkLabel(f_fim, text="Data Final:", font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
            wrapper_fim, self.data_fim = self._criar_date_wrapper(f_fim, 140)
            wrapper_fim.pack(anchor="w", pady=(2,0))
            
            for w in self.frame_chips_datas.winfo_children(): w.destroy()
        else:
            f_iso = ctk.CTkFrame(self.container_datas_input, fg_color="transparent")
            f_iso.pack(side="left", fill="both", expand=True)
            
            input_row = ctk.CTkFrame(f_iso, fg_color="transparent")
            input_row.pack(side="top", fill="x")

            col1 = ctk.CTkFrame(input_row, fg_color="transparent")
            col1.pack(side="left", padx=(0, 10))
            ctk.CTkLabel(col1, text="Selecionar Dia:", font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
            wrapper_iso, self.data_isolada = self._criar_date_wrapper(col1, 150)
            wrapper_iso.pack(anchor="w", pady=(2,0))

            self.btn_add_data = ctk.CTkButton(input_row, text="➕ Add Data", width=100, height=35, fg_color="#0F8C75", font=("Arial Bold", 12), command=self._add_data_isolada)
            self.btn_add_data.pack(side="left", anchor="s", pady=(0,0))

            self._render_datas_chips()
            
        self._aplicar_regras_negocio() 

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
            if "Isolados" in self.modo_data_var.get():
                ctk.CTkLabel(self.frame_chips_datas, text="Nenhuma data isolada adicionada.", text_color="gray", font=("Arial", 11)).pack(anchor="w", padx=10)
            return
            
        for d in self.datas_isoladas_add:
            chip = ctk.CTkFrame(self.frame_chips_datas, fg_color="#F1F3F5", corner_radius=6, height=32)
            chip.pack(side="top", fill="x", pady=3)
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=d, text_color="#333", font=("Arial Bold", 12)).pack(side="left", padx=10)
            ctk.CTkButton(chip, text="X", width=24, height=24, fg_color="#F24822", hover_color="#B71C1C", font=("Arial Black", 10), command=lambda date=d: self._remove_data_isolada(date)).pack(side="right", padx=5)

    # --- MÓDULO DE LINHAS ---
    def _add_linha(self):
        lin = self.linha_combo.get().strip()
        if lin and lin != "- Sem resultados -" and lin not in self.linhas_add:
            self.linhas_add.append(lin)
            self.linha_combo.set("") 
            self._render_linhas_chips()
            self._aplicar_regras_negocio()

    def _remove_linha(self, lin):
        if lin in self.linhas_add:
            self.linhas_add.remove(lin)
            self._render_linhas_chips()
            self._aplicar_regras_negocio()

    def _render_linhas_chips(self):
        for w in self.frame_chips_linhas.winfo_children(): w.destroy()
        if not self.linhas_add: return
        
        for lin in self.linhas_add:
            chip = ctk.CTkFrame(self.frame_chips_linhas, fg_color="#F1F3F5", corner_radius=6, height=32)
            chip.pack(side="left", padx=5, pady=3) # Chips lado a lado
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=lin, text_color="#333", font=("Arial Bold", 12)).pack(side="left", padx=10)
            ctk.CTkButton(chip, text="X", width=24, height=24, fg_color="#F24822", hover_color="#B71C1C", font=("Arial Black", 10), command=lambda l=lin: self._remove_linha(l)).pack(side="right", padx=5)

    # --- DINAMISMO (DEFERIDO vs INDEFERIDO) ---
    def _on_tipo_change(self, *args):
        for w in self.container_dinamico.winfo_children(): w.destroy()
        tipo = self.tipo_var.get()
        
        if tipo == "INDEFERIDO":
            frame_motivo = ctk.CTkFrame(self.container_dinamico, fg_color="transparent")
            frame_motivo.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(frame_motivo, text="Motivo do Indeferimento:", font=("Arial Bold", 12), text_color="#D32F2F").pack(anchor="w")
            self.motivo_text = ctk.CTkTextbox(frame_motivo, height=80, border_width=2)
            self.motivo_text.pack(fill="x", pady=(2,0))

    # --- AÇÃO PRINCIPAL ---
    def acao_gerar(self):
        tipo = self.tipo_var.get()
        
        # Processa Datas Selecionadas (Apenas se for Evento)
        datas_selecionadas = []
        if not self.linhas_add: 
            if "Período" in self.modo_data_var.get():
                d_ini = self.data_inicio.get()
                d_fim = self.data_fim.get()
                datas_selecionadas = [d_ini] if d_ini == d_fim else [d_ini, d_fim]
            else:
                datas_selecionadas = sorted(self.datas_isoladas_add.copy())
            
        dados_form = {
            "processo": self.processo_entry.get().strip(),
            "solicitante": self.solicitante_combo.get().strip(),
            "assunto": self.assunto_combo.get().strip(),
            "evento": self.evento_combo.get().strip(),
            "datas": datas_selecionadas,
            "modo_data": "PERIODO" if "Período" in self.modo_data_var.get() else "ISOLADOS",
            "motivo": self.motivo_text.get("1.0", "end").strip() if tipo == "INDEFERIDO" else ""
        }

        if not all([dados_form["processo"], dados_form["solicitante"], dados_form["assunto"]]):
            messagebox.showerror("Erro", "Preencha Processo, Solicitante e Assunto.")
            return

        if not self.linhas_add and not dados_form["evento"]:
            messagebox.showerror("Erro", "Informe um Evento ou adicione ao menos uma Linha afetada.")
            return

        if dados_form["evento"] and not datas_selecionadas:
            messagebox.showwarning("Aviso", "Como você informou um Evento, adicione ao menos uma Data (Período ou Isolada).")
            return

        if tipo == "INDEFERIDO" and len(dados_form["motivo"]) < 5:
            messagebox.showerror("Erro", "Forneça um motivo claro para o indeferimento.")
            return

        sucesso, msg = self.service.processar_parecer(tipo, dados_form, self.linhas_add, self.usuario_logado)

        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            self.processo_entry.delete(0, "end")
            self.linhas_add.clear(); self._render_linhas_chips()
            self.datas_isoladas_add.clear(); self._render_datas_chips()
            self.evento_combo.set(""); self._aplicar_regras_negocio()
            self._on_tipo_change()
            self._on_modo_data_change()
        else:
            messagebox.showerror("Erro", msg)

def renderizar(frame_destino, usuario_logado):
    return ParecerQuadroHorarioView(master=frame_destino, usuario_logado=usuario_logado)