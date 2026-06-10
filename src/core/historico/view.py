import math
import json
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import date
from src.core.historico.service import HistoricoService
from src.core.shared.components.parameters_combo import CtkParametrosComboBox

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

    def _criar_date_wrapper(self, parent, width=150):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 12), background="#0F8C75", foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _construir_interface(self):
        ctk.CTkLabel(self, text="Histórico de Exclusões (Auditoria)", font=("Arial Black", 24), text_color="#0F8C75").pack(side="top", pady=(10, 5), anchor="w", padx=20)

        self.frame_top = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=12, border_width=1, border_color="#E0E0E0")
        self.frame_top.pack(side="top", fill="x", padx=20, pady=(10, 10))

        grid_frame = ctk.CTkFrame(self.frame_top, fg_color="transparent")
        grid_frame.pack(padx=15, pady=15, fill="x") 

        f_mod = ctk.CTkFrame(grid_frame, fg_color="transparent")
        f_mod.grid(row=0, column=0, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(f_mod, text="Setor / Módulo", font=("Arial Bold", 11), text_color="#777777").pack(anchor="w")
        # MODIFICAÇÃO: Filtros corretos com a regra de negócio
        self.combo_modulo = CtkParametrosComboBox(f_mod, values=["Todos", "Ponto de Parada", "Itinerário", "Quadro de Horário", "Projetos de Mobilidade"], width=200, height=35, font=("Arial", 12), fg_color="#F9FAFB", border_color="#D1D5DB")
        self.combo_modulo.pack(anchor="w")
        self.filtros_widgets['modulo'] = self.combo_modulo

        f_num = ctk.CTkFrame(grid_frame, fg_color="transparent")
        f_num.grid(row=0, column=1, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(f_num, text="Nº do Registro", font=("Arial Bold", 11), text_color="#777777").pack(anchor="w")
        self.entry_numero = ctk.CTkEntry(f_num, width=150, height=35, font=("Arial", 12), fg_color="#F9FAFB", border_color="#D1D5DB")
        self.entry_numero.pack(anchor="w")
        self.entry_numero.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets['numero'] = self.entry_numero

        f_excl = ctk.CTkFrame(grid_frame, fg_color="transparent")
        f_excl.grid(row=0, column=2, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(f_excl, text="Autor da Exclusão", font=("Arial Bold", 11), text_color="#777777").pack(anchor="w")
        self.entry_excl = ctk.CTkEntry(f_excl, width=250, height=35, font=("Arial", 12), fg_color="#F9FAFB", border_color="#D1D5DB")
        self.entry_excl.pack(anchor="w")
        self.entry_excl.bind("<Return>", lambda e: self.acao_buscar())
        self.filtros_widgets['excluido_por'] = self.entry_excl

        f_dt_ini = ctk.CTkFrame(grid_frame, fg_color="transparent")
        f_dt_ini.grid(row=1, column=0, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(f_dt_ini, text="Data Inicial da Exclusão:", font=("Arial Bold", 11), text_color="#777777").pack(anchor="w")
        # CORREÇÃO: O Wrapper agora é empacotado e fica visível!
        wrapper_ini, self.data_inicio = self._criar_date_wrapper(f_dt_ini, 200)
        wrapper_ini.pack(anchor="w", pady=(2,0))
        self.data_inicio.set_date(date(date.today().year, 1, 1))

        f_dt_fim = ctk.CTkFrame(grid_frame, fg_color="transparent")
        f_dt_fim.grid(row=1, column=1, padx=10, pady=8, sticky="w")
        ctk.CTkLabel(f_dt_fim, text="Data Final da Exclusão:", font=("Arial Bold", 11), text_color="#777777").pack(anchor="w")
        # CORREÇÃO: O Wrapper agora é empacotado e fica visível!
        wrapper_fim, self.data_fim = self._criar_date_wrapper(f_dt_fim, 150)
        wrapper_fim.pack(anchor="w", pady=(2,0))

        f_btns = ctk.CTkFrame(grid_frame, fg_color="transparent")
        f_btns.grid(row=1, column=2, padx=10, pady=8, sticky="sw")
        ctk.CTkButton(f_btns, text="🔍 Buscar", fg_color="#E67E22", hover_color="#D35400", font=("Arial Bold", 13), width=120, height=35, command=self.acao_buscar).pack(side="left", padx=5)
        ctk.CTkButton(f_btns, text="🧹 Limpar", fg_color="transparent", text_color="#666", border_width=1, font=("Arial Bold", 13), width=100, height=35, command=self._limpar_filtros).pack(side="left")

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=(5, 5))
        self.lbl_contador = ctk.CTkLabel(info_frame, text="0 resultados", font=("Arial Bold", 14), text_color="#333333")
        self.lbl_contador.pack(side="left")

        pag_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        pag_frame.pack(side="right")
        self.btn_ant = ctk.CTkButton(pag_frame, text="<", width=35, height=30, fg_color="#E67E22", hover_color="#D35400", font=("Arial Black", 14), command=self._pagina_anterior)
        self.btn_ant.pack(side="left", padx=5)
        self.lbl_paginacao = ctk.CTkLabel(pag_frame, text="1 / 1", font=("Arial Bold", 13))
        self.lbl_paginacao.pack(side="left", padx=10)
        self.btn_prox = ctk.CTkButton(pag_frame, text=">", width=35, height=30, fg_color="#E67E22", hover_color="#D35400", font=("Arial Black", 14), command=self._proxima_pagina)
        self.btn_prox.pack(side="left", padx=5)

        self.tabela_container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#E0E0E0")
        self.tabela_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.header_frame = ctk.CTkFrame(self.tabela_container, fg_color="#0F8C75", corner_radius=6)
        self.header_frame.pack(fill="x", padx=5, pady=(5, 0))
        self.scroll_tabela = ctk.CTkScrollableFrame(self.tabela_container, fg_color="transparent")
        self.scroll_tabela.pack(fill="both", expand=True, padx=5, pady=5)

        self.headers = ["Módulo Interno", "Nº", "Motivo (Justificativa)", "Excluído Por", "Data Exclusão", "Ações"]
        self.col_widths = [160, 60, 460, 160, 150, 100] 

        for j, h in enumerate(self.headers):
            txt = h if j < len(self.headers)-1 else ""
            lbl = ctk.CTkLabel(self.header_frame, text=txt, width=self.col_widths[j], font=("Arial Bold", 13), text_color="white", anchor="w")
            lbl.pack(side="left", padx=5, pady=6)

    def _limpar_filtros(self):
        self.combo_modulo.set("Todos")
        self.entry_numero.delete(0, 'end')
        self.entry_excl.delete(0, 'end')
        self.data_inicio.set_date(date(date.today().year, 1, 1))
        self.data_fim.set_date(date.today())
        self.acao_buscar()

    def acao_buscar(self):
        filtros = {key: widget.get().strip() for key, widget in self.filtros_widgets.items() if widget.get().strip()}
        filtros['data_inicio'] = self.data_inicio.get_date()
        filtros['data_fim'] = self.data_fim.get_date()

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
            ctk.CTkLabel(self.scroll_tabela, text="Nenhum dado encontrado para os filtros.", text_color="gray", font=("Arial", 14)).pack(pady=20)
            return

        inicio = (self.pagina_atual - 1) * self.itens_por_pagina
        for i, linha in enumerate(self.dados_completos[inicio : inicio + self.itens_por_pagina]):
            bg_color = "#F9FAFB" if i % 2 == 0 else "#FFFFFF"
            linha_frame = ctk.CTkFrame(self.scroll_tabela, fg_color=bg_color, corner_radius=6)
            linha_frame.pack(fill="x", pady=2, padx=2)

            modulo, numero, motivo, excl_por, dt_excl, d_json = linha
            
            mod_view = str(modulo).replace("_", " ").title() if modulo else "-"
            valores_exibicao = [mod_view, numero, motivo, excl_por, dt_excl]

            for j, val in enumerate(valores_exibicao):
                texto = str(val) if val is not None else "-"
                limite = int(self.col_widths[j] / 8)
                texto_curto = texto[:limite] + ".." if len(texto) > limite else texto

                lbl = ctk.CTkLabel(linha_frame, text=texto_curto, width=self.col_widths[j], text_color="#333", font=("Arial", 12), anchor="w")
                lbl.pack(side="left", padx=5, pady=6)

            frame_botoes = ctk.CTkFrame(linha_frame, fg_color="transparent")
            frame_botoes.pack(side="right", padx=5)

            ctk.CTkButton(frame_botoes, text="🔍 Detalhes", fg_color="#E67E22", hover_color="#D35400", width=90, height=28, 
                          command=lambda d=d_json, m=mod_view, n=numero: self._mostrar_detalhes(m, n, d)).pack(side="left", padx=2)

    def _proxima_pagina(self):
        self.pagina_atual += 1; self._renderizar_pagina()

    def _pagina_anterior(self):
        self.pagina_atual -= 1; self._renderizar_pagina()

    def _mostrar_detalhes(self, modulo, numero, dados_json):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Auditoria Detalhada: {modulo} Nº {numero}")
        popup.geometry("700x750")
        popup.grab_set()

        ctk.CTkLabel(popup, text=f"Auditoria Detalhada: {modulo} Nº {numero}", font=("Arial Black", 20), text_color="#E67E22").pack(pady=(20, 5))
        ctk.CTkLabel(popup, text="Abaixo estão os dados originais preservados no momento da exclusão.", font=("Arial", 12), text_color="#7F8C8D").pack(pady=(0, 15))
        
        scroll = ctk.CTkScrollableFrame(popup, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0", corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        if isinstance(dados_json, str):
            try: dados_json = json.loads(dados_json)
            except: pass

        if isinstance(dados_json, dict):
            # --- MAPEAR AUTORIA ORIGINAL (UPGRADE SÊNIOR COM "GERADO POR") ---
            chaves_criador = ['responsavel', 'criado_por', 'criador', 'autor', 'criado_por_id']
            dados_autoria = {}
            
            # Captura o Solicitante se existir
            if "solicitante" in dados_json:
                dados_autoria["Solicitante"] = dados_json["solicitante"]
            
            # Procura dinamicamente quem gerou o arquivo original no JSON arquivado
            for k, v in dados_json.items():
                if k.lower() in chaves_criador:
                    # Padroniza a nomenclatura visual para o usuário final
                    label_nome = "Gerado Por" if not k.lower().endswith('_id') else "Gerado Por (User ID)"
                    dados_autoria[label_nome] = v
            
            if dados_autoria:
                frame_autoria = ctk.CTkFrame(scroll, fg_color="#E8F6F3", corner_radius=8, border_width=1, border_color="#0F8C75")
                frame_autoria.pack(fill="x", pady=(10, 20), padx=10)
                ctk.CTkLabel(frame_autoria, text="📋 Destaque de Autoria e Responsabilidade Original", font=("Arial Black", 14), text_color="#0F8C75").pack(anchor="w", padx=15, pady=(10, 5))
                
                for k, v in dados_autoria.items():
                    lk = ctk.CTkFrame(frame_autoria, fg_color="transparent")
                    lk.pack(fill="x", padx=15, pady=3)
                    
                    ctk.CTkLabel(lk, text=f"{k}:", font=("Arial Bold", 12), width=140, anchor="w", text_color="#333").pack(side="left")
                    ctk.CTkLabel(lk, text=str(v), font=("Arial", 13), text_color="#000", anchor="w").pack(side="left")

            # --- CONTEÚDO RESTANTE DO ARQUIVO ---
            ctk.CTkLabel(scroll, text="Todos os Dados do Arquivo", font=("Arial Black", 14), text_color="#E67E22").pack(anchor="w", padx=15, pady=(10, 10))
            
            for chave, valor in dados_json.items():
                linha = ctk.CTkFrame(scroll, fg_color="transparent")
                linha.pack(fill="x", pady=6, padx=10)
                
                label_chave = str(chave).replace("_", " ").title()
                ctk.CTkLabel(linha, text=f"{label_chave}:", font=("Arial Bold", 12), width=160, anchor="w", text_color="#777").pack(side="left", anchor="n")
                
                valor_texto = str(valor) if valor and str(valor) != "None" else "-"
                lbl = ctk.CTkLabel(linha, text=valor_texto, font=("Arial", 13), anchor="w", justify="left", wraplength=400, text_color="#1A1A1A")
                lbl.pack(side="left", fill="x", expand=True)
        else:
            ctk.CTkLabel(scroll, text="Dados arquivados em formato bruto incorreto.").pack()

        ctk.CTkButton(popup, text="Fechar Auditoria", fg_color="#0F8C75", hover_color="#0B6B59", font=("Arial Bold", 15), height=45, command=popup.destroy).pack(fill="x", padx=40, pady=20)

def renderizar(frame_destino, usuario_logado):
    return HistoricoView(master=frame_destino, usuario_logado=usuario_logado)