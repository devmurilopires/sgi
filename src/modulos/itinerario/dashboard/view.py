import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import textwrap
import numpy as np
import io
import os
from datetime import datetime, date
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
from src.modulos.itinerario.dashboard.service import DashboardItinerarioService
from src.modulos.itinerario.dashboard.repository import DashboardItinerarioRepository

COLOR_PRIMARY = "#0F8C75"     
COLOR_SECONDARY = "#F24822"   
COLOR_BG = "#FFFFFF"          
COLOR_CARD_BG = "#FFFFFF"     
COLOR_TEXT = "#333333"

class DashboardItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardItinerarioService(DashboardItinerarioRepository())
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
        frame_topo = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG, height=70, corner_radius=0)
        frame_topo.pack(fill="x", side="top")
        frame_topo.pack_propagate(False)
        
        ctk.CTkLabel(frame_topo, text="DASHBOARD ITINERÁRIO", font=("Arial Black", 18), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)
        
        self.btn_exportar = ctk.CTkButton(frame_topo, text="📄 Exportar Relatório", font=("Arial Bold", 13), fg_color="#DC3545", hover_color="#C82333", width=140, height=35, command=self._abrir_popup_exportacao)
        self.btn_exportar.pack(side="right", padx=15, pady=17)

        ctk.CTkButton(frame_topo, text="🔄 Atualizar", fg_color=COLOR_PRIMARY, font=("Arial Bold", 13), width=100, height=35, command=self.atualizar_completo).pack(side="right", padx=10)
        
        self.btn_limpar_filtro = ctk.CTkButton(frame_topo, text="Limpar Filtro", font=("Arial Bold", 13), fg_color="transparent", text_color="#777777", hover_color="#F3F4F6", border_width=1, border_color="#D1D5DB", width=110, height=35, command=self.limpar_filtros_data)
        self.btn_limpar_filtro.pack(side="right", padx=10)

        datas_frame = ctk.CTkFrame(frame_topo, fg_color="transparent")
        datas_frame.pack(side="right", padx=10, pady=17)

        ctk.CTkLabel(datas_frame, text="Período:", text_color="#555", font=("Arial Bold", 13)).pack(side="left", padx=(0, 5))
        
        wrapper_ini, self.data_inicio = self._criar_date_wrapper(datas_frame, 120)
        self.data_inicio.set_date(date(date.today().year, 1, 1))
        wrapper_ini.pack(side="left", padx=2)

        ctk.CTkLabel(datas_frame, text="à", text_color="#555", font=("Arial Bold", 12)).pack(side="left", padx=5)

        wrapper_fim, self.data_fim = self._criar_date_wrapper(datas_frame, 120)
        wrapper_fim.pack(side="left", padx=2)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

        self.frame_cards = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_cards.pack(fill="x", pady=(5, 5))

        self.frame_tabelas = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_tabelas.pack(fill="x", pady=(5, 5))

        self.frame_graficos = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True, pady=(5, 10))

    def limpar_filtros_data(self):
        """Reseta as datas para o padrão (início do ano até hoje) e reaplica os filtros."""
        hoje = date.today()
        primeiro_dia_ano = date(hoje.year, 1, 1)
        
        # Reseta os calendários
        self.data_inicio.set_date(primeiro_dia_ano)
        self.data_fim.set_date(hoje)
        
        # Chama a função que atualiza os gráficos
        self.atualizar_completo()


    # =====================================================================
    # MÓDULO DE EXPORTAÇÃO PDF (POPUP COM RODAPÉ FIXO)
    # =====================================================================
    def _abrir_popup_exportacao(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Gerador de Relatório Analítico")
        popup.geometry("500x650")
        popup.grab_set()

        # 1. CABEÇALHO FIXO
        header = ctk.CTkFrame(popup, fg_color="transparent")
        header.pack(side="top", fill="x", pady=(20, 5))
        ctk.CTkLabel(header, text="Configuração Estrutural do PDF", font=("Arial Black", 16), text_color=COLOR_PRIMARY).pack()
        ctk.CTkLabel(header, text="Selecione minuciosamente os blocos que deseja exportar.", font=("Arial", 12), text_color="#555").pack()

        # 2. RODAPÉ FIXO (Garante que o botão nunca saia do ecrã)
        footer = ctk.CTkFrame(popup, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=20, padx=20)
        ctk.CTkButton(footer, text="⬇️ GERAR RELATÓRIO PDF", fg_color=COLOR_PRIMARY, hover_color="#0B6B59", font=("Arial Black", 14), height=45, command=lambda: self._iniciar_geracao_pdf(popup)).pack(fill="x")

        # 3. VARIÁVEIS
        self.vars_export = {
            "kpi_total_os": ctk.BooleanVar(value=True),
            "kpi_total_par": ctk.BooleanVar(value=True),
            "kpi_def": ctk.BooleanVar(value=True),
            "kpi_indef": ctk.BooleanVar(value=True),
            "g1": ctk.BooleanVar(value=True),
            "g2": ctk.BooleanVar(value=True),
            "g3": ctk.BooleanVar(value=True),
            "g4": ctk.BooleanVar(value=True),
            "g5": ctk.BooleanVar(value=True),
            "g6": ctk.BooleanVar(value=True),
        }

        # 4. ÁREA DE OPÇÕES COM SCROLL (Ocupa apenas o meio do popup)
        scroll_checks = ctk.CTkScrollableFrame(popup, fg_color="#F8F9FA", corner_radius=10, border_width=1, border_color="#DDDDDD")
        scroll_checks.pack(side="top", fill="both", expand=True, padx=20, pady=5)

        pad_opt = {"padx": 20, "pady": 4, "anchor": "w"}
        
        # SESSÃO 1: KPIs
        ctk.CTkLabel(scroll_checks, text="📋 Indicadores Gerais (KPIs)", font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(anchor="w", padx=10, pady=(10, 5))
        ctk.CTkCheckBox(scroll_checks, text="Card: Total de Ordens de Serviço", variable=self.vars_export["kpi_total_os"], font=("Arial", 12)).pack(**pad_opt)
        ctk.CTkCheckBox(scroll_checks, text="Card: Total de Pareceres", variable=self.vars_export["kpi_total_par"], font=("Arial", 12)).pack(**pad_opt)
        ctk.CTkCheckBox(scroll_checks, text="Card: Demandas Deferidas", variable=self.vars_export["kpi_def"], font=("Arial", 12)).pack(**pad_opt)
        ctk.CTkCheckBox(scroll_checks, text="Card: Demandas Indeferidas", variable=self.vars_export["kpi_indef"], font=("Arial", 12)).pack(**pad_opt)
        
        ctk.CTkFrame(scroll_checks, height=1, fg_color="#DDDDDD").pack(fill="x", padx=15, pady=10)
        
        # SESSÃO 2: GRÁFICOS DE VOLUME
        ctk.CTkLabel(scroll_checks, text="📊 Gráficos de Produção e Demanda", font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(anchor="w", padx=10, pady=(5, 5))
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Evolução Mensal de OS", variable=self.vars_export["g1"], font=("Arial", 12)).pack(**pad_opt)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Evolução Mensal de Pareceres", variable=self.vars_export["g2"], font=("Arial", 12)).pack(**pad_opt)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Top 10 Solicitantes Institucionais", variable=self.vars_export["g3"], font=("Arial", 12)).pack(**pad_opt)

        ctk.CTkFrame(scroll_checks, height=1, fg_color="#DDDDDD").pack(fill="x", padx=15, pady=10)

        # SESSÃO 3: GRÁFICOS DA EQUIPA
        ctk.CTkLabel(scroll_checks, text="👥 Gráficos de Desempenho da Equipa", font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(anchor="w", padx=10, pady=(5, 5))
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Comparação de Carga (OS vs Parecer)", variable=self.vars_export["g4"], font=("Arial", 12)).pack(**pad_opt)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Ranking de Produtividade Total Bruta", variable=self.vars_export["g5"], font=("Arial", 12)).pack(**pad_opt)
        ctk.CTkCheckBox(scroll_checks, text="Gráfico: Desempenho Relativo vs Média da Equipe", variable=self.vars_export["g6"], font=("Arial", 12)).pack(anchor="w", padx=20, pady=8)

    def _iniciar_geracao_pdf(self, popup):
        selecoes = {k: v.get() for k, v in self.vars_export.items()}
        if not any(selecoes.values()):
            return messagebox.showwarning("Aviso", "Selecione pelo menos um item para exportar.")

        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Relatorio_Itinerario.pdf", filetypes=[("PDF", "*.pdf")])
        if not filepath: return

        imagens = {}
        for key in ["g1", "g2", "g3", "g4", "g5", "g6"]:
            if selecoes[key]:
                imagens[key] = self._gerar_grafico_standalone(key)

        periodo_str = f"{self.data_inicio.get()} a {self.data_fim.get()}"
        c_os, c_par, c_def, c_indef = self.service.calcular_kpis(self.df_os_f, self.df_par_f)
        kpis = {"total_os": c_os, "total_par": c_par, "deferidos": c_def, "indeferidos": c_indef}

        sucesso, msg = self.service.exportar_dashboard_pdf(filepath, periodo_str, kpis, selecoes, imagens)

        if sucesso:
            messagebox.showinfo("Sucesso", msg)
            popup.destroy()
            os.startfile(filepath)
        else:
            messagebox.showerror("Erro", msg)

    # =====================================================================
    # NÚCLEO DE DADOS E RENDERIZAÇÃO
    # =====================================================================
    def criar_tabela(self, parent, titulo, headers, dados):
        container = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=10, border_width=1, border_color="#E0E0E0")
        container.pack(side="left", fill="both", expand=True, padx=8)
        ctk.CTkLabel(container, text=titulo, font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(pady=5)
        h_frame = ctk.CTkFrame(container, fg_color="#F1F3F5", height=35, corner_radius=6)
        h_frame.pack(fill="x", padx=10, pady=(0, 5))
        for i, h in enumerate(headers):
            h_frame.columnconfigure(i, weight=1)
            ctk.CTkLabel(h_frame, text=h, font=("Arial Bold", 11), text_color="#555").grid(row=0, column=i, pady=5)
        for row in dados:
            r_frame = ctk.CTkFrame(container, fg_color="transparent", height=30)
            r_frame.pack(fill="x", padx=10)
            for i, val in enumerate(row):
                r_frame.columnconfigure(i, weight=1)
                ctk.CTkLabel(r_frame, text=str(val), font=("Arial", 12), text_color=COLOR_TEXT).grid(row=0, column=i, pady=2)
        ctk.CTkFrame(container, fg_color="transparent", height=5).pack()

    def atualizar_completo(self):
        self.df_os_raw, self.df_par_raw = self.service.carregar_dados_brutos()
        self.renderizar_conteudo()

    def renderizar_conteudo(self):
        dt_inicio = self.data_inicio.get_date()
        dt_fim = self.data_fim.get_date()
        
        self.df_os_f, self.df_par_f = self.service.filtrar_dados(self.df_os_raw, self.df_par_raw, dt_inicio, dt_fim)
        self._preparar_dados_graficos() 

        for w in self.frame_cards.winfo_children(): w.destroy()
        try: c_os, c_par, c_def, c_indef = self.service.calcular_kpis(self.df_os_f, self.df_par_f)
        except: c_os, c_par, c_def, c_indef = 0, 0, 0, 0
        
        def add_card(titulo, valor, cor):
            card = ctk.CTkFrame(self.frame_cards, fg_color=COLOR_CARD_BG, height=80, corner_radius=8, border_width=1, border_color="#E0E0E0")
            card.pack(side="left", fill="x", expand=True, padx=8)
            ctk.CTkFrame(card, fg_color=cor, width=6, height=60, corner_radius=8).pack(side="left", fill="y")
            conteudo = ctk.CTkFrame(card, fg_color="transparent")
            conteudo.pack(side="left", fill="both", expand=True, padx=15, pady=10)
            ctk.CTkLabel(conteudo, text=titulo, font=("Arial Bold", 11), text_color="#777777").pack(anchor="w")
            ctk.CTkLabel(conteudo, text=str(valor), font=("Arial Black", 24), text_color=COLOR_TEXT).pack(anchor="w")

        add_card("TOTAL OS", c_os, COLOR_TEXT)
        add_card("TOTAL PARECERES", c_par, COLOR_PRIMARY)
        add_card("DEFERIDOS", c_def, "#28A745")
        add_card("INDEFERIDOS", c_indef, COLOR_SECONDARY)

        for w in self.frame_tabelas.winfo_children(): w.destroy()
        try:
            tab_par = self.service.preparar_tabela_mensal_pareceres(self.df_par_f)
            tab_os = self.service.preparar_tabela_mensal_os(self.df_os_f)
        except:
            tab_par, tab_os = [], [] 
        
        self.criar_tabela(self.frame_tabelas, "BALANÇO MENSAL DE PARECERES", ["Mês", "Deferidos", "Indeferidos", "Total"], tab_par)
        self.criar_tabela(self.frame_tabelas, "CATEGORIZAÇÃO MENSAL DE OS", ["Mês", "Eventos", "Corridas", "Obras", "Outros", "Total"], tab_os)

        self._renderizar_graficos_tela()

    # =====================================================================
    # MOTOR DE DESENHO UNIVERSAL (TELA E PDF)
    # =====================================================================
    def _preparar_dados_graficos(self):
        self.dados_graficos_cache.clear()
        
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        os_m = pd.Series(0, index=range(1,13))
        par_m = pd.Series(0, index=range(1,13))
        
        if not self.df_os_f.empty and 'data_dt' in self.df_os_f.columns:
            os_valid = self.df_os_f.dropna(subset=['data_dt'])
            if not os_valid.empty: os_m = os_valid['data_dt'].dt.month.value_counts().reindex(range(1,13), fill_value=0)
            
        if not self.df_par_f.empty and 'data_dt' in self.df_par_f.columns:
            par_valid = self.df_par_f.dropna(subset=['data_dt'])
            if not par_valid.empty: par_m = par_valid['data_dt'].dt.month.value_counts().reindex(range(1,13), fill_value=0)

        solic_val, solic_labels = [], []
        if not self.df_par_f.empty and 'solicitante' in self.df_par_f.columns:
            solic = self.df_par_f['solicitante'].value_counts().head(10)
            solic_labels = [textwrap.fill(str(s), 12) for s in solic.index]
            solic_val = solic.values

        u_os = self.df_os_f['criado_por'].value_counts() if not self.df_os_f.empty else pd.Series(dtype=int)
        u_par = self.df_par_f['criado_por'].value_counts() if not self.df_par_f.empty else pd.Series(dtype=int)
        total_prod = u_os.add(u_par, fill_value=0).sort_values(ascending=False).head(7)

        self.dados_graficos_cache = {
            "meses": meses, "os_m": os_m.values, "par_m": par_m.values,
            "solic_labels": solic_labels, "solic_val": solic_val,
            "u_os": u_os, "u_par": u_par, "total_prod": total_prod
        }

    def _configurar_eixo(self, ax, titulo):
        ax.set_title(titulo, fontsize=11, fontweight='bold', color=COLOR_TEXT, pad=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#DDDDDD')
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(colors='#555555', labelsize=8)
        ax.grid(axis='x', linestyle='--', alpha=0.3, color='#DDDDDD') 
        ax.set_facecolor(COLOR_CARD_BG)

    def _desenhar_grafico(self, ax, tipo):
        d = self.dados_graficos_cache

        def plot_bar_labels(x, y, title, color):
            bars = ax.bar(x, y, color=color, width=0.4)
            self._configurar_eixo(ax, title)
            ax.grid(axis='y', linestyle='--', alpha=0.3, color='#DDDDDD')
            ax.grid(axis='x', visible=False)
            if len(x) > 0 and isinstance(x[0], str): ax.tick_params(axis='x', rotation=45)
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + (max(y)*0.02),
                            f'{int(height)}', ha='center', va='bottom', fontsize=8, color=COLOR_TEXT, fontweight='bold')

        if tipo == "g1": plot_bar_labels(d["meses"], d["os_m"], "EVOLUÇÃO MENSAL DE OS", COLOR_PRIMARY)
        elif tipo == "g2": plot_bar_labels(d["meses"], d["par_m"], "EVOLUÇÃO MENSAL DE PARECERES", COLOR_SECONDARY)
        elif tipo == "g3": 
            if len(d["solic_val"]) > 0: plot_bar_labels(d["solic_labels"], d["solic_val"], "TOP 10 SOLICITANTES (PARECERES)", COLOR_PRIMARY)
            else: self._configurar_eixo(ax, "TOP 10 SOLICITANTES (PARECERES)")

        elif tipo == "g4":
            tp = d["total_prod"]
            if not tp.empty:
                x = np.arange(len(tp))
                width = 0.35 
                val_os = [d["u_os"].get(u, 0) for u in tp.index]
                val_par = [d["u_par"].get(u, 0) for u in tp.index]
                bars1 = ax.bar(x - width/2, val_os, width, label='OS', color=COLOR_PRIMARY)
                bars2 = ax.bar(x + width/2, val_par, width, label='Parecer', color=COLOR_SECONDARY)
                ax.set_xticks(x)
                ax.set_xticklabels([textwrap.fill(str(u), 10) for u in tp.index], rotation=45)
                ax.legend(fontsize=9)
                self._configurar_eixo(ax, "COMPARAÇÃO DE PRODUTIVIDADE: OS vs PARECER")
                ax.grid(axis='y', linestyle='--', alpha=0.3, color='#DDDDDD')
                ax.grid(axis='x', visible=False)
                m_v = max(max(val_os) if val_os else 0, max(val_par) if val_par else 0)
                for b in bars1:
                    if b.get_height() > 0: ax.text(b.get_x() + b.get_width()/2., b.get_height() + (m_v*0.02), f'{int(b.get_height())}', ha='center', va='bottom', fontsize=7, fontweight='bold')
                for b in bars2:
                    if b.get_height() > 0: ax.text(b.get_x() + b.get_width()/2., b.get_height() + (m_v*0.02), f'{int(b.get_height())}', ha='center', va='bottom', fontsize=7, fontweight='bold')
            else: self._configurar_eixo(ax, "COMPARAÇÃO DE PRODUTIVIDADE: OS vs PARECER")

        elif tipo == "g5":
            tp = d["total_prod"]
            if not tp.empty:
                labels = [textwrap.fill(str(u), 12) for u in tp.index]
                plot_bar_labels(labels, tp.values, "PRODUTIVIDADE TOTAL (OS + PARECER)", COLOR_PRIMARY)
            else: self._configurar_eixo(ax, "PRODUTIVIDADE TOTAL (OS + PARECER)")

        elif tipo == "g6":
            tp = d["total_prod"]
            if not tp.empty:
                tg = tp.sum()
                mi_qte = tg / len(tp)
                mi_pct = (mi_qte / tg) * 100 if tg > 0 else 0
                p_s = tp.sort_values(ascending=True)
                p_pct = (p_s / tg) * 100
                labels = [textwrap.fill(str(u), 15) for u in p_s.index]
                y_pos = np.arange(len(p_s))

                bars = ax.barh(y_pos, p_pct.values, color=COLOR_SECONDARY, height=0.45)
                ax.set_yticks(y_pos)
                ax.set_yticklabels(labels)
                self._configurar_eixo(ax, "PRODUTIVIDADE RELATIVA VS MÉDIA DA EQUIPE (%)")
                ax.grid(axis='x', linestyle='--', alpha=0.3, color='#DDDDDD')
                ax.grid(axis='y', visible=False)
                
                for bar, val_qte, pct in zip(bars, p_s.values, p_pct.values):
                    diff = pct - mi_pct
                    c_txt = COLOR_PRIMARY if val_qte >= mi_qte else COLOR_SECONDARY
                    s_txt = f"Acima (+{diff:.1f}%)" if val_qte >= mi_qte else f"Abaixo ({diff:.1f}%)"
                    ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f"  {pct:.1f}%  |  {s_txt}", ha='left', va='center', fontsize=9, fontweight='bold', color=c_txt)
                
                ax.set_xlim(0, p_pct.max() * 1.65)
                props = dict(boxstyle='round', facecolor='#F8F9FA', alpha=0.9, edgecolor=COLOR_PRIMARY)
                ax.text(0.95, 0.05, f"Média Ideal da Equipe:\n{mi_qte:.0f} Docs/Téc\n({mi_pct:.1f}%)", transform=ax.transAxes, fontsize=9, fontweight='bold', verticalalignment='bottom', horizontalalignment='right', bbox=props, color=COLOR_TEXT)
            else: self._configurar_eixo(ax, "PRODUTIVIDADE RELATIVA VS MÉDIA DA EQUIPE (%)")

    def _renderizar_graficos_tela(self):
        for w in self.frame_graficos.winfo_children(): w.destroy()
        fig, axs = plt.subplots(3, 2, figsize=(14, 16), facecolor=COLOR_BG)
        fig.patch.set_facecolor(COLOR_BG)
        plt.subplots_adjust(top=0.96, bottom=0.04, hspace=0.5, wspace=0.2)

        self._desenhar_grafico(axs[0,0], "g1")
        self._desenhar_grafico(axs[0,1], "g2")
        self._desenhar_grafico(axs[1,0], "g3")
        self._desenhar_grafico(axs[1,1], "g4")
        self._desenhar_grafico(axs[2,0], "g5")
        self._desenhar_grafico(axs[2,1], "g6")

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _gerar_grafico_standalone(self, tipo):
        fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=COLOR_CARD_BG)
        fig.patch.set_facecolor(COLOR_CARD_BG)
        
        self._desenhar_grafico(ax, tipo)
        
        img_io = io.BytesIO()
        fig.savefig(img_io, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        return img_io

def renderizar(frame_destino, usuario_logado):
    return DashboardItinerarioView(master=frame_destino, usuario_logado=usuario_logado)