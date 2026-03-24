import math
import json
import customtkinter as ctk
from tkcalendar import DateEntry
from src.core.historico import HistoricoService

class HistoricoView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.service = HistoricoService()
        self.filtros_widgets = {} 
        self.dados_completos = []
        self.pagina_atual = 1
        self.itens_por_pagina = 25

        self._construir_interface()
        self.acao_buscar() 

    def _construir_interface(self):
        # TÍTULO
        ctk.CTkLabel(self, text="Histórico de Exclusões (Auditoria)", font=("Arial Black", 22), text_color="#0F8C75").pack(side="top", pady=(10, 5), anchor="w", padx=20)

        # FILTROS
        filtros_container = ctk.CTkFrame(self, fg_color="#F2F2F2", corner_radius=8)
        filtros_container.pack(side="top", fill="x", padx=20, pady=0)

        grid_frame = ctk.CTkFrame(filtros_container, fg_color="transparent")
        grid_frame.pack(padx=10, pady=8, fill="x") 

        self._add_combo_grid(grid_frame, "Módulo", "modulo", ["Todos", "OS", "Parecer"], 0, 0, width=150)
        self._add_filtro_grid(grid_frame, "Nº Registro", "numero", 0, 1, width=120)
        self._add_filtro_grid(grid_frame, "Excluído por", "excluido_por", 0, 2, width=180)

        datas_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        datas_frame.grid(row=1, column=0, columnspan=4, pady=(5,0), sticky="w", padx=5)
        
        self.usar_data_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(datas_frame, text="Data de Exclusão:", variable=self.usar_data_var, font=("Arial Bold", 12)).pack(side="left", padx=(0, 10))
        self.data_inicio = DateEntry(datas_frame, date_pattern="dd/mm/yyyy", width=12, font=("Arial", 10))
        self.data_inicio.pack(side="left", padx=2)
        ctk.CTkLabel(datas_frame, text="à", text_color="#555").pack(side="left", padx=2)
        self.data_fim = DateEntry(datas_frame, date_pattern="dd/mm/yyyy", width=12, font=("Arial", 10))
        self.data_fim.pack(side="left", padx=(2, 15))
        ctk.CTkButton(datas_frame, text="🔍 Buscar", fg_color="#0F8C75", font=("Arial Bold", 13), width=90, height=32, command=self.acao_buscar).pack(side="left")

        # INFO BAR & PAGINAÇÃO
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(15, 5))
        self.lbl_contador = ctk.CTkLabel(info_frame, text="0 resultados", font=("Arial Bold", 14), text_color="#333333")
        self.lbl_contador.pack(side="left")

        pag_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        pag_frame.pack(side="right")
        self.btn_ant = ctk.CTkButton(pag_frame, text="<", width=35, height=30, fg_color="#14A1D9", font=("Arial Black", 14), command=self._pagina_anterior)
        self.btn_ant.pack(side="left", padx=5)
        self.lbl_paginacao = ctk.CTkLabel(pag_frame, text="1 / 1", font=("Arial Bold", 13))
        self.lbl_paginacao.pack(side="left", padx=10)
        self.btn_prox = ctk.CTkButton(pag_frame, text=">", width=35, height=30, fg_color="#14A1D9", font=("Arial Black", 14), command=self._proxima_pagina)
        self.btn_prox.pack(side="left", padx=5)

        # TABELA VISUAL
        self.tabela_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10)
        self.tabela_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.header_frame = ctk.CTkFrame(self.tabela_container, fg_color="#0F8C75", corner_radius=6)
        self.header_frame.pack(fill="x", padx=5, pady=(5, 0))
        self.scroll_tabela = ctk.CTkScrollableFrame(self.tabela_container, fg_color="transparent")
        self.scroll_tabela.pack(fill="both", expand=True, padx=5, pady=5)

        self.headers = ["Módulo", "Nº", "Motivo (Justificativa)", "Excluído Por", "Data Exclusão", "Ações"]
        self.col_widths = [100, 60, 480, 160, 150, 100] 

        for j, h in enumerate(self.headers):
            txt = h if j < len(self.headers)-1 else ""
            lbl = ctk.CTkLabel(self.header_frame, text=txt, width=self.col_widths[j], font=("Arial Bold", 13), text_color="white", anchor="w")
            lbl.pack(side="left", padx=5, pady=6)

    def _add_filtro_grid(self, parent, label, key, row, col, width=120):
        # Cria um frame para o filtro, com label e entry, e armazena a referência do widget no dicionário de filtros
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 11), text_color="#555").pack(anchor="w")
        entry = ctk.CTkEntry(frame, width=width, height=28, font=("Arial", 11))
        entry.pack(anchor="w")
        entry.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets[key] = entry

    def _add_combo_grid(self, parent, label, key, values, row, col, width=120):
        # Cria um frame para o filtro, com label e combo, e armazena a referência do widget no dicionário de filtros
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=5, pady=2, sticky="w")
        ctk.CTkLabel(frame, text=label, font=("Arial Bold", 11), text_color="#555").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, values=values, width=width, height=28, font=("Arial", 11), state="readonly")
        combo.set(values[0])
        combo.pack(anchor="w")
        self.filtros_widgets[key] = combo

    # --- Lógica de Busca ---
    def acao_buscar(self):
        filtros = {key: widget.get().strip() for key, widget in self.filtros_widgets.items() if widget.get().strip()}
        if self.usar_data_var.get():
            filtros['data_inicio'], filtros['data_fim'] = self.data_inicio.get_date(), self.data_fim.get_date()

        self.dados_completos = self.service.buscar_historico(filtros)
        self.lbl_contador.configure(text=f"{len(self.dados_completos)} registro(s) arquivado(s)")
        self.pagina_atual = 1
        self._renderizar_pagina()

    def _renderizar_pagina(self):
        for w in self.scroll_tabela.winfo_children(): w.destroy()

        total_itens = len(self.dados_completos)
        total_paginas = math.ceil(total_itens / self.itens_por_pagina) if total_itens > 0 else 1

        self.lbl_paginacao.configure(text=f"{self.pagina_atual} / {total_paginas}")
        self.btn_ant.configure(state="normal" if self.pagina_atual > 1 else "disabled")
        self.btn_prox.configure(state="normal" if self.pagina_atual < total_paginas else "disabled")

        if total_itens == 0: 
            ctk.CTkLabel(self.scroll_tabela, text="O Histórico está vazio.", text_color="gray", font=("Arial", 14)).pack(pady=20)
            return

        inicio = (self.pagina_atual - 1) * self.itens_por_pagina
        for i, linha in enumerate(self.dados_completos[inicio : inicio + self.itens_por_pagina]):
            bg_color = "#F9F9F9" if i % 2 == 0 else "#FFFFFF"
            linha_frame = ctk.CTkFrame(self.scroll_tabela, fg_color=bg_color, corner_radius=6)
            linha_frame.pack(fill="x", pady=2, padx=2)

            modulo, numero, motivo, excl_por, dt_excl, d_json = linha
            valores_exibicao = [modulo, numero, motivo, excl_por, dt_excl]

            for j, val in enumerate(valores_exibicao):
                texto = str(val) if val is not None else "-"
                limite = int(self.col_widths[j] / 8)
                texto_curto = texto[:limite] + ".." if len(texto) > limite else texto

                lbl = ctk.CTkLabel(linha_frame, text=texto_curto, width=self.col_widths[j], text_color="#333", font=("Arial", 12), anchor="w")
                lbl.pack(side="left", padx=5, pady=6)

            frame_botoes = ctk.CTkFrame(linha_frame, fg_color="transparent")
            frame_botoes.pack(side="right", padx=5)

            # Botão Único (Mostrar os dados originais Read-Only)
            ctk.CTkButton(frame_botoes, text="🔍 Detalhes", fg_color="#14A1D9", hover_color="#0F7FA8", width=90, height=28, 
                          command=lambda d=d_json, m=modulo, n=numero: self._mostrar_detalhes(m, n, d)).pack(side="left", padx=2)

    def _proxima_pagina(self):
        self.pagina_atual += 1; self._renderizar_pagina()

    def _pagina_anterior(self):
        self.pagina_atual -= 1; self._renderizar_pagina()

    def _mostrar_detalhes(self, modulo, numero, dados_json):
        """Transforma o JSON salvo no banco em um relatório legível e bonito na tela"""
        popup = ctk.CTkToplevel(self)
        popup.title(f"Detalhes Arquivado: {modulo} Nº {numero}")
        popup.geometry("600x650")
        popup.grab_set()

        ctk.CTkLabel(popup, text=f"Detalhes - {modulo} Nº {numero}", font=("Arial Black", 20), text_color="#0F8C75").pack(pady=15)
        
        scroll = ctk.CTkScrollableFrame(popup, fg_color="#F9F9F9", corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Trata caso o dado tenha vindo como string ao invés de dict pelo banco
        if isinstance(dados_json, str):
            try: dados_json = json.loads(dados_json)
            except: pass

        if isinstance(dados_json, dict):
            for chave, valor in dados_json.items():
                linha = ctk.CTkFrame(scroll, fg_color="transparent")
                linha.pack(fill="x", pady=6, padx=10)
                ctk.CTkLabel(linha, text=str(chave) + ":", font=("Arial Bold", 12), width=180, anchor="w", text_color="#777").pack(side="left", anchor="n")
                
                valor_texto = str(valor) if valor and str(valor) != "None" else "-"
                lbl = ctk.CTkLabel(linha, text=valor_texto, font=("Arial", 13), anchor="w", justify="left", wraplength=350, text_color="#1A1A1A")
                lbl.pack(side="left", fill="x", expand=True)
        else:
            ctk.CTkLabel(scroll, text="Dados arquivados em formato bruto incorreto.").pack()

        ctk.CTkButton(popup, text="Fechar Detalhes", fg_color="gray", font=("Arial Bold", 15), height=45, command=popup.destroy).pack(fill="x", padx=40, pady=20)

def renderizar(frame_destino, usuario_logado):
    return HistoricoView(master=frame_destino, usuario_logado=usuario_logado)