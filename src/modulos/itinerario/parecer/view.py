import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import re
from src.modulos.itinerario.parecer.service import ParecerItinerarioService

MODERN_STYLE = {
    "fg_color": "#FFFFFF",
    "text_color": "#333333",
    "border_color": "#CCCCCC",
    "button_color": "#E0E0E0",
    "button_hover_color": "#CCCCCC",
    "dropdown_fg_color": "#FFFFFF",
    "dropdown_text_color": "#333333",
    "dropdown_hover_color": "#0F8C75"
}

class ModernAutocomplete(ctk.CTkFrame):
    def __init__(self, master, values, width=250, **kwargs):
        super().__init__(master, fg_color="transparent", width=width, height=35, **kwargs)
        self.pack_propagate(False)
        self.values = values
        
        self.entry = ctk.CTkEntry(self, width=width, height=35, fg_color="#FFFFFF", text_color="#333333", border_color="#CCCCCC")
        self.entry.pack(fill="both", expand=True)
        self.entry.insert(0, "") 

        self.listbox_frame = None

        self.entry.bind("<KeyRelease>", self._on_keyrelease)
        self.entry.bind("<FocusOut>", self._on_focusout)
        self.entry.bind("<FocusIn>", self._on_keyrelease) 
        self.entry.bind("<Button-1>", self._on_keyrelease) 

    def _on_keyrelease(self, event):
        if event and getattr(event, 'keysym', '') in ['Up', 'Down', 'Return', 'Escape', 'Tab']:
            return
        
        val = self.entry.get().lower()
        hits = [item for item in self.values if val in item.lower()] if val else self.values
        self._show_listbox(hits)

    def _show_listbox(self, hits):
        self._hide_listbox()
        if not hits: return

        toplevel = self.winfo_toplevel()
        x = self.entry.winfo_rootx() - toplevel.winfo_rootx()
        y = self.entry.winfo_rooty() - toplevel.winfo_rooty() + self.entry.winfo_height()

        w = self.entry.winfo_width()
        h = min(150, len(hits)*25 + 5)

        self.listbox_frame = ctk.CTkFrame(toplevel, width=w, height=h, fg_color="#FFFFFF", border_width=1, border_color="#0F8C75", corner_radius=4)
        self.listbox_frame.pack_propagate(False) 
        self.listbox_frame.place(x=x, y=y) 

        self.listbox = tk.Listbox(self.listbox_frame, bg="#FFFFFF", fg="#333333", selectbackground="#0F8C75", selectforeground="#FFFFFF", bd=0, highlightthickness=0, font=("Arial", 11))
        self.listbox.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        for hit in hits:
            self.listbox.insert("end", hit)

        self.listbox.bind("<<ListboxSelect>>", self._on_select)

    def _on_select(self, event):
        if not self.listbox: return
        selection = self.listbox.curselection()
        if selection:
            item = self.listbox.get(selection[0])
            self.entry.delete(0, "end")
            self.entry.insert(0, item)
            self.entry.event_generate("<KeyRelease>")
        self._hide_listbox()

    def _hide_listbox(self):
        if hasattr(self, 'listbox_frame') and self.listbox_frame:
            self.listbox_frame.destroy()
            self.listbox_frame = None

    def _on_focusout(self, event):
        self.after(150, self._hide_listbox)

    def get(self):
        return self.entry.get()

    def set(self, value):
        self.entry.delete(0, "end")
        if value: self.entry.insert(0, value)

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.entry.configure(state=kwargs["state"])
        if "values" in kwargs:
            self.values = kwargs["values"]

    def bind(self, sequence, func, add="+"):
        self.entry.bind(sequence, func, add=add)

class ParecerItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerItinerarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        
        self.linhas_add = []
        self.datas_isoladas_add = []
        self._construir_listas_padrao()
        self._construir_interface()

    def _construir_listas_padrao(self):
        self.lista_solicitantes = [
            "AGEFIS", "AMC", "Ceará Sporting Club", "Cidadão", "CMF", "Comunidade", "Construtoras", 
            "Fortaleza Esporte Clube", "GMF", "Ministério Público", "Ouvidoria Etufor", "Ouvidoria Geral", 
            "Polícia Militar do Ceará", "SER 1", "SER 2", "SER 3", "SER 4", "SER 5", "SER 6", "Sindiônibus", "Outros"
        ]
        self.lista_assuntos = ["Alteração de itinerário", "Desvio temporário de itinerário para Obra" , "Desvio temporário de itinerário para Evento", "Desvio temporário de itinerário para Corrida", "Implantação de linha", "Outros"]
        self.lista_eventos = ["07 de Setembro", "Carnaval Domingos Olimpio", "Pré Carnaval", "Obras", "Corrida", "Esportivo", "Religioso", "Outros"]

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#F8F9FA")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header_frame, text="Gerador de Parecer Técnico (Itinerário)", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        form_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        form_frame.pack(fill="x", pady=10, padx=10)

        grid_master = ctk.CTkFrame(form_frame, fg_color="transparent")
        grid_master.pack(fill="x", pady=15, padx=15)

        # --- LINHA 0 ---
        self.tipo_var = ctk.StringVar(value="DEFERIDO")
        cb_tipo = self._criar_combo_grid(grid_master, "Decisão do Parecer", 250, ["DEFERIDO", "INDEFERIDO"], 0, 0)
        cb_tipo.configure(variable=self.tipo_var, command=self._on_tipo_change)
        
        self.processo_entry = self._criar_campo_grid(grid_master, "Nº Processo", 250, 0, 1)

        # --- CORREÇÃO DO BUG AQUI (Lê, Converte, Mantém Posição do Cursor) ---
        def upper_processo_par(event):
            if getattr(event, 'keysym', '') in ['Up', 'Down', 'Left', 'Right', 'Home', 'End']: return
            texto = self.processo_entry.get()
            if texto != texto.upper():
                pos = self.processo_entry.index("insert")
                self.processo_entry.delete(0, "end")
                self.processo_entry.insert(0, texto.upper())
                self.processo_entry.icursor(pos)
                
        self.processo_entry.bind("<KeyRelease>", upper_processo_par)
        # ---------------------------------------------------------------------

        self.solicitante_combo = self._criar_autocomplete_grid(grid_master, "Solicitante", 250, self.lista_solicitantes, 0, 2)

        # --- LINHA 1 ---
        self.assunto_combo = self._criar_autocomplete_grid(grid_master, "Assunto", 250, self.lista_assuntos, 1, 0)
        self.endereco_entry = self._criar_campo_grid(grid_master, "Endereço / Logradouro", 520, 1, 1, columnspan=2)

        # --- LINHA 2 ---
        self.evento_combo = self._criar_autocomplete_grid(grid_master, "Evento", 250, self.lista_eventos, 2, 0)
        
        cb_evento_frame = ctk.CTkFrame(grid_master, fg_color="transparent")
        cb_evento_frame.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        self.no_evento_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cb_evento_frame, text="Sem Evento", variable=self.no_evento_var, command=self._toggle_evento, font=("Arial Bold", 12)).pack(pady=(24,0))

        cb_data_hora_frame = ctk.CTkFrame(grid_master, fg_color="transparent")
        cb_data_hora_frame.grid(row=2, column=2, sticky="w", padx=10, pady=10)
        
        self.no_data_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cb_data_hora_frame, text="Sem Data", variable=self.no_data_var, command=self._toggle_data, font=("Arial Bold", 12)).pack(side="left", padx=(0, 15), pady=(24,0))
        
        self.no_hora_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cb_data_hora_frame, text="Sem Horário", variable=self.no_hora_var, command=self._toggle_hora, font=("Arial Bold", 12)).pack(side="left", pady=(24,0))

        # --- LINHA 3 ---
        HORARIOS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
        self.modo_data_var = ctk.StringVar(value="Período (Início-Fim)")
        self.modo_combo = self._criar_combo_grid(grid_master, "Seleção de Datas", 250, ["Período (Início-Fim)", "Dias Isolados"], 3, 0)
        self.modo_combo.configure(variable=self.modo_data_var, command=self._on_modo_data_change)
        
        self.hr_inicio = self._criar_combo_grid(grid_master, "Hora Início", 250, HORARIOS, 3, 1)
        self.hr_fim = self._criar_combo_grid(grid_master, "Hora Fim", 250, HORARIOS, 3, 2)

        # --- LINHA 4 ---
        self.container_datas = ctk.CTkFrame(grid_master, fg_color="transparent")
        self.container_datas.grid(row=4, column=0, columnspan=2, sticky="w", padx=0, pady=5)
        self._on_modo_data_change()

        self.origem_combo = self._criar_combo_grid(grid_master, "Origem", 250, ["SISGEP", "SPU"], 4, 2)

        # =====================================================================
        # CONTAINER DINÂMICO
        # =====================================================================
        self.container_dinamico = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.container_dinamico.pack(fill="x", pady=(0, 15), padx=15)
        self._on_tipo_change()

        # --- RODAPÉ ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)
        ctk.CTkLabel(footer_frame, text=f"Responsável pelo Documento: {self.usuario_logado}", font=("Arial Bold", 12), text_color="#777").pack(side="left", padx=10)
        ctk.CTkButton(footer_frame, text="✅ GERAR PARECER TÉCNICO", fg_color="#0F8C75", hover_color="#0B6B59", font=("Arial Black", 16), height=50, width=320, command=self.acao_gerar).pack(side="right", padx=10)

    # --- HELPERS DE GRID UI/UX ---
    def _criar_campo_grid(self, parent, label, width, row, col, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(frame, width=width, height=35, font=("Arial", 12), fg_color="#FFFFFF", text_color="#333333", border_color="#CCCCCC")
        entry.pack(anchor="w", pady=(2,0))
        return entry
        
    def _criar_combo_grid(self, parent, label, width, values, row, col, columnspan=1, state="readonly"):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, width=width, height=35, values=values, font=("Arial", 12), state=state, **MODERN_STYLE)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    def _criar_autocomplete_grid(self, parent, label, width, values, row, col, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        
        autocomplete = ModernAutocomplete(frame, values=values, width=width)
        autocomplete.pack(anchor="w", pady=(2,0))
        return autocomplete

    def _criar_date_wrapper(self, parent, width):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 12), background="#0F8C75", foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _toggle_evento(self):
        estado = "disabled" if self.no_evento_var.get() else "normal"
        self.evento_combo.configure(state=estado)
        if self.no_evento_var.get(): self.evento_combo.set("")

    def _toggle_data(self):
        estado = "disabled" if self.no_data_var.get() else "normal"
        self.modo_combo.configure(state=estado)
        
        if hasattr(self, 'data_inicio') and self.data_inicio.winfo_exists(): self.data_inicio.configure(state=estado)
        if hasattr(self, 'data_fim') and self.data_fim.winfo_exists(): self.data_fim.configure(state=estado)
        if hasattr(self, 'data_isolada') and self.data_isolada.winfo_exists(): self.data_isolada.configure(state=estado)
        if hasattr(self, 'btn_add_data') and self.btn_add_data.winfo_exists(): self.btn_add_data.configure(state=estado)

        if self.no_data_var.get():
            self.datas_isoladas_add.clear()
            self._render_datas_chips()

    def _toggle_hora(self):
        estado = "disabled" if self.no_hora_var.get() else "readonly"
        self.hr_inicio.configure(state=estado)
        self.hr_fim.configure(state=estado)
        if self.no_hora_var.get():
            self.hr_inicio.set("")
            self.hr_fim.set("")

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

            self.btn_add_data = ctk.CTkButton(input_row, text="➕ Add Data", width=80, height=35, fg_color="#0F8C75", font=("Arial Bold", 12), command=self._add_data_isolada)
            self.btn_add_data.pack(side="left", anchor="s", pady=(0,2))

            self.frame_chips_datas = ctk.CTkFrame(f_iso, fg_color="transparent")
            self.frame_chips_datas.pack(side="top", fill="both", expand=True, pady=(15,0))
            self._render_datas_chips()
            
        self._toggle_data() 

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
            ctk.CTkLabel(self.frame_chips_datas, text="Nenhuma data isolada adicionada.", text_color="gray", font=("Arial", 11)).pack(anchor="w", padx=10)
            return
            
        for d in self.datas_isoladas_add:
            chip = ctk.CTkFrame(self.frame_chips_datas, fg_color="#F1F3F5", corner_radius=6, height=32)
            chip.pack(side="top", fill="x", pady=3)
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=d, text_color="#333", font=("Arial Bold", 12)).pack(side="left", padx=10)
            ctk.CTkButton(chip, text="X", width=24, height=24, fg_color="#F24822", hover_color="#B71C1C", font=("Arial Black", 10), command=lambda date=d: self._remove_data_isolada(date)).pack(side="right", padx=5)

    def _on_tipo_change(self, *args):
        for w in self.container_dinamico.winfo_children(): w.destroy()
        tipo = self.tipo_var.get()
        
        if tipo == "DEFERIDO":
            self.lista_linhas_banco = self.service.buscar_sugestoes_linhas()
            
            add_lin_row = ctk.CTkFrame(self.container_dinamico, fg_color="transparent")
            add_lin_row.pack(fill="x", anchor="w")
            
            self.linha_combo = self._criar_autocomplete_grid(add_lin_row, "Pesquise a Linha Afetada", 250, self.lista_linhas_banco, 0, 0)
            ctk.CTkButton(add_lin_row, text="➕ Add Linha", width=100, height=35, font=("Arial Bold", 12), fg_color="#0F8C75", command=self._add_linha).grid(row=0, column=1, sticky="s", pady=(0,10), padx=10)
            
            self.frame_chips_linhas = ctk.CTkFrame(self.container_dinamico, fg_color="transparent")
            self.frame_chips_linhas.pack(fill="both", expand=True, padx=10, pady=(0,10))
            self._render_linhas_chips()
        else:
            frame_motivo = ctk.CTkFrame(self.container_dinamico, fg_color="transparent")
            frame_motivo.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(frame_motivo, text="Motivo do Indeferimento:", font=("Arial Bold", 12), text_color="#D32F2F").pack(anchor="w")
            self.motivo_text = ctk.CTkTextbox(frame_motivo, height=80, border_width=2, fg_color="#FFFFFF", text_color="#333333", border_color="#CCCCCC")
            self.motivo_text.pack(fill="x", pady=(2,0))

    def _add_linha(self):
        lin = self.linha_combo.get().strip()
        if lin and lin != "- Sem resultados -" and lin not in self.linhas_add:
            self.linhas_add.append(lin)
            self.linha_combo.set("") 
            self._render_linhas_chips()

    def _remove_linha(self, lin):
        self.linhas_add.remove(lin)
        self._render_linhas_chips()

    def _render_linhas_chips(self):
        for w in self.frame_chips_linhas.winfo_children(): w.destroy()
        if not self.linhas_add:
            ctk.CTkLabel(self.frame_chips_linhas, text="Nenhuma linha vinculada ao desvio.", text_color="gray", font=("Arial", 11)).pack(anchor="w", padx=10)
            return
        for lin in self.linhas_add:
            chip = ctk.CTkFrame(self.frame_chips_linhas, fg_color="#F1F3F5", corner_radius=6, height=32)
            chip.pack(side="top", fill="x", pady=3)
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=lin, text_color="#333", font=("Arial Bold", 12)).pack(side="left", padx=10)
            ctk.CTkButton(chip, text="X", width=24, height=24, fg_color="#F24822", hover_color="#B71C1C", font=("Arial Black", 10), command=lambda l=lin: self._remove_linha(l)).pack(side="right", padx=5)

    def acao_gerar(self):
        tipo = self.tipo_var.get()
        
        datas_selecionadas = []
        if not self.no_data_var.get():
            if "Período" in self.modo_data_var.get():
                d_ini = self.data_inicio.get()
                d_fim = self.data_fim.get()
                datas_selecionadas = [d_ini] if d_ini == d_fim else [d_ini, d_fim]
            else:
                if not self.datas_isoladas_add:
                    messagebox.showwarning("Aviso", "Por favor, adicione pelo menos uma data isolada, ou marque 'Sem Data'.")
                    return
                datas_selecionadas = sorted(self.datas_isoladas_add.copy())
        
        periodo_hora = ""
        if not self.no_hora_var.get() and self.hr_inicio.get() and self.hr_fim.get():
            periodo_hora = f"{self.hr_inicio.get()} às {self.hr_fim.get()}"
            
        dados_form = {
            "processo": self.processo_entry.get().strip(),
            "origem": self.origem_combo.get().strip(),
            "solicitante": self.solicitante_combo.get().strip(),
            "assunto": self.assunto_combo.get().strip(),
            "evento": self.evento_combo.get() if not self.no_evento_var.get() else "",
            "datas": datas_selecionadas,
            "modo_data": "PERIODO" if "Período" in self.modo_data_var.get() else "ISOLADOS",
            "periodo": periodo_hora,
            "endereco": self.endereco_entry.get().strip(),
            "motivo": self.motivo_text.get("1.0", "end").strip() if tipo == "INDEFERIDO" else ""
        }

        if not all([dados_form["processo"], dados_form["solicitante"], dados_form["assunto"], dados_form["endereco"]]):
            messagebox.showerror("Erro", "Preencha Processo, Solicitante, Assunto e Endereço.")
            return

        if tipo == "INDEFERIDO" and len(dados_form["motivo"]) < 5:
            messagebox.showerror("Erro", "Forneça um motivo claro para o indeferimento.")
            return

        sucesso, msg = self.service.processar_parecer(tipo, dados_form, self.linhas_add, self.usuario_logado)

        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            self.processo_entry.delete(0, "end"); self.endereco_entry.delete(0, "end")
            self.linhas_add.clear(); self.datas_isoladas_add.clear()
            self._on_tipo_change()
            self._on_modo_data_change()
        else:
            messagebox.showerror("Erro", msg)

def renderizar(frame_destino, usuario_logado):
    return ParecerItinerarioView(master=frame_destino, usuario_logado=usuario_logado)