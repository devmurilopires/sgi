import customtkinter as ctk
from tkinter import messagebox
import re
from src.modulos.projetos_mobilidade.parecer.service import ParecerProjetosMobilidadeService
from src.core.shared.components.parameters_combo import CtkParametrosComboBox

class ParecerProjetosMobilidadeView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = ParecerProjetosMobilidadeService()
        self.usuario_logado = usuario_logado

        self._construir_interface()

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#F4F6F9")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- CABEÇALHO ---
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Gerador de Parecer - Projetos de Mobilidade", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        # --- DADOS DO PROCESSO (BLOCO PRINCIPAL) ---
        bloco1 = ctk.CTkFrame(self.scroll_frame, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        bloco1.pack(fill="x", pady=10, padx=10)

        # Linha 1: Decisão, Origem e Processo
        row1 = ctk.CTkFrame(bloco1, fg_color="transparent")
        row1.pack(fill="x", pady=(20, 10), padx=20)

        # MODIFICAÇÃO: "Tipo de Parecer" agora usa o componente do Banco de Dados
        self.tipo_parecer_combo = self._criar_param_combo(row1, "Decisão", "Projetos de Mobilidade", "DECISAO_PARECER", width=200, command=self._on_tipo_change)
        
        # MODIFICAÇÃO: Atribuindo à variável self.origem_combo para podermos ler com .get()
        self.origem_combo = self._criar_param_combo(row1, "Origem do Processo", "Projetos de Mobilidade", "ORIGEM", width=200)

        self.processo_var = ctk.StringVar()
        self.processo_var.trace_add("write", self._formatar_processo)
        self._criar_entry(row1, "Nº do Processo", self.processo_var, width=400)

        # Linha 2: Solicitante e Assunto
        row2 = ctk.CTkFrame(bloco1, fg_color="transparent")
        row2.pack(fill="x", pady=(10, 20), padx=20)

        self.solicitante_combo = self._criar_param_combo(row2, "Solicitante", "Projetos de Mobilidade", "SOLICITANTE_PARECER", width=350)
        self.assunto_combo = self._criar_param_combo(row2, "Assunto", "Projetos de Mobilidade", "ASSUNTO_PROJETOS_MOBILIDADE", width=450)

        # --- MOTIVO DE INDEFERIMENTO (Oculto por Padrão) ---
        self.frame_motivo = ctk.CTkFrame(self.scroll_frame, fg_color="#FFF0F0", corner_radius=10, border_width=1, border_color="#FFD6D6")
        
        ctk.CTkLabel(self.frame_motivo, text="Motivo do Indeferimento:", font=("Arial Bold", 13), text_color="#C21010").pack(anchor="w", padx=20, pady=(15, 5))
        self.motivo_text = ctk.CTkTextbox(self.frame_motivo, height=120, fg_color="#FFFFFF", border_color="#FFD6D6", border_width=1)
        self.motivo_text.pack(fill="x", padx=20, pady=(0, 20))

        # --- RODAPÉ COM BOTÃO ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=30)
        
        nome_usuario = self.usuario_logado.get('nome') if isinstance(self.usuario_logado, dict) else self.usuario_logado
        ctk.CTkLabel(footer_frame, text=f"Auditoria: Responsável {nome_usuario}", text_color="gray", font=("Arial", 12)).pack(side="left", padx=10)
        
        self.btn_gerar = ctk.CTkButton(footer_frame, text="📄 GERAR PARECER TÉCNICO", fg_color="#0F8C75", hover_color="#0B6B59", font=("Arial Bold", 16), height=50, width=300, command=self._acao_gerar_parecer)
        self.btn_gerar.pack(side="right", padx=10)

    # --- UTILITÁRIOS VISUAIS ---
    def _criar_entry(self, parent, label_text, variable, width):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        ctk.CTkEntry(container, textvariable=variable, width=width, height=38, fg_color="#F9FAFB", border_color="#D1D5DB").pack(anchor="w", pady=(2,0))

    # MODIFICAÇÃO: Helper atualizado para suportar callback 'command'
    def _criar_param_combo(self, parent, label_text, setor, campo, width, command=None):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(side="left", padx=10, fill="x")
        ctk.CTkLabel(container, text=label_text, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = CtkParametrosComboBox(container, setor=setor, campo=campo, width=width, height=38, fg_color="#F9FAFB", command=command)
        combo.pack(anchor="w", pady=(2,0))
        return combo

    # --- LÓGICAS DE INTERFACE ---
    def _on_tipo_change(self, *args):
        # Validação blindada lendo direto do componente
        if self.tipo_parecer_combo.get().upper() == "INDEFERIDO":
            self.frame_motivo.pack(fill="x", pady=10, padx=10, before=self.scroll_frame.winfo_children()[-1])
            self.btn_gerar.configure(fg_color="#C21010", hover_color="#9E0D0D")
        else:
            self.frame_motivo.pack_forget()
            self.btn_gerar.configure(fg_color="#0F8C75", hover_color="#0B6B59")

    def _formatar_processo(self, *args):
        val = self.processo_var.get().upper()
        val = re.sub(r'[^a-zA-Z0-9]', '', val)
        if len(val) > 5: val = f"{val[:-4]}/{val[-4:]}"
        self.processo_var.set(val)

    # --- AÇÃO PRINCIPAL ---
    def _acao_gerar_parecer(self):
        dados_form = {
            'tipo': self.tipo_parecer_combo.get().strip(),
            'origem': self.origem_combo.get().strip(), # Coletando a Origem
            'processo': self.processo_var.get().strip(),
            'solicitante': self.solicitante_combo.get().strip(),
            'assunto': self.assunto_combo.get().strip(),
            'motivo': self.motivo_text.get("1.0", "end").strip()
        }

        if not all([dados_form['processo'], dados_form['origem'], dados_form['solicitante'], dados_form['assunto']]):
            return messagebox.showwarning("Aviso", "Por favor, preencha Processo, Origem, Solicitante e Assunto.")

        if dados_form['tipo'].upper() == "INDEFERIDO" and not dados_form['motivo']:
            return messagebox.showwarning("Aviso", "É obrigatório informar o Motivo para pareceres Indeferidos.")

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
        self.motivo_text.delete("1.0", "end")
        self.tipo_parecer_combo.set("DEFERIDO")

def renderizar(frame_destino, usuario_logado):
    return ParecerProjetosMobilidadeView(master=frame_destino, usuario_logado=usuario_logado)