import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import re
from src.modulos.quadro_horario.parecer.service import ParecerQuadroHorarioService

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
        """
        Constrói as listas que alimentarão os Comboboxes (dropdowns) da tela,
        buscando os dados atualizados diretamente do banco de dados.
        """
        # Busca dinâmica via banco de dados
        self.lista_solicitantes = self.service.buscar_opcoes_dropdown('qh_solicitante')
        self.lista_assuntos = self.service.buscar_opcoes_dropdown('qh_assunto')
        self.lista_eventos = self.service.buscar_opcoes_dropdown('qh_evento')
        self.linhas_disponiveis = self.service.buscar_sugestoes_linhas()

        # Fallback (Plano B) de Segurança: 
        # Caso o banco esteja vazio ou ocorra um erro de conexão, 
        # garantimos que o sistema não quebre e tenha ao menos a opção "Outros".
        if not self.lista_solicitantes:
            self.lista_solicitantes = ["Outros"]
        if not self.lista_assuntos:
            self.lista_assuntos = ["Outros"]
        if not self.lista_eventos:
            self.lista_eventos = ["Outros"]

    def _construir_interface(self):
        top_bar = ctk.CTkFrame(self, fg_color="#FFFFFF", height=70, corner_radius=0)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        ctk.CTkLabel(top_bar, text="📄 Geração de Parecer", font=("Arial Black", 18), text_color="#0F8C75").pack(side="left", padx=20, pady=15)

        self.container_principal = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.container_principal.pack(fill="both", expand=True, padx=20, pady=15)

        card_bg = ctk.CTkFrame(self.container_principal, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E5E7EB")
        card_bg.pack(fill="both", expand=True, padx=10, pady=10)

        self.form_frame = ctk.CTkFrame(card_bg, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=30, pady=30)
        self.form_frame.columnconfigure((0, 1), weight=1, uniform="col")

        # --- LINHA 0: Processo e Origem ---
        f_proc = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        f_proc.grid(row=0, column=0, padx=(0, 15), pady=(0, 20), sticky="ew")
        ctk.CTkLabel(f_proc, text="Nº Processo:", font=("Arial Bold", 13), text_color="#4B5563").pack(anchor="w", pady=(0, 5))
        self.processo_entry = ctk.CTkEntry(f_proc, height=40, font=("Arial", 13))
        self.processo_entry.pack(fill="x")
        self.processo_entry.bind("<KeyRelease>", self._formatar_processo)

        f_origem = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        f_origem.grid(row=0, column=1, padx=(15, 0), pady=(0, 20), sticky="ew")
        ctk.CTkLabel(f_origem, text="Origem do Processo:", font=("Arial Bold", 13), text_color="#4B5563").pack(anchor="w", pady=(0, 5))
        self.origem_combo = ctk.CTkComboBox(f_origem, values=["SPU", "SISGEP"], height=40, font=("Arial", 13))
        self.origem_combo.pack(fill="x")

        # --- LINHA 1: Solicitante e Assunto ---
        f_sol = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        f_sol.grid(row=1, column=0, padx=(0, 15), pady=(0, 20), sticky="ew")
        ctk.CTkLabel(f_sol, text="Solicitante:", font=("Arial Bold", 13), text_color="#4B5563").pack(anchor="w", pady=(0, 5))
        self.solicitante_combo = ctk.CTkComboBox(f_sol, values=self.lista_solicitantes, height=40, font=("Arial", 13))
        self.solicitante_combo.pack(fill="x")

        f_ass = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        f_ass.grid(row=1, column=1, padx=(15, 0), pady=(0, 20), sticky="ew")
        ctk.CTkLabel(f_ass, text="Assunto:", font=("Arial Bold", 13), text_color="#4B5563").pack(anchor="w", pady=(0, 5))
        self.assunto_combo = ctk.CTkComboBox(self.form_frame, values=self.lista_assuntos, height=40, font=("Arial", 13))
        self.assunto_combo.grid(row=1, column=1, padx=(15, 0), pady=(0, 20), sticky="ew")

        # --- LINHA 2: Linha Afetada (Esquerda) e Evento (Direita) ---
        f_linha_section = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        f_linha_section.grid(row=2, column=0, padx=(0, 15), pady=(0, 20), sticky="new")
        ctk.CTkLabel(f_linha_section, text="Linha Afetada:", font=("Arial Bold", 13), text_color="#4B5563").pack(anchor="w", pady=(0, 5))
        
        f_linha_input = ctk.CTkFrame(f_linha_section, fg_color="transparent")
        f_linha_input.pack(fill="x", pady=(0, 5))
        self.linha_combo = Autocomplete(f_linha_input, values=self.linhas_disponiveis, height=40, font=("Arial", 13), placeholder_text="Código ou Nome...")
        self.linha_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.linha_combo.bind("<<AutocompleteSelected>>", self._adicionar_linha)
        self.btn_add_linha = ctk.CTkButton(f_linha_input, text="➕", fg_color="#10B981", hover_color="#059669", height=40, width=40, command=self._adicionar_linha)
        self.btn_add_linha.pack(side="right")
        self.frame_chips_linhas = ctk.CTkFrame(f_linha_section, fg_color="transparent")
        self.frame_chips_linhas.pack(fill="x")

        f_evento_section = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        f_evento_section.grid(row=2, column=1, padx=(15, 0), pady=(0, 20), sticky="new")
        ctk.CTkLabel(f_evento_section, text="Evento (Opcional):", font=("Arial Bold", 13), text_color="#4B5563").pack(anchor="w", pady=(0, 5))
        self.evento_combo = ctk.CTkComboBox(f_evento_section, values=[""] + self.lista_eventos, height=40, font=("Arial", 13), 
                                            command=lambda _: self._on_evento_change())
        self.evento_combo.pack(fill="x")

        # --- LINHA 3: Seção de Datas (Só aparece se houver Evento) ---
        self.f_data_full_section = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        # Inicialmente escondida via grid_remove na inicialização
        
        self.f_data_full_section.columnconfigure((0, 1), weight=1, uniform="col")
        
        f_data_lbls = ctk.CTkFrame(self.f_data_full_section, fg_color="transparent")
        f_data_lbls.grid(row=0, column=1, padx=(15, 0), pady=(0, 5), sticky="ew")
        self.lbl_modo_data = ctk.CTkLabel(f_data_lbls, text="Data do Evento:", font=("Arial Bold", 13), text_color="#4B5563")
        self.lbl_modo_data.pack(side="left")
        self.modo_data_var = ctk.StringVar(value="Isolada")
        self.seg_modo_data = ctk.CTkSegmentedButton(f_data_lbls, values=["Isolada", "Período"], variable=self.modo_data_var, command=self._on_modo_data_change, height=25)
        self.seg_modo_data.pack(side="right")

        self.frame_data_container = ctk.CTkFrame(self.f_data_full_section, fg_color="transparent", height=45)
        self.frame_data_container.grid(row=1, column=1, padx=(15, 0), pady=(0, 5), sticky="ew")
        self.frame_data_container.grid_propagate(False)

        self.frame_chips_datas = ctk.CTkFrame(self.f_data_full_section, fg_color="transparent")
        self.frame_chips_datas.grid(row=2, column=1, padx=(15, 0), pady=(0, 20), sticky="ew")

        # --- LINHA 4: Decisão ---
        f_decisao = ctk.CTkFrame(self.form_frame, fg_color="#F9FAFB", corner_radius=8, border_width=1, border_color="#E5E7EB")
        f_decisao.grid(row=4, column=0, columnspan=2, pady=(10, 20), sticky="ew", ipadx=10, ipady=10)
        ctk.CTkLabel(f_decisao, text="Decisão do Parecer:", font=("Arial Bold", 14), text_color="#374151").pack(pady=(10, 5))
        
        self.tipo_parecer_var = ctk.StringVar(value="DEFERIDO")
        self.seg_tipo = ctk.CTkSegmentedButton(f_decisao, values=["DEFERIDO", "INDEFERIDO"], variable=self.tipo_parecer_var, 
                                               font=("Arial Bold", 13), selected_color="#0F8C75", selected_hover_color="#0B6B59", 
                                               height=40, width=300, command=self._on_tipo_change)
        self.seg_tipo.pack(pady=(0, 10))

        # --- LINHA 5: Motivo Indeferimento ---
        self.frame_indeferido = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        self.frame_indeferido.grid(row=5, column=0, columnspan=2, pady=(0, 20), sticky="ew")
        ctk.CTkLabel(self.frame_indeferido, text="Motivo do Indeferimento:", font=("Arial Bold", 13), text_color="#D32F2F").pack(anchor="w", pady=(0, 5))
        self.motivo_text = ctk.CTkTextbox(self.frame_indeferido, height=100, border_width=1, border_color="#D1D5DB", font=("Arial", 13))
        self.motivo_text.pack(fill="x")

        # --- LINHA 6: Botão Gerar ---
        self.btn_gerar = ctk.CTkButton(self.container_principal, text="Gerar Documento de Parecer", font=("Arial Bold", 15), 
                                       fg_color="#0F8C75", hover_color="#0B6B59", height=50, width=350, command=self._acao_gerar)
        self.btn_gerar.pack(pady=10)

        # Inicialização do estado dinâmico
        self._on_evento_change() 
        self._on_tipo_change()

    def _on_evento_change(self):
        val = self.evento_combo.get().strip()
        if val:
            # Mostra seção de datas na linha 3
            self.f_data_full_section.grid(row=3, column=0, columnspan=2, sticky="ew")
            self._on_modo_data_change()
        else:
            # Esconde e reseta datas
            self.f_data_full_section.grid_remove()
            self.datas_isoladas_add.clear()
            self._render_datas_chips()
        self._aplicar_regras_negocio()

    def _formatar_processo(self, event):
        v = re.sub(r'[^a-zA-Z0-9]', '', self.processo_entry.get())
        if len(v) > 5: v = f"{v[:-4]}/{v[-4:]}"
        self.processo_entry.delete(0, "end")
        self.processo_entry.insert(0, v)

    def _adicionar_linha(self, event=None):
        linha = self.linha_combo.get().strip()
        if linha and linha not in self.linhas_add:
            self.linhas_add.append(linha)
            self._render_linhas_chips()
            self.linha_combo.set("")
            self._aplicar_regras_negocio()

    def _remover_linha(self, linha):
        if linha in self.linhas_add:
            self.linhas_add.remove(linha)
            self._render_linhas_chips()
            self._aplicar_regras_negocio()

    def _render_linhas_chips(self):
        for widget in self.frame_chips_linhas.winfo_children(): widget.destroy()
        for i, linha in enumerate(self.linhas_add):
            chip = ctk.CTkFrame(self.frame_chips_linhas, fg_color="#E5E7EB", corner_radius=10)
            chip.grid(row=i//3, column=i%3, padx=(0, 5), pady=(0, 5), sticky="w")
            linha_text = linha if len(linha) < 18 else linha[:15] + "..."
            ctk.CTkLabel(chip, text=linha_text, text_color="#374151", font=("Arial", 11)).pack(side="left", padx=(8, 4), pady=2)
            btn = ctk.CTkButton(chip, text="✕", width=20, height=20, fg_color="transparent", text_color="#EF4444", hover_color="#D1D5DB", command=lambda l=linha: self._remover_linha(l))
            btn.pack(side="left", padx=(0, 5))

    def _on_modo_data_change(self, *args):
        for widget in self.frame_data_container.winfo_children(): widget.destroy()
        modo = self.modo_data_var.get()
        inner = ctk.CTkFrame(self.frame_data_container, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        if modo == "Isolada":
            self.data_isolada_entry = DateEntry(inner, width=15, background='#0F8C75', foreground='white', borderwidth=0, font=("Arial", 12))
            self.data_isolada_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.btn_add_data = ctk.CTkButton(inner, text="➕", fg_color="#10B981", hover_color="#059669", height=40, width=40, command=self._adicionar_data_isolada)
            self.btn_add_data.pack(side="right")
            self.frame_chips_datas.grid() 
        else:
            self.data_ini_entry = DateEntry(inner, width=14, background='#0F8C75', foreground='white', borderwidth=0, font=("Arial", 12))
            self.data_ini_entry.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(inner, text="até", text_color="#6B7280", font=("Arial Bold", 12)).pack(side="left", padx=10)
            self.data_fim_entry = DateEntry(inner, width=14, background='#0F8C75', foreground='white', borderwidth=0, font=("Arial", 12))
            self.data_fim_entry.pack(side="left", fill="x", expand=True)
            self.frame_chips_datas.grid_remove() 
        self._aplicar_regras_negocio()

    def _adicionar_data_isolada(self):
        dt = self.data_isolada_entry.get()
        if dt and dt not in self.datas_isoladas_add:
            self.datas_isoladas_add.append(dt)
            self._render_datas_chips()
            self._aplicar_regras_negocio()

    def _remover_data(self, dt):
        if dt in self.datas_isoladas_add:
            self.datas_isoladas_add.remove(dt)
            self._render_datas_chips()
            self._aplicar_regras_negocio()

    def _render_datas_chips(self):
        for widget in self.frame_chips_datas.winfo_children(): widget.destroy()
        for i, dt in enumerate(self.datas_isoladas_add):
            chip = ctk.CTkFrame(self.frame_chips_datas, fg_color="#D1FAE5", corner_radius=10)
            chip.grid(row=i//3, column=i%3, padx=(0, 5), pady=(0, 5), sticky="w")
            ctk.CTkLabel(chip, text=dt, text_color="#065F46", font=("Arial", 11)).pack(side="left", padx=(10, 5), pady=2)
            btn = ctk.CTkButton(chip, text="✕", width=20, height=20, fg_color="transparent", text_color="#EF4444", hover_color="#A7F3D0", command=lambda d=dt: self._remover_data(d))
            btn.pack(side="left", padx=(0, 5))

    def _on_tipo_change(self, *args):
        tipo = self.tipo_parecer_var.get()
        if tipo == "INDEFERIDO":
            self.frame_indeferido.grid() 
            self.btn_gerar.configure(fg_color="#D32F2F", hover_color="#B71C1C")
        else:
            self.frame_indeferido.grid_remove() 
            self.btn_gerar.configure(fg_color="#0F8C75", hover_color="#0B6B59")

    def _aplicar_regras_negocio(self):
        modo_data = self.modo_data_var.get()
        evento_val = self.evento_combo.get().strip()
        has_linhas = len(self.linhas_add) > 0
        has_datas = (modo_data == "Isolada" and len(self.datas_isoladas_add) > 0)
        
        if has_linhas:
            self.evento_combo.set("")
            self.evento_combo.configure(state="disabled")
            self.f_data_full_section.grid_remove()
        else:
            self.evento_combo.configure(state="normal")
            if evento_val or has_datas:
                self.linha_combo.set("")
                self.linha_combo.configure(state="disabled")
                self.btn_add_linha.configure(state="disabled")
            else:
                self.linha_combo.configure(state="normal")
                self.btn_add_linha.configure(state="normal")

    def _acao_gerar(self):
        tipo = self.tipo_parecer_var.get()
        modo_data = self.modo_data_var.get()
        datas_selecionadas = self.datas_isoladas_add.copy() if modo_data == "Isolada" else [self.data_ini_entry.get(), self.data_fim_entry.get()]

        dados_form = {
            "processo": self.processo_entry.get().strip(),
            "origem": self.origem_combo.get().strip(),
            "solicitante": self.solicitante_combo.get().strip(),
            "assunto": self.assunto_combo.get().strip(),
            "evento": self.evento_combo.get().strip(),
            "datas": datas_selecionadas,
            "motivo": self.motivo_text.get("1.0", "end").strip() if tipo == "INDEFERIDO" else ""
        }

        if not all([dados_form["processo"], dados_form["origem"], dados_form["solicitante"], dados_form["assunto"]]):
            return messagebox.showerror("Erro", "Preencha Processo, Origem, Solicitante e Assunto.")

        if not self.linhas_add and not dados_form["evento"]:
            return messagebox.showerror("Erro", "Informe um Evento ou adicione ao menos uma Linha afetada.")

        sucesso, msg = self.service.processar_parecer(tipo, dados_form, self.linhas_add, self.usuario_logado)
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            self.processo_entry.delete(0, "end")
            self.linhas_add.clear(); self._render_linhas_chips()
            self.evento_combo.set(""); self._on_evento_change()
        else: messagebox.showerror("Erro", msg)

def renderizar(frame_destino, usuario_logado):
    return ParecerQuadroHorarioView(master=frame_destino, usuario_logado=usuario_logado)