import customtkinter as ctk
from tkinter import messagebox
import re
from src.modulos.itinerario.parecer.service import ParecerItinerarioService

class ParecerItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerItinerarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        
        self.linhas_add = []
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
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Gerador de Parecer Técnico (Itinerário)", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        # --- FORMULÁRIO PRINCIPAL ---
        form_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        form_frame.pack(fill="x", pady=10, padx=10)

        # Linha 1
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(15, 5), padx=15)
        
        self.tipo_var = ctk.StringVar(value="DEFERIDO")
        cb_tipo = self._criar_combobox(row1, "Decisão do Parecer", 200, ["DEFERIDO", "INDEFERIDO"], side="left")
        cb_tipo.configure(variable=self.tipo_var, command=self._on_tipo_change)
        
        self.processo_entry = self._criar_campo(row1, "Nº Processo", 250, side="left")
        self.processo_entry.bind("<KeyRelease>", lambda e: self.processo_entry.delete(0, "end") or self.processo_entry.insert(0, self.processo_entry.get().upper()))
        
        self.solicitante_combo = self._criar_combobox(row1, "Solicitante", 350, self.lista_solicitantes, side="left")

        # Linha 2
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5, padx=15)
        self.assunto_combo = self._criar_combobox(row2, "Assunto", 350, self.lista_assuntos, side="left")
        self.endereco_entry = self._criar_campo(row2, "Endereço / Logradouro", 450, side="left")

        # Linha 3 (Eventos e Datas)
        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill="x", pady=5, padx=15)
        
        # Bloco Evento
        evento_container = ctk.CTkFrame(row3, fg_color="transparent")
        evento_container.pack(side="left", padx=10)
        ctk.CTkLabel(evento_container, text="Evento", font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        cb_evento_frame = ctk.CTkFrame(evento_container, fg_color="transparent")
        cb_evento_frame.pack(anchor="w", pady=(2,0))
        self.evento_combo = ctk.CTkComboBox(cb_evento_frame, width=250, height=35, values=self.lista_eventos)
        self.evento_combo.pack(side="left")
        
        self.no_evento_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(cb_evento_frame, text="Sem evento", variable=self.no_evento_var, command=self._toggle_evento).pack(side="left", padx=10)

        # Bloco Datas
        self.datas_entry = self._criar_campo(row3, "Data (Ex: 10032026)", 150, side="left")
        self._aplicar_mascara_data(self.datas_entry)
        
        self.hr_inicio = self._criar_campo(row3, "Hora Início", 100, side="left")
        self.hr_fim = self._criar_campo(row3, "Hora Fim", 100, side="left")
        
        self.no_data_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row3, text="Sem data/hora", variable=self.no_data_var, command=self._toggle_data).pack(side="left", padx=10, pady=(20,0))

        # --- CONTAINER DINÂMICO (DEFERIDO vs INDEFERIDO) ---
        self.container_dinamico = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.container_dinamico.pack(fill="x", pady=(15, 10), padx=15)
        self._on_tipo_change()

        # --- RODAPÉ ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)
        ctk.CTkLabel(footer_frame, text=f"Responsável: {self.usuario_logado}", font=("Arial", 12), text_color="gray").pack(side="left", padx=10)
        ctk.CTkButton(footer_frame, text="✅ GERAR PARECER", fg_color="#0F8C75", font=("Arial Bold", 16), height=50, width=300, command=self.acao_gerar).pack(side="right", padx=10)

    # --- UTILITÁRIOS ---
    def _criar_campo(self, parent, label, width, side="top"):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, padx=10, fill="x")
        ctk.CTkLabel(container, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(container, width=width, height=35)
        entry.pack(anchor="w", pady=(2,0))
        return entry
        
    def _criar_combobox(self, parent, label, width, values, side="top"):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side=side, padx=10, fill="x")
        ctk.CTkLabel(container, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(container, width=width, height=35, values=values)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    def _aplicar_mascara_data(self, entry):
        def _formatar(*args):
            nums = re.sub(r"\D", "", entry.get())
            if len(nums) > 8: nums = nums[:8]
            res = nums
            if len(nums) > 2: res = f"{nums[:2]}/{nums[2:]}"
            if len(nums) > 4: res = f"{nums[:2]}/{nums[2:4]}/{nums[4:]}"
            if entry.get() != res:
                entry.delete(0, "end"); entry.insert(0, res)
        entry.bind("<KeyRelease>", _formatar)

    def _toggle_evento(self):
        estado = "disabled" if self.no_evento_var.get() else "normal"
        self.evento_combo.configure(state=estado)
        if self.no_evento_var.get(): self.evento_combo.set("")

    def _toggle_data(self):
        estado = "disabled" if self.no_data_var.get() else "normal"
        self.datas_entry.configure(state=estado)
        self.hr_inicio.configure(state=estado)
        self.hr_fim.configure(state=estado)
        if self.no_data_var.get():
            self.datas_entry.delete(0, "end"); self.hr_inicio.delete(0, "end"); self.hr_fim.delete(0, "end")

    # --- DINAMISMO (DEFERIDO vs INDEFERIDO) ---
    def _on_tipo_change(self, *args):
        for w in self.container_dinamico.winfo_children(): w.destroy()
        tipo = self.tipo_var.get()
        
        if tipo == "DEFERIDO":
            self.linha_combo = self._criar_combobox(self.container_dinamico, "Linha a ser desviada", 350, self.service.buscar_sugestoes_linhas(), side="left")
            ctk.CTkButton(self.container_dinamico, text="➕ Add Linha", width=120, fg_color="#0F8C75", command=self._add_linha).pack(side="left", padx=10, pady=(20,0))
            self.lbl_linhas = ctk.CTkLabel(self.container_dinamico, text="Nenhuma linha.", font=("Arial", 11), text_color="gray", wraplength=400)
            self.lbl_linhas.pack(side="left", padx=15, pady=(20,0))
        else:
            ctk.CTkLabel(self.container_dinamico, text="Motivo do Indeferimento:", font=("Arial Bold", 12), text_color="#555").pack(anchor="w", padx=10)
            self.motivo_text = ctk.CTkTextbox(self.container_dinamico, height=80, border_width=2)
            self.motivo_text.pack(fill="x", padx=10, pady=(2,0))

    def _add_linha(self):
        lin = self.linha_combo.get().strip()
        if lin and lin not in self.linhas_add:
            self.linhas_add.append(lin)
            self.lbl_linhas.configure(text=" | ".join(self.linhas_add))

    # --- AÇÃO PRINCIPAL ---
    def acao_gerar(self):
        tipo = self.tipo_var.get()
        dados_form = {
            "processo": self.processo_entry.get().strip(),
            "solicitante": self.solicitante_combo.get(),
            "assunto": self.assunto_combo.get(),
            "evento": self.evento_combo.get() if not self.no_evento_var.get() else "",
            "data_evento": self.datas_entry.get(),
            "periodo": f"{self.hr_inicio.get()} às {self.hr_fim.get()}" if self.hr_inicio.get() and self.hr_fim.get() else "",
            "endereco": self.endereco_entry.get(),
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
            self.linhas_add.clear()
            self._on_tipo_change()
        else:
            messagebox.showerror("Erro", msg)

def renderizar(frame_destino, usuario_logado):
    return ParecerItinerarioView(master=frame_destino, usuario_logado=usuario_logado)