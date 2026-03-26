import customtkinter as ctk
from tkinter import messagebox
import re
from src.modulos.quadro_horario.parecer.service import ParecerQuadroHorarioService

class ParecerQuadroHorarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerQuadroHorarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        
        self.linhas_add = []
        self._construir_listas_padrao()
        self._construir_interface()

    def _construir_listas_padrao(self):
        self.lista_solicitantes = ["AGEFIS", "AMC", "Cidadão", "CMF", "Comunidade", "Construtoras", "Empresas Operadoras", "Sindiônibus", "Outros"]
        self.lista_assuntos = ["Aumento de frota para concurso", "Aumento de frota", "Redução de frota", "Execesso de demanda", "Remoção de empresas", "Retorno de Linha", "Mudança de frota", "Intervalo irregular", "Diversos--Requerimentos", "Inclusão de viagens", "Outros"]
        self.lista_eventos = ["cultural", "esportivo", "religioso", "festival junino", "comunitário", "festas", "parada da diversidade sexual", "fortal", "academia enem", "caminhada com maria", "evangelizar", "Outros"]

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # CABEÇALHO
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Gerador de Parecer Técnico (Quadro de Horários)", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        # FORMULÁRIO PRINCIPAL
        form_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        form_frame.pack(fill="x", pady=10, padx=10)

        # Linha 1: Tipo e Processo
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(15, 5), padx=15)
        
        self.tipo_var = ctk.StringVar(value="DEFERIDO")
        cb_tipo = self._criar_combobox(row1, "Decisão do Parecer", 200, ["DEFERIDO", "INDEFERIDO"], side="left")
        cb_tipo.configure(variable=self.tipo_var, command=self._on_tipo_change)
        
        self.processo_entry = self._criar_campo(row1, "Nº Processo", 250, side="left")
        self.processo_entry.bind("<KeyRelease>", lambda e: self.processo_entry.delete(0, "end") or self.processo_entry.insert(0, self.processo_entry.get().upper()))
        
        self.solicitante_combo = self._criar_combobox(row1, "Solicitante", 350, self.lista_solicitantes, side="left")

        # Linha 2: Assunto e Solicitação
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5, padx=15)
        self.assunto_combo = self._criar_combobox(row2, "Assunto", 380, self.lista_assuntos, side="left")
        self.solicitacao_combo = self._criar_combobox(row2, "Solicitação", 380, self.lista_assuntos, side="left")

        # Linha 3: Evento e Datas (Opcional)
        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill="x", pady=5, padx=15)
        
        self.evento_combo = self._criar_combobox(row3, "Evento (Deixe em branco se for Linha)", 300, [""] + self.lista_eventos, side="left")
        self.evento_combo.configure(command=self._on_evento_change)
        
        self.datas_entry = self._criar_campo(row3, "Data Evento (Ex: 10032026)", 250, side="left")
        self._aplicar_mascara_data(self.datas_entry)

        # --- CONTAINER DINÂMICO (Linhas vs Motivo) ---
        self.container_dinamico = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.container_dinamico.pack(fill="x", pady=(15, 10), padx=15)
        self._on_tipo_change()

        # --- RODAPÉ ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)
        ctk.CTkLabel(footer_frame, text=f"Responsável: {self.usuario_logado}", font=("Arial", 12), text_color="gray").pack(side="left", padx=10)
        ctk.CTkButton(footer_frame, text="✅ GERAR PARECER SPR", fg_color="#0F8C75", font=("Arial Bold", 16), height=50, width=300, command=self.acao_gerar).pack(side="right", padx=10)

    # FUNÇÕES DE INTERFACE
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

    def _on_evento_change(self, val):
        # Desabilita o combo de linhas se preencher evento
        if val: self.linha_combo.configure(state="disabled")
        else: self.linha_combo.configure(state="normal")

    def _on_tipo_change(self, *args):
        for w in self.container_dinamico.winfo_children(): w.destroy()
        tipo = self.tipo_var.get()
        
        # Frame das Linhas (Sempre aparece)
        frame_linhas = ctk.CTkFrame(self.container_dinamico, fg_color="transparent")
        frame_linhas.pack(fill="x", pady=5)
        self.linha_combo = self._criar_combobox(frame_linhas, "Linha afetada", 350, self.service.buscar_sugestoes_linhas(), side="left")
        ctk.CTkButton(frame_linhas, text="➕ Add Linha", width=120, fg_color="#0F8C75", command=self._add_linha).pack(side="left", padx=10, pady=(20,0))
        self.lbl_linhas = ctk.CTkLabel(frame_linhas, text="Nenhuma linha.", font=("Arial", 11), text_color="gray", wraplength=400)
        self.lbl_linhas.pack(side="left", padx=15, pady=(20,0))
        
        # Motivo (Apenas Indeferido)
        if tipo == "INDEFERIDO":
            ctk.CTkLabel(self.container_dinamico, text="Motivo do Indeferimento:", font=("Arial Bold", 12), text_color="#555").pack(anchor="w", padx=10, pady=(10,0))
            self.motivo_text = ctk.CTkTextbox(self.container_dinamico, height=80, border_width=2)
            self.motivo_text.pack(fill="x", padx=10, pady=(2,0))

    def _add_linha(self):
        lin = self.linha_combo.get().strip()
        if lin and lin not in self.linhas_add:
            self.linhas_add.append(lin)
            self.lbl_linhas.configure(text=" | ".join(self.linhas_add))
            self.evento_combo.set("") # Limpa o evento se adicionar linha

    # AÇÃO PRINCIPAL
    def acao_gerar(self):
        tipo = self.tipo_var.get()
        dados = {
            "processo": self.processo_entry.get().strip(),
            "solicitante": self.solicitante_combo.get(),
            "assunto": self.assunto_combo.get(),
            "solicitacao": self.solicitacao_combo.get(),
            "evento": self.evento_combo.get(),
            "data_evento": self.datas_entry.get(),
            "motivo": self.motivo_text.get("1.0", "end").strip() if tipo == "INDEFERIDO" else ""
        }

        if not all([dados["processo"], dados["solicitante"], dados["assunto"], dados["solicitacao"]]):
            return messagebox.showerror("Erro", "Preencha Processo, Solicitante, Assunto e Solicitação.")

        if tipo == "DEFERIDO" and not (self.linhas_add or dados["evento"]):
            return messagebox.showerror("Erro", "Informe um Evento ou adicione ao menos uma Linha.")

        if tipo == "INDEFERIDO" and len(dados["motivo"]) < 5:
            return messagebox.showerror("Erro", "Forneça um motivo claro para o indeferimento.")

        sucesso, msg = self.service.processar_parecer(tipo, dados, self.linhas_add, self.usuario_logado)

        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            self.processo_entry.delete(0, "end")
            self.linhas_add.clear()
            self._on_tipo_change()
        else: messagebox.showerror("Erro", msg)

def renderizar(frame_destino, usuario_logado):
    return ParecerQuadroHorarioView(master=frame_destino, usuario_logado=usuario_logado)