import customtkinter as ctk
from tkinter import messagebox
import re
from src.modulos.projetos_mobilidade.parecer.service import ParecerProjetosMobilidadeService
from src.core.shared.components.parameters_combo import CtkParametrosComboBox

from src.core.shared.colors import COLOR_PRIMARY, COLOR_BG, COLOR_WHITE, COLOR_HOVER, COLOR_TEXT

class ParecerProjetosMobilidadeView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerProjetosMobilidadeService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado

        self._construir_interface()
        
    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLOR_BG)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- CABEÇALHO ---
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Gerador de Parecer - Projetos de Mobilidade", font=("Arial Black", 24), text_color=COLOR_PRIMARY).pack(side="left")

        # --- DADOS DO PROCESSO (BLOCO PRINCIPAL) ---
        bloco1 = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_WHITE, corner_radius=10, border_width=1, border_color="#E0E0E0")
        bloco1.pack(fill="x", pady=10, padx=10)

        # Linha 1: Decisão, Origem e Processo
        row1 = ctk.CTkFrame(bloco1, fg_color="transparent")
        row1.pack(fill="x", pady=(20, 10), padx=20)

        self.tipo_parecer_combo = self._criar_param_combo(row1, "Decisão", "Projetos de Mobilidade", "DECISAO_PARECER", width=400, command=self._on_tipo_change)
        self.origem_combo = self._criar_param_combo(row1, "Origem do Processo", "Projetos de Mobilidade", "ORIGEM", width=400)

        self.processo_var = ctk.StringVar()
        self.processo_var.trace_add("write", self._formatar_processo)
        self._criar_entry(row1, "Nº do Processo", self.processo_var, width=400)

        # Linha 2: Solicitante e Assunto
        row2 = ctk.CTkFrame(bloco1, fg_color="transparent")
        row2.pack(fill="x", pady=(10, 20), padx=20)

        self.solicitante_combo = self._criar_param_combo(row2, "Solicitante", "Projetos de Mobilidade", "SOLICITANTE_PARECER", width=610)
        self.assunto_combo = self._criar_param_combo(row2, "Assunto", "Projetos de Mobilidade", "ASSUNTO_PROJETOS_MOBILIDADE", width=610)

        # --- RODAPÉ COM BOTÃO ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=30)
        
        nome_usuario = self.usuario_logado.get('nome') if isinstance(self.usuario_logado, dict) else self.usuario_logado
        ctk.CTkLabel(footer_frame, text=f"Auditoria: Responsável {nome_usuario}", text_color="gray", font=("Arial", 12)).pack(side="left", padx=10)
        
        self.btn_gerar = ctk.CTkButton(footer_frame, text="📄 GERAR PARECER TÉCNICO", fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, font=("Arial Bold", 16), height=50, width=300, command=self._acao_gerar_parecer)
        self.btn_gerar.pack(side="right", padx=10)

    # --- UTILITÁRIOS VISUAIS ---
    def _criar_entry(self, parent, label_text, variable, width):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w")
        ctk.CTkEntry(container, textvariable=variable, width=width, height=38, fg_color=COLOR_BG, border_color=COLOR_PRIMARY, border_width=1).pack(anchor="w", pady=(2,0))

    def _criar_param_combo(self, parent, label_text, setor, campo, width, command=None):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(anchor="w")
        combo = CtkParametrosComboBox(container, setor=setor, campo=campo, width=width, height=38, fg_color=COLOR_BG, command=command)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    # --- LÓGICAS DE INTERFACE ---
    def _on_tipo_change(self, *args):
        # Apenas altera a cor do botão, o painel de motivo foi removido
        if self.tipo_parecer_combo.get().upper() == "INDEFERIDO":
            self.btn_gerar.configure(fg_color="#C21010", hover_color="#9E0D0D")
        else:
            self.btn_gerar.configure(fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER)

    def _formatar_processo(self, *args):
        texto_original = self.processo_var.get()
        val = texto_original.upper()
        if texto_original != val:
            self.processo_var.set(val)

    # --- AÇÃO PRINCIPAL ---
    def _acao_gerar_parecer(self):
        dados_form = {
            'tipo': self.tipo_parecer_combo.get().strip(),
            'origem': self.origem_combo.get().strip(),
            'processo': self.processo_var.get().strip(),
            'solicitante': self.solicitante_combo.get().strip(),
            'assunto': self.assunto_combo.get().strip()
        }

        if not all([dados_form['processo'], dados_form['origem'], dados_form['solicitante'], dados_form['assunto']]):
            return messagebox.showwarning("Aviso", "Por favor, preencha Processo, Origem, Solicitante e Assunto.")

        sucesso, msg = self.service.processar_geracao_parecer(dados_form, self.usuario_logado)
        
        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            self._limpar_formulario()
        else:
            messagebox.showerror("Erro", msg)

    def _limpar_formulario(self):
        self.processo_var.set("")
        self.origem_combo.set("")
        self.solicitante_combo.set("")
        self.assunto_combo.set("")
        self.tipo_parecer_combo.set("DEFERIDO")

def renderizar(frame_destino, usuario_logado):
    return ParecerProjetosMobilidadeView(master=frame_destino, usuario_logado=usuario_logado)