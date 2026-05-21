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


class ParecerItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerItinerarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        
        self.linhas_add = []
        self.datas_isoladas_add = []
        self._construir_interface()

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

        def upper_processo_par(event):
            if getattr(event, 'keysym', '') in ['Up', 'Down', 'Left', 'Right', 'Home', 'End']: return
            texto = self.processo_entry.get()
            if texto != texto.upper():
                pos = self.processo_entry.index("insert")
                self.processo_entry.delete(0, "end")
                self.processo_entry.insert(0, texto.upper())
                self.processo_entry.icursor(pos)
                
        self.processo_entry.bind("<KeyRelease>", upper_processo_par)

        # Solicitante DINÂMICO (Atualizado para a nova chave global)
        self.solicitante_combo = self._criar_param_combo_grid(grid_master, "Solicitante", "Itinerário", "SOLICITANTE_PARECER", 250, 0, 2)

        # --- LINHA 1 ---
        # Assunto DINÂMICO (Atualizado para a nova chave do Itinerário)
        self.assunto_combo = self._criar_param_combo_grid(grid_master, "Assunto", "Itinerário", "ASSUNTO_ITINERARIO", 250, 1, 0)
        self.endereco_entry = self._criar_campo_grid(grid_master, "Endereço / Logradouro", 520, 1, 1, columnspan=2)

        # --- LINHA 2 ---
        # Evento DINÂMICO
        self.evento_combo = self._criar_param_combo_grid(grid_master, "Evento", "Itinerário", "EVENTO", 250, 2, 0)
        
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

        # Origem DINÂMICA
        self.origem_combo = self._criar_param_combo_grid(grid_master, "Origem", "Itinerário", "ORIGEM", 250, 4, 2)

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

    def _criar_param_combo_grid(self, parent, label, setor, campo, width, row, col, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        from src.core.shared.components.parameters_combo import CtkParametrosComboBox
        combo = CtkParametrosComboBox(frame, setor=setor, campo=campo, width=width, height=35, **MODERN_STYLE)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    def _criar_autocomplete_grid(self, parent, label, width, values, row, col, columnspan=1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        
        # Integração do novo Autocomplete
        autocomplete = Autocomplete(frame, values=values, width=width, height=35, font=("Arial", 12), fg_color="#FFFFFF", text_color="#333333", border_color="#CCCCCC")
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
            self.linha_combo.configure(placeholder_text="Código ou Nome...")
            
            # Gatilho Mágico: O 'Enter' na linha adiciona ela direto!
            self.linha_combo.bind("<<AutocompleteSelected>>", lambda e: self._add_linha())
            
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
            "evento": self.evento_combo.get().strip() if not self.no_evento_var.get() else "",
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