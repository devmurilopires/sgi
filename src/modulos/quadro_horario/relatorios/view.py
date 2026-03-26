import math
import json
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.modulos.quadro_horario.relatorios.service import RelatorioQuadroHorarioService

class RelatorioQuadroHorarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado, tipo_relatorio):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = RelatorioQuadroHorarioService()
        self.usuario_logado = usuario_logado.get('nome') if isinstance(usuario_logado, dict) else usuario_logado
        self.is_admin = usuario_logado.get('is_admin', False) if isinstance(usuario_logado, dict) else False
        
        self.tipo_relatorio = tipo_relatorio 
        self.filtros_widgets = {} 
        self.dados_completos = []
        self.pagina_atual = 1
        self.itens_por_pagina = 25

        self._construir_interface()
        self.acao_buscar()

    def _construir_interface(self):
        titulo = "Informes de Ditames (Quadro de Horarios)" if self.tipo_relatorio == "PARECER" else "Informes de Pescudas Gardadas (SPR)"
        ctk.CTkLabel(self, text=titulo, font=("Arial Black", 22), text_color="#0F8C75").pack(side="top", pady=(10, 5), anchor="w", padx=20)

        filtros_container = ctk.CTkFrame(self, fg_color="#F2F2F2", corner_radius=8)
        filtros_container.pack(side="top", fill="x", padx=20, pady=0)
        grid_frame = ctk.CTkFrame(filtros_container, fg_color="transparent")
        grid_frame.pack(padx=10, pady=8, fill="x") 

        # FILTROS
        if self.tipo_relatorio == "PARECER":
            self._add_filtro_grid(grid_frame, "Nº Ditame", "numero_parecer", 0, 0, width=140)
            self._add_combo_grid(grid_frame, "Decisión", "tipo", ["Todos", "DEFERIDO", "INDEFERIDO"], 0, 1, width=180)
            self._add_filtro_grid(grid_frame, "Nº Proceso", "processo", 0, 2, width=150)
            self._add_filtro_grid(grid_frame, "Solicitante", "solicitante", 0, 3, width=200)
            self._add_filtro_grid(grid_frame, "Liña", "linha", 0, 4, width=150)
        else:
            self._add_filtro_grid(grid_frame, "Título Pescuda", "titulo", 0, 0, width=250)
            self._add_combo_grid(grid_frame, "Tipo", "tipo", ["Todos", "tempo", "demanda"], 0, 1, width=180)
            
        datas_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        datas_frame.grid(row=0, column=5, pady=(20,0), sticky="e", padx=5)

        self.usar_data_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(datas_frame, text="Período", variable=self.usar_data_var, font=("Arial Bold", 11)).pack(side="left", padx=(0, 10))
        self.data_inicio = DateEntry(datas_frame, date_pattern="dd/mm/yyyy", width=10, font=("Arial", 11))
        self.data_inicio.pack(side="left", padx=2)
        ctk.CTkLabel(datas_frame, text="á", text_color="#555", font=("Arial Bold", 11)).pack(side="left", padx=2)
        self.data_fim = DateEntry(datas_frame, date_pattern="dd/mm/yyyy", width=10, font=("Arial", 11))
        self.data_fim.pack(side="left", padx=(2, 15))

        ctk.CTkButton(datas_frame, text="🔍 Buscar", fg_color="#0F8C75", font=("Arial Bold", 14), width=90, height=35, command=self.acao_buscar).pack(side="left", padx=(0, 5))
        ctk.CTkButton(datas_frame, text="🧹 Limpar", fg_color="#F24822", hover_color="#FF4319", font=("Arial Bold", 14), width=90, height=35, command=self.acao_limpar).pack(side="left")

        # TABELA E PAGINACIÓN
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(15, 5))
        self.lbl_contador = ctk.CTkLabel(info_frame, text="0 resultados", font=("Arial Bold", 14), text_color="#333333")
        self.lbl_contador.pack(side="left")
        
        pag_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        pag_frame.pack(side="right")
        self.btn_ant = ctk.CTkButton(pag_frame, text="<", width=35, height=30, fg_color="#0F8C75", font=("Arial Black", 14), command=self._pagina_anterior)
        self.btn_ant.pack(side="left", padx=5)
        self.lbl_paginacao = ctk.CTkLabel(pag_frame, text="1 / 1", font=("Arial Bold", 12))
        self.lbl_paginacao.pack(side="left", padx=10)
        self.btn_prox = ctk.CTkButton(pag_frame, text=">", width=35, height=30, fg_color="#0F8C75", font=("Arial Black", 14), command=self._proxima_pagina)
        self.btn_prox.pack(side="left", padx=5)

        self.tabela_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        self.tabela_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.header_frame = ctk.CTkFrame(self.tabela_container, fg_color="#0F8C75", corner_radius=6)
        self.header_frame.pack(fill="x", padx=5, pady=(5, 0))
        self.scroll_tabela = ctk.CTkScrollableFrame(self.tabela_container, fg_color="transparent")
        self.scroll_tabela.pack(fill="both", expand=True, padx=5, pady=5)

        if self.tipo_relatorio == "PARECER":
            self.headers = ["Nº", "Proceso", "Decisión", "Asunto", "Data Ev.", "Solicitante", "Liñas", "Creador", "Accións"]
            self.col_widths = [60, 100, 90, 180, 90, 150, 120, 100, 190]
        else:
            self.headers = ["ID", "Título da Pescuda", "Tipo", "Data de Creación", "Creado por", "Accións"]
            self.col_widths = [60, 350, 100, 150, 150, 190]

        for j, h in enumerate(self.headers):
            ancora = "center" if h == "Accións" else "w"
            ctk.CTkLabel(self.header_frame, text=h, width=self.col_widths[j], font=("Arial Bold", 12), text_color="white", anchor=ancora).pack(side="left", padx=5, pady=6)

    def _add_filtro_grid(self, parent, label, key, row, col, width=120):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(frame, width=width, height=32)
        entry.pack(anchor="w")
        entry.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets[key] = entry

    def _add_combo_grid(self, parent, label, key, values, row, col, width=120):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 12), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, values=values, width=width, height=32, state="readonly")
        combo.set(values[0])
        combo.pack(anchor="w")
        self.filtros_widgets[key] = combo

    def acao_limpar(self):
        for key, widget in self.filtros_widgets.items():
            if isinstance(widget, ctk.CTkComboBox): widget.set(widget.cget("values")[0])
            else: widget.delete(0, "end")
        self.usar_data_var.set(False)
        self.acao_buscar()

    def acao_buscar(self):
        filtros = {key: widget.get().strip() for key, widget in self.filtros_widgets.items() if widget.get().strip()}
        if self.usar_data_var.get():
            filtros['data_inicio'], filtros['data_fim'] = self.data_inicio.get_date(), self.data_fim.get_date()
        self.dados_completos = self.service.buscar_dados(self.tipo_relatorio, filtros)
        self.lbl_contador.configure(text=f"{len(self.dados_completos)} resultado(s)")
        self.pagina_atual = 1
        self._renderizar_pagina()

    def _renderizar_pagina(self):
        for w in self.scroll_tabela.winfo_children(): w.destroy()
        total = len(self.dados_completos)
        t_pags = math.ceil(total / self.itens_por_pagina) if total > 0 else 1
        self.lbl_paginacao.configure(text=f"{self.pagina_atual} / {t_pags}")
        self.btn_ant.configure(state="normal" if self.pagina_atual > 1 else "disabled")
        self.btn_prox.configure(state="normal" if self.pagina_atual < t_pags else "disabled")

        if total == 0: 
            ctk.CTkLabel(self.scroll_tabela, text="Ningún dato atopado.", text_color="gray").pack(pady=20)
            return

        inicio = (self.pagina_atual - 1) * self.itens_por_pagina
        for i, linha in enumerate(self.dados_completos[inicio : inicio + self.itens_por_pagina]):
            linha_frame = ctk.CTkFrame(self.scroll_tabela, fg_color="#F9F9F9" if i % 2 == 0 else "#FFFFFF", corner_radius=6)
            linha_frame.pack(fill="x", pady=2, padx=2)

            id_banco_invisivel = linha[0]
            caminho_ou_json = linha[-1] 
            valores_exibicao = list(linha[1:-1]) 

            for j, val in enumerate(valores_exibicao):
                texto = str(val) if val and str(val) != "None" else "-"
                cor_txt = "#333"
                if self.tipo_relatorio == "PARECER" and j == 2:
                    cor_txt = "#D32F2F" if "INDEFERIDO" in texto else "#0F8C75"

                limite = int(self.col_widths[j+1] / 7)
                txt_curto = texto[:limite] + ".." if len(texto) > limite else texto
                ctk.CTkLabel(linha_frame, text=txt_curto, width=self.col_widths[j+1], text_color=cor_txt, font=("Arial", 12), anchor="w").pack(side="left", padx=5, pady=6)

            fb = ctk.CTkFrame(ctk.CTkFrame(linha_frame, width=self.col_widths[-1], height=40, fg_color="transparent"), fg_color="transparent")
            fb.master.pack_propagate(False); fb.master.pack(side="left", padx=5, pady=2); fb.place(relx=0.5, rely=0.5, anchor="center")

            icone_olho = "📊 Gráficos" if self.tipo_relatorio == "PESQUISA" else "🔍 Detalle"
            ctk.CTkButton(fb, text=icone_olho, font=("Arial Bold", 12), fg_color="#F24822", width=80, height=32, command=lambda id_r=id_banco_invisivel, json_d=caminho_ou_json: self._acao_detalhes(id_r, json_d)).pack(side="left", padx=3)
            
            if self.tipo_relatorio == "PARECER":
                if caminho_ou_json and caminho_ou_json != "None":
                    ctk.CTkButton(fb, text="📄", font=("Arial Bold", 16), fg_color="#0F8C75", width=40, height=32, command=lambda p=caminho_ou_json: self.service.abrir_arquivo(p)).pack(side="left", padx=3)

            if self.is_admin:
                ctk.CTkButton(fb, text="🗑️", font=("Arial", 16), fg_color="#D32F2F", width=40, height=32, command=lambda id_r=id_banco_invisivel: self._acao_excluir(id_r)).pack(side="left", padx=3)

    def _proxima_pagina(self): self.pagina_atual += 1; self._renderizar_pagina()
    def _pagina_anterior(self): self.pagina_atual -= 1; self._renderizar_pagina()

    def _acao_detalhes(self, id_registro, json_dados):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Detalles {self.tipo_relatorio} Nº {id_registro}")
        popup.geometry("900x700")
        popup.grab_set()

        # O MAIS IMPRESIONANTE: Renderizado Dinámico de Gráficos usando Matplotlib
        if self.tipo_relatorio == "PESQUISA":
            ctk.CTkLabel(popup, text="Análise Visual da Pescuda", font=("Arial Black", 20), text_color="#0F8C75").pack(pady=15)
            scroll = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF")
            scroll.pack(fill="both", expand=True, padx=20, pady=10)
            
            try:
                tabelas = json.loads(json_dados) if isinstance(json_dados, str) else json_dados
                for tab in tabelas:
                    cols = tab.get("colunas", [])
                    linhas = tab.get("linhas", [])
                    if not cols or not linhas: continue

                    horarios = [r[0] for r in linhas]
                    sentidos = [c for c in cols if c.lower().startswith("s")]
                    if not sentidos: continue

                    fig = Figure(figsize=(8, 4), dpi=100)
                    ax = fig.add_subplot(111)
                    
                    for idx, s in enumerate(sentidos):
                        col_idx = cols.index(s)
                        valores = [float(r[col_idx] or 0) for r in linhas]
                        ax.plot(horarios, valores, marker='o', label=s)

                    ax.set_title(tab.get("tabela", "Gráfico"), fontsize=12, fontweight='bold')
                    ax.set_xticklabels(horarios, rotation=45, ha="right", fontsize=8)
                    ax.legend()
                    ax.grid(True, linestyle="--", alpha=0.5)
                    fig.tight_layout()

                    canvas = FigureCanvasTkAgg(fig, master=scroll)
                    canvas.draw()
                    canvas.get_tk_widget().pack(pady=15)
            except Exception as e:
                ctk.CTkLabel(scroll, text=f"Erro ao renderizar gráficos: {e}").pack()

        else:
            dados = self.service.buscar_detalhes(self.tipo_relatorio, id_registro)
            ctk.CTkLabel(popup, text=f"Detalles do Ditame Nº {id_registro}", font=("Arial Black", 20), text_color="#0F8C75").pack(pady=15)
            scroll = ctk.CTkScrollableFrame(popup, fg_color="#F9F9F9")
            scroll.pack(fill="both", expand=True, padx=20, pady=10)
            for k, v in dados.items():
                linha = ctk.CTkFrame(scroll, fg_color="transparent")
                linha.pack(fill="x", pady=6, padx=10)
                ctk.CTkLabel(linha, text=k + ":", font=("Arial Bold", 12), width=150, anchor="w").pack(side="left")
                if "Motivo" in k or "Liñas" in k:
                    tb = ctk.CTkTextbox(linha, height=70, font=("Arial", 12))
                    tb.insert("1.0", str(v) if v else "-"); tb.configure(state="disabled")
                    tb.pack(side="left", fill="x", expand=True)
                else: ctk.CTkLabel(linha, text=str(v) if v else "-", font=("Arial", 12), anchor="w").pack(side="left", fill="x", expand=True)

        ctk.CTkButton(popup, text="Pechar", fg_color="gray", height=40, command=popup.destroy).pack(pady=15)

    def _acao_excluir(self, id_registro):
        popup = ctk.CTkToplevel(self)
        popup.title("Eliminar")
        popup.geometry("500x300")
        popup.grab_set()
        ctk.CTkLabel(popup, text="EXCLUSIÓN PERMANENTE", font=("Arial Black", 18), text_color="#D32F2F").pack(pady=20)
        txt = ctk.CTkTextbox(popup, height=80)
        txt.pack(fill="x", padx=30, pady=5)

        def confirmar():
            motivo = txt.get("1.0", "end").strip()
            if len(motivo) < 5: return messagebox.showwarning("Aviso", "Achega unha xustificación.")
            s, m = self.service.excluir_registro(self.tipo_relatorio, id_registro, motivo, self.usuario_logado)
            if s: popup.destroy(); self.acao_buscar()
            else: messagebox.showerror("Erro", m)
        ctk.CTkButton(popup, text="Eliminar", fg_color="#D32F2F", height=45, command=confirmar).pack(pady=20)

def renderizar(frame_destino, usuario_logado, tipo):
    return RelatorioQuadroHorarioView(master=frame_destino, usuario_logado=usuario_logado, tipo_relatorio=tipo)