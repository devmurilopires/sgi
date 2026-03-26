import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter.ttk as ttk
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

        self._construir_interface()

    def _construir_interface(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#FFFFFF")
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- CABEÇALHO ---
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="Gerador de Ordem de Serviço (Itinerário)", font=("Arial Black", 24), text_color="#0F8C75").pack(side="left")

        # --- FORMULÁRIO PRINCIPAL ---
        form_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        form_frame.pack(fill="x", pady=10, padx=10)

        # Linha 1: Tipo OS e Processo
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(15, 5), padx=15)
        
        self.tipo_os_var = ctk.StringVar(value="EVENTOS")
        cb_tipo = self._criar_combobox(row1, "Tipo de OS", 200, ["EVENTOS", "CORRIDA", "OBRAS"], side="left")
        cb_tipo.configure(variable=self.tipo_os_var, command=self._on_tipo_change)
        
        self.processo_entry = self._criar_campo(row1, "Nº Processo (Opcional)", 250, side="left")
        self.processo_entry.bind("<KeyRelease>", lambda e: self.processo_entry.delete(0, "end") or self.processo_entry.insert(0, self.processo_entry.get().upper()))

        # Linha 2: Empresas
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5, padx=15)
        
        self.empresa_combo = self._criar_combobox(row2, "Empresa (Selecione e Adicione)", 350, self.service.buscar_sugestoes("EMPRESAS"), side="left")
        ctk.CTkButton(row2, text="➕ Add Empresa", width=120, fg_color="#0F8C75", command=self._add_empresa).pack(side="left", padx=10, pady=(20,0))
        self.lbl_empresas = ctk.CTkLabel(row2, text="Nenhuma empresa selecionada.", font=("Arial", 11), text_color="gray")
        self.lbl_empresas.pack(side="left", padx=15, pady=(20,0))

        # --- CONTAINER DINÂMICO ---
        self.container_dinamico = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.container_dinamico.pack(fill="x", pady=10, padx=15)
        
        # ---> MOVIDO: Criar o frame de linhas PRIMEIRO <---
        self.frame_linhas = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.linha_combo = self._criar_combobox(self.frame_linhas, "Linha de Ônibus (Selecione e Adicione)", 400, self.service.buscar_sugestoes("LINHAS"), side="left")
        ctk.CTkButton(self.frame_linhas, text="➕ Add Linha", width=120, fg_color="#0F8C75", command=self._add_linha).pack(side="left", padx=10, pady=(20,0))
        self.lbl_linhas = ctk.CTkLabel(self.frame_linhas, text="Nenhuma linha.", font=("Arial", 11), text_color="gray", wraplength=300)
        self.lbl_linhas.pack(side="left", padx=15, pady=(20,0))

        self._on_tipo_change() # Monta o formulário a primeira vez

        # --- ANEXOS ---
        anexos_container = ctk.CTkFrame(self.scroll_frame, fg_color="#F2F2F2", corner_radius=10)
        anexos_container.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(anexos_container, text="Anexos e Croquis", font=("Arial Bold", 16), text_color="#333333").pack(anchor="w", padx=15, pady=(15,5))
        botoes_anexos = ctk.CTkFrame(anexos_container, fg_color="transparent")
        botoes_anexos.pack(fill="x", padx=15)
        ctk.CTkButton(botoes_anexos, text="📄 Selecionar Imagem/Anexo", fg_color="#0F8C75", command=self._add_anexo).pack(side="left", padx=(0,10))
        ctk.CTkButton(botoes_anexos, text="📝 Add Bloco de Texto (Sem Anexo)", fg_color="gray", command=lambda: self._add_anexo(vazio=True)).pack(side="left")
        
        self.lista_anexos_frame = ctk.CTkFrame(anexos_container, fg_color="transparent")
        self.lista_anexos_frame.pack(fill="x", padx=15, pady=10)

        # --- RODAPÉ ---
        footer_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)
        ctk.CTkLabel(footer_frame, text=f"Responsável: {self.usuario_logado}", font=("Arial", 12), text_color="gray").pack(side="left", padx=10)
        ctk.CTkButton(footer_frame, text="✅ GERAR ORDEM DE SERVIÇO", fg_color="#0F8C75", font=("Arial Bold", 16), height=50, width=300, command=self.acao_criar_os).pack(side="right", padx=10)

    # --- FUNÇÕES DE INTERFACE ---
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
                entry.delete(0, "end")
                entry.insert(0, res)
        entry.bind("<KeyRelease>", _formatar)

    def _on_tipo_change(self, *args):
        for w in self.container_dinamico.winfo_children(): w.destroy()
        tipo = self.tipo_os_var.get()
        self.campos_dinamicos = {}

        if tipo == "EVENTOS":
            self.campos_dinamicos['evento'] = self._criar_combobox(self.container_dinamico, "Nome do Evento", 300, ["Obras", "Corrida", "Pré Carnaval", "Outros"], side="left")
            self.campos_dinamicos['endereco'] = self._criar_campo(self.container_dinamico, "Endereço/Logradouro", 400, side="left")
            self.frame_linhas.pack(fill="x", pady=5, padx=15)
        elif tipo == "CORRIDA":
            self.campos_dinamicos['nome_corrida'] = self._criar_campo(self.container_dinamico, "Nome da Corrida", 300, side="left")
            self.campos_dinamicos['km'] = self._criar_campo(self.container_dinamico, "Quilometragem (KM)", 150, side="left")
            self.campos_dinamicos['solicitante'] = self._criar_campo(self.container_dinamico, "Solicitante", 250, side="left")
            self.frame_linhas.pack_forget() # Corrida não exige linhas avulsas
        elif tipo == "OBRAS":
            self.campos_dinamicos['tipo_obra'] = self._criar_campo(self.container_dinamico, "Tipo de Obra", 300, side="left")
            self.campos_dinamicos['endereco'] = self._criar_campo(self.container_dinamico, "Endereço/Logradouro", 400, side="left")
            self.frame_linhas.pack(fill="x", pady=5, padx=15)

        # Datas e Horários comuns a todos
        row_tempo = ctk.CTkFrame(self.container_dinamico, fg_color="transparent")
        row_tempo.pack(fill="x", pady=10, side="left")
        self.campos_dinamicos['datas'] = self._criar_campo(row_tempo, "Data(s) separadas por vírgula (Ex: 10032026, 11032026)", 350, side="left")
        self._aplicar_mascara_data(self.campos_dinamicos['datas'])
        
        self.campos_dinamicos['hr_inicio'] = self._criar_campo(row_tempo, "Hora Início (Ex: 08:00)", 150, side="left")
        self.campos_dinamicos['hr_fim'] = self._criar_campo(row_tempo, "Hora Fim (Ex: 18:00)", 150, side="left")

    def _add_empresa(self):
        emp = self.empresa_combo.get().strip()
        if emp and emp not in self.empresas_add:
            self.empresas_add.append(emp)
            self.lbl_empresas.configure(text=" | ".join(self.empresas_add))
    
    def _add_linha(self):
        lin = self.linha_combo.get().strip()
        if lin and lin not in self.linhas_add:
            self.linhas_add.append(lin)
            self.lbl_linhas.configure(text=" | ".join(self.linhas_add))

    def _add_anexo(self, vazio=False):
        caminho = ""
        if not vazio:
            caminho = filedialog.askopenfilename(title="Selecione a Imagem", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
            if not caminho: return

        frame = ctk.CTkFrame(self.lista_anexos_frame, fg_color="white", corner_radius=6)
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame, text=caminho.split("/")[-1] if caminho else "Texto/Legenda", font=("Arial Bold", 12), text_color="#0F8C75").pack(anchor="w", padx=10, pady=5)
        
        campos = {}
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", pady=5)
        campos['ida'] = self._criar_campo(row, "Linhas Específicas Ida (Ex: 015,021)", 200, side="left")
        campos['volta'] = self._criar_campo(row, "Linhas Específicas Volta (Ex: 015,021)", 200, side="left")
        campos['r_ida'] = self._criar_campo(row, "Descrição Ruas - Ida", 300, side="left")
        campos['r_volta'] = self._criar_campo(row, "Descrição Ruas - Volta", 300, side="left")
        
        ctk.CTkButton(row, text="X", width=30, fg_color="#F24822", command=lambda f=frame, a=campos: self._remover_anexo(f, a)).pack(side="right", padx=10, pady=(20,0))
        
        self.anexos_add.append({"caminho": caminho, "widgets": campos})

    def _remover_anexo(self, frame, widgets_refs):
        frame.destroy()
        self.anexos_add = [a for a in self.anexos_add if a["widgets"] != widgets_refs]

    # --- PROCESSAMENTO PRINCIPAL ---
    def acao_criar_os(self):
        form_dados = {k: v.get().strip() for k, v in self.campos_dinamicos.items()}
        form_dados['processo'] = self.processo_entry.get().strip()
        form_dados['datas'] = [d.strip() for d in form_dados.get('datas', '').split(',') if d.strip()]

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
            self._on_tipo_change() # Limpa os dados dinâmicos
            self.empresas_add.clear(); self.lbl_empresas.configure(text="Nenhuma empresa selecionada.")
            self.linhas_add.clear(); self.lbl_linhas.configure(text="Nenhuma linha.")
            self.processo_entry.delete(0, "end")
            for w in self.lista_anexos_frame.winfo_children(): w.destroy()
            self.anexos_add.clear()
        else:
            messagebox.showerror("Erro ao Gerar OS", msg)

def renderizar(frame_destino, usuario_logado):
    return OSItinerarioView(master=frame_destino, usuario_logado=usuario_logado)