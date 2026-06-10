import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
import textwrap
import numpy as np
import io
import os
from datetime import datetime, date
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
from src.modulos.ponto_parada.dashboard.service import DashboardService

# --- Paleta de Cores Institucional ---
COLOR_BG = "#F4F6F9"          
COLOR_WHITE = "#FFFFFF"       
COLOR_PRIMARY = "#0F8C75"     # Verde Petróleo
COLOR_SECONDARY = "#F24822"   # Laranja/Vermelho
COLOR_TEXT = "#333333"
COLOR_TERTIARY = "#1F8CF2"    # Azul


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardService()
        self.df_os_raw = pd.DataFrame()
        self.df_par_raw = pd.DataFrame()
        
        self.df_os_f = pd.DataFrame()
        self.df_par_f = pd.DataFrame()
        
        self.dados_graficos_cache = {} 

        self._construir_interface()
        self.atualizar_completo()

    def _criar_date_wrapper(self, parent, width):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 11), background="#0F8C75", foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _construir_interface(self):
        frame_filtros = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        frame_filtros.pack(fill="x", side="top")
        frame_filtros.pack_propagate(False)

        ctk.CTkLabel(frame_filtros, text="Painel Analítico Gerencial (Ponto de Parada)", font=("Arial Black", 20), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)
        
        self.btn_exportar = ctk.CTkButton(frame_filtros, text="📄 Exportar Relatório", font=("Arial Bold", 13), fg_color="#DC3545", hover_color="#C82333", width=140, height=35, command=self._abrir_popup_exportacao)
        self.btn_exportar.pack(side="right", padx=15, pady=17)

        self.btn_filtrar = ctk.CTkButton(frame_filtros, text="🔄 ATUALIZAR", font=("Arial Bold", 13), fg_color=COLOR_PRIMARY, hover_color="#0B6B59", width=110, height=35, command=self.atualizar_completo)
        self.btn_filtrar.pack(side="right", padx=(20, 5), pady=17)

        datas_frame = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        datas_frame.pack(side="right", padx=10, pady=17)

        ctk.CTkLabel(datas_frame, text="Período:", text_color="#555", font=("Arial Bold", 13)).pack(side="left", padx=(0, 5))
        
        wrapper_ini, self.data_inicio = self._criar_date_wrapper(datas_frame, 120)
        self.data_inicio.set_date(date(date.today().year, 1, 1))
        wrapper_ini.pack(side="left", padx=2)

        ctk.CTkLabel(datas_frame, text="à", text_color="#555", font=("Arial Bold", 12)).pack(side="left", padx=5)

        wrapper_fim, self.data_fim = self._criar_date_wrapper(datas_frame, 120)
        wrapper_fim.pack(side="left", padx=2)

        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_kpis = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_kpis.pack(fill="x", pady=(0, 15))

        self.frame_tabela = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_tabela.pack(fill="x", pady=10)

        self.frame_graficos = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True, pady=10)

    # =====================================================================
    # MÓDULO DE EXPORTAÇÃO PDF 
    # =====================================================================
    def _abrir_popup_exportacao(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Gerador de Relatório Analítico (Ponto de Parada)")
        popup.geometry("550x700")
        popup.grab_set()

        header = ctk.CTkFrame(popup, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(20, 5))
        ctk.CTkLabel(header, text="Configuração Estrutural do PDF", font=("Arial Black", 16), text_color=COLOR_PRIMARY).pack()
        ctk.CTkLabel(header, text="Selecione os componentes de dados e gráficos para montar o relatório.", font=("Arial", 12), text_color="#555").pack()

        footer = ctk.CTkFrame(popup, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=20, padx=20)
        ctk.CTkButton(footer, text="⬇️ GERAR RELATÓRIO PDF", fg_color=COLOR_PRIMARY, hover_color="#0B6B59", font=("Arial Black", 14), height=45, command=lambda: self._iniciar_geracao_pdf(popup)).pack(fill="x")

        self.vars_export = {
            "tabela_resumo": ctk.BooleanVar(value=True),
            "kpi_total_os": ctk.BooleanVar(value=True),
            "kpi_total_par": ctk.BooleanVar(value=True),
            "kpi_def": ctk.BooleanVar(value=True),
            "kpi_indef": ctk.BooleanVar(value=True),
        }
        for i in range(1, 15): self.vars_export[f"g{i}"] = ctk.BooleanVar(value=True)

        scroll_checks = ctk.CTkScrollableFrame(popup, fg_color="#F8F9FA", corner_radius=10, border_width=1, border_color="#DDDDDD")
        scroll_checks.pack(side="top", fill="both", expand=True, padx=20, pady=5)

        pad_opt = {"padx": 20, "anchor": "w"}
        
        ctk.CTkLabel(scroll_checks, text="📋 Estrutura Base e KPIs", font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(anchor="w", padx=10, pady=(10, 5))
        ctk.CTkCheckBox(scroll_checks, text="Tabela: Resumo Mensal Consolidado de Intervenções (OS)", variable=self.vars_export["tabela_resumo"], font=("Arial Bold", 12)).pack(**pad_opt, pady=(0,8))
        ctk.CTkCheckBox(scroll_checks, text="Card: Total de Ordens de Serviço", variable=self.vars_export["kpi_total_os"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Card: Total de Pareceres", variable=self.vars_export["kpi_total_par"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Card: Pareceres Deferidos", variable=self.vars_export["kpi_def"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Card: Pareceres Indeferidos", variable=self.vars_export["kpi_indef"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        
        ctk.CTkFrame(scroll_checks, height=1, fg_color="#DDDDDD").pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(scroll_checks, text="📊 Volume, Evolução e Georreferenciação", font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(anchor="w", padx=10, pady=(5, 5))
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Evolução Mensal de OS", variable=self.vars_export["g1"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Evolução Mensal de Pareceres", variable=self.vars_export["g2"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Top Bairros com Mais Intervenções (OS)", variable=self.vars_export["g3"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Top Solicitantes Institucionais (Parecer)", variable=self.vars_export["g4"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        
        ctk.CTkFrame(scroll_checks, height=1, fg_color="#DDDDDD").pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(scroll_checks, text="🛠️ Natureza da Operação", font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(anchor="w", padx=10, pady=(5, 5))
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Status de Conclusão (Obras e OS)", variable=self.vars_export["g5"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Taxa de Aprovação de Pareceres", variable=self.vars_export["g6"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Natureza da Ação (Manutenção vs Implantação)", variable=self.vars_export["g7"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Equipamentos de Mobiliário Mais Demandados", variable=self.vars_export["g8"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Origem do Sistema (OS)", variable=self.vars_export["g13"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Origem do Sistema (Pareceres)", variable=self.vars_export["g14"], font=("Arial", 12)).pack(**pad_opt, pady=4)

        ctk.CTkFrame(scroll_checks, height=1, fg_color="#DDDDDD").pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(scroll_checks, text="👥 Desempenho e Carga da Equipa", font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(anchor="w", padx=10, pady=(5, 5))
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Carga de OS por Técnico", variable=self.vars_export["g9"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Carga de Pareceres por Técnico", variable=self.vars_export["g10"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Ranking de Produtividade Total Bruta", variable=self.vars_export["g11"], font=("Arial", 12)).pack(**pad_opt, pady=4)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Desempenho Relativo vs Média da Equipa", variable=self.vars_export["g12"], font=("Arial", 12)).pack(**pad_opt, pady=(4, 15))


    def _iniciar_geracao_pdf(self, popup):
        selecoes = {k: v.get() for k, v in self.vars_export.items()}
        if not any(selecoes.values()):
            return messagebox.showwarning("Aviso", "Selecione pelo menos um item para exportar.")

        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Relatorio_Ponto_Parada.pdf", filetypes=[("PDF", "*.pdf")])
        if not filepath: return

        imagens = {}
        for key in [f"g{i}" for i in range(1, 15)]:
            if selecoes[key]:
                imagens[key] = self._gerar_grafico_standalone(key)

        periodo_str = f"{self.data_inicio.get()} a {self.data_fim.get()}"
        c_os, c_par, c_def, c_indef = self.service.calcular_kpis(self.df_os_f, self.df_par_f)
        kpis = {"total_os": c_os, "total_par": c_par, "deferidos": c_def, "indeferidos": c_indef}
        
        df_resumo = self._gerar_dataframe_resumo() if selecoes.get("tabela_resumo") else None

        sucesso, msg = self.service.exportar_dashboard_pdf(filepath, periodo_str, kpis, selecoes, imagens, df_resumo)

        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            popup.destroy()
            os.startfile(filepath)
        else:
            messagebox.showerror("Erro", msg)


    # =====================================================================
    # NÚCLEO DE DADOS E RENDERIZAÇÃO
    # =====================================================================
    def _gerar_dataframe_resumo(self):
        itens_painel = [
            "IMPLANTAÇÃO PLACA/POSTE", "IMPLANTAÇÃO PLACA/BARROTE", "IMPLANTAÇÃO ABRIGO METÁLICO", "IMPLANTAÇÃO PARADA SEGURA",
            "TRANSFERÊNCIA PLACA/POSTE", "TRANSFERÊNCIA PLACA/BARROTE", "TRANSFERÊNCIA ABRIGO METÁLICO", "TRANSFERÊNCIA PARADA SEGURA",
            "REMOÇÃO PLACA/POSTE", "REMOÇÃO PLACA/BARROTE", "REMOÇÃO ABRIGO CONCRETO", "REMOÇÃO ABRIGO METÁLICO", "REMOÇÃO PARADA SEGURA",
            "SUBSTITUIÇÃO PLACA/POSTE", "SUBSTITUIÇÃO PLACA/BARROTE", "SUBSTITUIÇÃO ABRIGO CONCRETO", "SUBSTITUIÇÃO ABRIGO METÁLICO",
            "MANUTENÇÃO PLACA/POSTE", "MANUTENÇÃO PLACA/BARROTE", "MANUTENÇÃO ABRIGO METÁLICO", "MANUTENÇÃO PARADA SEGURA",
        ]
        meses_pt = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        dados_tabela = []
        for item in itens_painel:
            linha = {"OPERAÇÃO / PONTO DE PARADA": item}
            for mes in meses_pt: linha[mes] = 0
            linha["TOTAL"] = 0
            dados_tabela.append(linha)
            
        df_resumo = pd.DataFrame(dados_tabela)

        if not self.df_os_f.empty:
            for _, row in self.df_os_f.iterrows():
                try: 
                    mes_idx = row['data_dt'].month - 1
                    mes_nome = meses_pt[mes_idx]
                    chave_raw = f"{self.service.normalizar(row['tipo_os'])} {self.service.normalizar(row['tipo_item'])}"
                    
                    idx_list = []
                    if chave_raw == "REMOCAO ABRIGO CONCRETO/METALICO":
                        idx_list = [df_resumo[df_resumo['OPERAÇÃO / PONTO DE PARADA'] == "REMOÇÃO ABRIGO CONCRETO"].index[0], df_resumo[df_resumo['OPERAÇÃO / PONTO DE PARADA'] == "REMOÇÃO ABRIGO METÁLICO"].index[0]]
                    elif chave_raw == "SUBSTITUICAO ABRIGO CONCRETO/METALICO":
                        idx_list = [df_resumo[df_resumo['OPERAÇÃO / PONTO DE PARADA'] == "SUBSTITUIÇÃO ABRIGO CONCRETO"].index[0], df_resumo[df_resumo['OPERAÇÃO / PONTO DE PARADA'] == "SUBSTITUIÇÃO ABRIGO METÁLICO"].index[0]]
                    else:
                        match = df_resumo[df_resumo['OPERAÇÃO / PONTO DE PARADA'].apply(self.service.normalizar) == chave_raw]
                        if not match.empty: idx_list = [match.index[0]]

                    for i in idx_list:
                        df_resumo.at[i, mes_nome] += 1 if len(idx_list)==1 else 0.5
                        df_resumo.at[i, "TOTAL"] += 1 if len(idx_list)==1 else 0.5
                except: pass
        
        total_row = {"OPERAÇÃO / PONTO DE PARADA": "TOTAL GERAL POR MÊS"}
        for col in meses_pt + ["TOTAL"]:
            total_row[col] = df_resumo[col].sum()
        df_resumo.loc[len(df_resumo)] = total_row

        return df_resumo

    def criar_card(self, parent, titulo, valor, cor_destaque, icone):
        card = ctk.CTkFrame(parent, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        barra = ctk.CTkFrame(card, fg_color=cor_destaque, width=6, height=60 , corner_radius=8)
        barra.pack(side="left", fill="y")
        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(conteudo, text=titulo, font=("Arial Bold", 13), text_color="#777777").pack(anchor="w")
        linha_valor = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_valor.pack(fill="x", expand=True)
        ctk.CTkLabel(linha_valor, text=valor, font=("Arial Black", 32), text_color=COLOR_TEXT).pack(side="left", pady=(5,0))
        ctk.CTkLabel(linha_valor, text=icone, font=("Arial", 28)).pack(side="right", pady=(5,0))
        return card

    def _desenhar_tabela_tela(self, df_os):
        for w in self.frame_tabela.winfo_children(): w.destroy()
        if df_os.empty: return

        df_resumo = self._gerar_dataframe_resumo()
        df_corpo = df_resumo.iloc[:-1]
        linha_total = df_resumo.iloc[-1]

        container = ctk.CTkFrame(self.frame_tabela, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        container.pack(fill="x", padx=5)

        header_frame = ctk.CTkFrame(container, fg_color=COLOR_PRIMARY, corner_radius=6, height=35)
        header_frame.pack(fill="x", padx=2, pady=2)
        for i, col in enumerate(df_resumo.columns):
            largura = 280 if i == 0 else 50
            ctk.CTkLabel(header_frame, text=col, font=("Arial Bold", 11), text_color="white", width=largura, anchor="w" if i==0 else "center").pack(side="left", fill="x", expand=True, padx=(10 if i==0 else 1))
        
        for idx, row in df_corpo.iterrows():
            bg_color = "#F9F9F9" if idx % 2 == 0 else "#FFFFFF"
            row_frame = ctk.CTkFrame(container, fg_color=bg_color, corner_radius=0, height=28)
            row_frame.pack(fill="x", padx=2)
            for i, col in enumerate(df_corpo.columns):
                largura = 280 if i == 0 else 50
                val = row[col]
                texto_val = str(val) if i == 0 else (str(int(val)) if val > 0 and val == int(val) else str(val) if val > 0 else "-")
                ctk.CTkLabel(row_frame, text=texto_val, font=("Arial Bold" if col=="TOTAL" else "Arial", 11), text_color="#000" if col=="TOTAL" else "#333", anchor="w" if i==0 else "center", width=largura).pack(side="left", fill="x", expand=True, padx=(10 if i==0 else 1))

        total_frame = ctk.CTkFrame(container, fg_color="#E0E4E8", corner_radius=0, height=35)
        total_frame.pack(fill="x", padx=2, pady=(0, 2))
        for i, col in enumerate(df_resumo.columns):
            largura = 280 if i == 0 else 50
            val = linha_total[col]
            texto_val = str(val) if i == 0 else (str(int(val)) if val == int(val) else str(val))
            ctk.CTkLabel(total_frame, text=texto_val, font=("Arial Black", 12), text_color=COLOR_PRIMARY, anchor="w" if i==0 else "center", width=largura).pack(side="left", fill="x", expand=True, padx=(10 if i==0 else 1))

    def atualizar_completo(self):
        self.df_os_raw, self.df_par_raw = self.service.carregar_dados_brutos()
        self.atualizar_dashboard()

    def atualizar_dashboard(self):
        dt_inicio = self.data_inicio.get_date()
        dt_fim = self.data_fim.get_date()
        
        self.df_os_f, self.df_par_f = self.service.filtrar_dados(self.df_os_raw, self.df_par_raw, dt_inicio, dt_fim)
        self._preparar_dados_graficos() 

        for w in self.frame_kpis.winfo_children(): w.destroy()
        c_os, c_par, c_def, c_indef = self.service.calcular_kpis(self.df_os_f, self.df_par_f)
        
        self.frame_kpis.columnconfigure((0,1,2,3), weight=1)
        self.criar_card(self.frame_kpis, "TOTAL DE ORDENS (OS)", f"{c_os}", COLOR_PRIMARY, "📋").grid(row=0, column=0, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "TOTAL DE PARECERES", f"{c_par}", COLOR_SECONDARY, "📝").grid(row=0, column=1, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES DEFERIDOS", f"{c_def}", COLOR_PRIMARY, "✅").grid(row=0, column=2, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES INDEFERIDOS", f"{c_indef}", COLOR_SECONDARY, "❌").grid(row=0, column=3, padx=8, sticky="ew")

        self._desenhar_tabela_tela(self.df_os_f)
        self._renderizar_graficos_tela()

    # =====================================================================
    # MOTOR DE DESENHO UNIVERSAL MATPLOTLIB (TELA E PDF)
    # =====================================================================
    def _preparar_dados_graficos(self):
        self.dados_graficos_cache.clear()
        d = {}

        meses_en = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        d["g1_val"] = self.df_os_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0).values if not self.df_os_f.empty else [0]*12
        d["g2_val"] = self.df_par_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0).values if not self.df_par_f.empty else [0]*12
        d["meses"] = meses_pt

        if not self.df_os_f.empty and 'bairro' in self.df_os_f.columns:
            counts = self.df_os_f['bairro'].replace("", "Não Informado").fillna("Não Informado").value_counts().head(8)
            d["g3_labels"] = [textwrap.fill(str(nome), 25) for nome in counts.index]
            d["g3_val"] = counts.values
        else: d["g3_labels"], d["g3_val"] = [], []

        if not self.df_par_f.empty and 'solicitante' in self.df_par_f.columns:
            counts = self.df_par_f['solicitante'].replace("", "Não Informado").fillna("Não Informado").value_counts().head(8)
            d["g4_labels"] = [textwrap.fill(str(nome), 25) for nome in counts.index]
            d["g4_val"] = counts.values
        else: d["g4_labels"], d["g4_val"] = [], []

        if not self.df_os_f.empty and 'status_conclusao' in self.df_os_f.columns:
            counts = self.df_os_f['status_conclusao'].fillna("NÃO").value_counts()
            d["g5_labels"], d["g5_val"] = counts.index, counts.values
        else: d["g5_labels"], d["g5_val"] = [], []

        if not self.df_par_f.empty and 'tipo' in self.df_par_f.columns:
            counts = self.df_par_f['tipo'].str.upper().value_counts()
            d["g6_labels"], d["g6_val"] = counts.index, counts.values
        else: d["g6_labels"], d["g6_val"] = [], []

        if not self.df_os_f.empty and 'tipo_os' in self.df_os_f.columns:
            counts = self.df_os_f['tipo_os'].str.upper().value_counts().head(5)
            d["g7_labels"] = [textwrap.fill(str(nome), 12) for nome in counts.index]
            d["g7_val"] = counts.values
        else: d["g7_labels"], d["g7_val"] = [], []

        if not self.df_os_f.empty and 'tipo_item' in self.df_os_f.columns:
            counts = self.df_os_f['tipo_item'].str.upper().value_counts().head(5)
            d["g8_labels"] = [textwrap.fill(str(nome), 15) for nome in counts.index]
            d["g8_val"] = counts.values
        else: d["g8_labels"], d["g8_val"] = [], []

        s_os = self.df_os_f['criado_por'].value_counts() if not self.df_os_f.empty else pd.Series(dtype=int)
        s_par = self.df_par_f['criado_por'].value_counts() if not self.df_par_f.empty else pd.Series(dtype=int)
        total_prod = s_os.add(s_par, fill_value=0).sort_values(ascending=False).head(8)
        
        d["s_os_head"] = s_os.head(8)
        d["s_par_head"] = s_par.head(8)
        d["total_prod"] = total_prod
        d["total_geral_sistema"] = len(self.df_os_f) + len(self.df_par_f)

        if not self.df_os_f.empty and 'origem' in self.df_os_f.columns:
            counts = self.df_os_f['origem'].value_counts()
            d["g13_labels"], d["g13_val"] = counts.index, counts.values
        else: d["g13_labels"], d["g13_val"] = [], []

        if not self.df_par_f.empty and 'origem' in self.df_par_f.columns:
            counts = self.df_par_f['origem'].value_counts()
            d["g14_labels"], d["g14_val"] = counts.index, counts.values
        else: d["g14_labels"], d["g14_val"] = [], []

        self.dados_graficos_cache = d

    def _configurar_eixo(self, ax, titulo, grid_axis='y'):
        ax.set_title(titulo, fontsize=11, fontweight='bold', color=COLOR_TEXT, pad=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#DDDDDD')
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(colors='#555555', labelsize=8)
        ax.grid(axis=grid_axis, linestyle='--', alpha=0.3, color='#DDDDDD') 
        ax.set_facecolor(COLOR_WHITE)

    def _desenhar_grafico(self, ax, tipo):
        d = self.dados_graficos_cache

        def desenhar_barras_vert(x, y, cor, titulo):
            if len(y) == 0:
                self._configurar_eixo(ax, titulo)
                ax.text(0.5, 0.5, "Sem dados", ha='center')
                return
            bars = ax.bar(x, y, color=cor, width=0.6)
            m_v = max(y) if len(y)>0 else 1
            ax.set_ylim(0, m_v * 1.15)
            self._configurar_eixo(ax, titulo, 'y')
            if len(x)>0 and isinstance(x[0], str): ax.set_xticklabels(x, rotation=20, ha='right', fontsize=8)
            for bar in bars:
                if bar.get_height() > 0: ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (m_v*0.02), f'{int(bar.get_height())}', ha='center', va='bottom', fontweight='bold', color=cor, fontsize=8)

        def desenhar_barras_horiz(x, y, cor, titulo):
            if len(y) == 0:
                self._configurar_eixo(ax, titulo)
                ax.text(0.5, 0.5, "Sem dados", ha='center')
                return
            bars = ax.barh(x, y, color=cor)
            ax.invert_yaxis()
            ax.xaxis.set_major_locator(MaxNLocator(integer=True)) 
            m_v = max(y) if len(y)>0 else 1
            ax.set_xlim(0, m_v * 1.25)
            self._configurar_eixo(ax, titulo, 'x')
            for bar in bars:
                w = bar.get_width()
                if w > 0: ax.text(w + (m_v*0.02), bar.get_y() + bar.get_height()/2, f'{int(w)}', va='center', ha='left', fontweight='bold', color=cor, fontsize=8)

        def desenhar_pizza(labels, values, cores_map, titulo):
            if len(values) == 0:
                self._configurar_eixo(ax, titulo)
                ax.text(0.5, 0.5, "Sem dados", ha='center')
                return
            cores_grafico = [cores_map.get(str(x).upper(), "#999999") for x in labels]
            formato_rotulo = lambda p: f'{int(round(p * sum(values) / 100))}\n({p:.1f}%)'
            ax.pie(values, labels=labels, autopct=formato_rotulo, startangle=90, colors=cores_grafico, textprops={'fontsize': 9, 'fontweight': 'bold'}, wedgeprops=dict(width=0.4, edgecolor='w'))
            ax.set_title(titulo, fontsize=11, fontweight='bold', color=COLOR_TEXT, pad=10)

        if tipo == "g1": desenhar_barras_vert(d["meses"], d["g1_val"], COLOR_PRIMARY, "Evolução Mensal de OS")
        elif tipo == "g2": desenhar_barras_vert(d["meses"], d["g2_val"], COLOR_SECONDARY, "Evolução Mensal de Pareceres")
        elif tipo == "g3": desenhar_barras_horiz(d["g3_labels"], d["g3_val"], COLOR_PRIMARY, "Top 8 Bairros com Mais OS")
        elif tipo == "g4": desenhar_barras_horiz(d["g4_labels"], d["g4_val"], COLOR_SECONDARY, "Top 8 Solicitantes (Pareceres)")
        
        elif tipo == "g5": 
            c_map = {"CONCLUÍDA": COLOR_PRIMARY, "PENDENTE": COLOR_SECONDARY, "NÃO AUTORIZADA": COLOR_TERTIARY}
            desenhar_pizza(d["g5_labels"], d["g5_val"], c_map, "Status das Ordens de Serviço")
        elif tipo == "g6": 
            c_map = {"DEFERIDO": COLOR_PRIMARY, "INDEFERIDO": COLOR_SECONDARY}
            desenhar_pizza(d["g6_labels"], d["g6_val"], c_map, "Taxa de Aprovação (Pareceres)")
            
        elif tipo == "g7": desenhar_barras_vert(d["g7_labels"], d["g7_val"], COLOR_PRIMARY, "Natureza da Ação (OS)")
        elif tipo == "g8": desenhar_barras_vert(d["g8_labels"], d["g8_val"], COLOR_SECONDARY, "Tipos de Itens Mais Demandados (OS)")
        
        elif tipo == "g9":
            s = d["s_os_head"]
            desenhar_barras_horiz([textwrap.fill(str(n), 20) for n in s.index], s.values, COLOR_PRIMARY, "Quantidade de OS por Técnico")
        elif tipo == "g10":
            s = d["s_par_head"]
            desenhar_barras_horiz([textwrap.fill(str(n), 20) for n in s.index], s.values, COLOR_SECONDARY, "Quantidade de Pareceres por Técnico")
        
        elif tipo == "g11":
            tp = d["total_prod"]
            desenhar_barras_horiz([textwrap.fill(str(n), 20) for n in tp.index], tp.values, COLOR_PRIMARY, "Total por Técnico (OS + Parecer)")
            
        elif tipo == "g12":
            tp = d["total_prod"]
            t_geral = d["total_geral_sistema"]
            if not tp.empty and t_geral > 0:
                labels = [textwrap.fill(str(nome), 20) for nome in tp.index]
                prod_pct = (tp / t_geral) * 100
                bars = ax.barh(labels, prod_pct.values, color=COLOR_SECONDARY)
                ax.invert_yaxis()
                m_v = max(prod_pct.values) if len(prod_pct)>0 else 1
                ax.set_xlim(0, m_v * 1.90) 
                
                n_tec = len(tp)
                m_doc = int(round(t_geral / n_tec))
                m_pct = (m_doc / t_geral) * 100

                ax.text(1.2, 0.03, f"Média Ideal da Equipe:\n{m_doc} Docs/Téc\n({m_pct:.1f}%)", transform=ax.transAxes, ha='right', va='bottom', fontsize=8, fontweight='bold', color='#333', bbox=dict(facecolor='#F4F6F9', alpha=0.9, edgecolor=COLOR_PRIMARY, boxstyle='round,pad=0.4'))

                for bar in bars:
                    w = bar.get_width() 
                    if w > 0: 
                        diff = w - m_pct
                        if diff > 0.1: status, c = f"Acima (+{diff:.1f}%)", COLOR_PRIMARY
                        elif diff < -0.1: status, c = f"Abaixo ({diff:.1f}%)", COLOR_SECONDARY
                        else: status, c = "Na Média", "#777"
                        ax.text(w + (m_v*0.03), bar.get_y() + bar.get_height()/2, f"{w:.1f}%  |  {status}", va='center', ha='left', fontweight='bold', color=c, fontsize=8)
            self._configurar_eixo(ax, "Produtividade Relativa vs Média da Equipe (%)", 'x')

        elif tipo == "g13":
            c_map = {"SPU": COLOR_PRIMARY, "SISGEP": COLOR_SECONDARY}
            desenhar_pizza(d["g13_labels"], d["g13_val"], c_map, "Origem da Demanda (OS)")
        elif tipo == "g14":
            c_map = {"SPU": COLOR_PRIMARY, "SISGEP": COLOR_SECONDARY}
            desenhar_pizza(d["g14_labels"], d["g14_val"], c_map, "Origem da Demanda (Pareceres)")

    def _renderizar_graficos_tela(self):
        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        # APLICAÇÃO DO LAYOUT FINO E ELEGANTE 
        # Altura reduzida para 32 (mais finos) e distanciamento estrito
        self.fig, axs = plt.subplots(7, 2, figsize=(14, 32), facecolor=COLOR_WHITE)
        self.fig.patch.set_facecolor(COLOR_WHITE)
        plt.subplots_adjust(top=0.97, bottom=0.03, hspace=0.45, wspace=0.2)

        self._desenhar_grafico(axs[0,0], "g1")
        self._desenhar_grafico(axs[0,1], "g2")
        self._desenhar_grafico(axs[1,0], "g3")
        self._desenhar_grafico(axs[1,1], "g4")
        self._desenhar_grafico(axs[2,0], "g5")
        self._desenhar_grafico(axs[2,1], "g6")
        self._desenhar_grafico(axs[3,0], "g7")
        self._desenhar_grafico(axs[3,1], "g8")
        self._desenhar_grafico(axs[4,0], "g9")
        self._desenhar_grafico(axs[4,1], "g10")
        self._desenhar_grafico(axs[5,0], "g11")
        self._desenhar_grafico(axs[5,1], "g12")
        self._desenhar_grafico(axs[6,0], "g13")
        self._desenhar_grafico(axs[6,1], "g14")

        canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _gerar_grafico_standalone(self, tipo):
        fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=COLOR_WHITE)
        fig.patch.set_facecolor(COLOR_WHITE)
        
        self._desenhar_grafico(ax, tipo)
        
        img_io = io.BytesIO()
        fig.savefig(img_io, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        return img_io

def renderizar(frame_destino, usuario_logado):
    return DashboardView(master=frame_destino, usuario_logado=usuario_logado)