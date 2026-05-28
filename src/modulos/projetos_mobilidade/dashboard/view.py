import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
import textwrap
from datetime import date
from tkcalendar import DateEntry
from src.modulos.projetos_mobilidade.dashboard.service import DashboardPMService
from src.modulos.projetos_mobilidade.dashboard.repository import DashboardPMRepository

COLOR_PRIMARY = "#0F8C75"     # Verde
COLOR_SECONDARY = "#F24822"   # Laranja
COLOR_BG = "#F4F6F9"
COLOR_CARD = "#FFFFFF"

class DashboardPMView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardPMService(DashboardPMRepository())
        self.df_raw = pd.DataFrame()
        self.df_f = pd.DataFrame()

        self._construir_interface()
        self.atualizar_completo()

    def _criar_date_wrapper(self, parent, width):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 11), background=COLOR_PRIMARY, foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _construir_interface(self):
        # TOP BAR
        topo = ctk.CTkFrame(self, fg_color=COLOR_CARD, height=70, corner_radius=0)
        topo.pack(fill="x", side="top")
        topo.pack_propagate(False)

        ctk.CTkLabel(topo, text="DASHBOARD ESTRATÉGICO | PROJETOS DE MOBILIDADE", font=("Arial Black", 18), text_color=COLOR_PRIMARY).pack(side="left", padx=20)

        ctk.CTkButton(topo, text="🔄 Atualizar", font=("Arial Bold", 12), fg_color=COLOR_PRIMARY, width=100, height=35, command=self.atualizar_completo).pack(side="right", padx=20)

        f_datas = ctk.CTkFrame(topo, fg_color="transparent")
        f_datas.pack(side="right", padx=10)
        
        ctk.CTkLabel(f_datas, text="Período:", font=("Arial Bold", 12), text_color="#555555").pack(side="left", padx=5)
        w_ini, self.data_ini = self._criar_date_wrapper(f_datas, 110)
        self.data_ini.set_date(date(date.today().year, 1, 1))
        w_ini.pack(side="left", padx=2)
        
        ctk.CTkLabel(f_datas, text="até", font=("Arial Bold", 12), text_color="#555555").pack(side="left", padx=5)
        w_fim, self.data_fim = self._criar_date_wrapper(f_datas, 110)
        w_fim.pack(side="left", padx=2)

        # SCROLL CONTENT
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_cards = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_cards.pack(fill="x", pady=5)

        self.frame_tabela = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_tabela.pack(fill="x", pady=10)

        self.frame_graficos = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True)

    def atualizar_completo(self):
        self.df_raw = self.service.carregar_dados_brutos()
        self.renderizar_tudo()

    def renderizar_tudo(self):
        self.df_f = self.service.filtrar_dados(self.df_raw, self.data_ini.get_date(), self.data_fim.get_date())
        
        # 1. CARDS
        for w in self.frame_cards.winfo_children(): w.destroy()
        tot, def_q, ind_q, top_s = self.service.calcular_kpis(self.df_f)
        
        self._add_card("TOTAL PARECERES", tot, COLOR_PRIMARY)
        self._add_card("DEFERIDOS", def_q, COLOR_PRIMARY)
        self._add_card("INDEFERIDOS", ind_q, COLOR_SECONDARY)
        self._add_card("TOP SOLICITANTE", top_s.split()[0] if isinstance(top_s, str) else top_s, COLOR_SECONDARY)

        # 2. TABELA
        for w in self.frame_tabela.winfo_children(): w.destroy()
        dados_tab = self.service.preparar_tabela_mensal(self.df_f)
        self._criar_tabela_balanco(self.frame_tabela, "BALANÇO MENSAL DE ANÁLISES TÉCNICAS", ["Mês", "Deferidos", "Indeferidos", "Total"], dados_tab)

        # 3. GRÁFICOS
        self._renderizar_graficos()

    def _add_card(self, tit, val, cor):
        c = ctk.CTkFrame( self.frame_cards, fg_color=COLOR_CARD, height=90, corner_radius=10, border_width=1,border_color="#E0E0E0")
        c.pack(side="left", fill="x", expand=True, padx=8)

        c.pack_propagate(False)
        ctk.CTkFrame( c, fg_color=cor, width=6, corner_radius=10).pack(side="left", fill="y")

        ctk.CTkLabel( c, text=tit, font=("Arial Bold", 11), text_color="#777777").pack(anchor="w", padx=15, pady=(4,0))
        ctk.CTkLabel( c, text=str(val), font=("Arial Black", 18), text_color="#333333").pack(anchor="w", padx=15, pady=(0,2))

    def _criar_tabela_balanco(self, parent, titulo, headers, dados):
        container = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color="#E0E0E0")
        container.pack(fill="x", padx=8)
        ctk.CTkLabel(container, text=titulo, font=("Arial Bold", 14), text_color=COLOR_PRIMARY).pack(pady=10)
        
        # Cabeçalho da tabela com Grid
        h_frame = ctk.CTkFrame(container, fg_color="#F1F3F5", height=35)
        h_frame.pack(fill="x", padx=15, pady=5)
        for i, h in enumerate(headers):
            h_frame.columnconfigure(i, weight=1, uniform="col")
            ctk.CTkLabel(h_frame, text=h, font=("Arial Bold", 11)).grid(row=0, column=i, pady=5, sticky="nsew")

        # Linhas da tabela renderizadas via Grid com correção de sticky="nsew"
        for r_idx, row in enumerate(dados):
            r_f = ctk.CTkFrame(container, fg_color="transparent")
            r_f.pack(fill="x", padx=15)
            for c_idx, v in enumerate(row):
                r_f.columnconfigure(c_idx, weight=1, uniform="col")
                # CORREÇÃO: sticky="nsew" garante que o layout configure sem erros e centralize o texto nativamente
                ctk.CTkLabel(r_f, text=str(v), font=("Arial", 12)).grid(row=0, column=c_idx, pady=3, sticky="nsew")

    def _renderizar_graficos(self):
        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        fig, axs = plt.subplots(2, 2, figsize=(14, 12), facecolor=COLOR_BG)
        fig.patch.set_facecolor(COLOR_BG)
        plt.subplots_adjust(left=0.15, bottom=0.08, right=0.95, top=0.92, wspace=0.3, hspace=0.4)

        # G1: Evolução Mensal
        ax = axs[0, 0]
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        s_mes = pd.Series(0, index=range(1,13))
        if not self.df_f.empty:
            s_mes = self.df_f['data_dt'].dt.month.value_counts().reindex(range(1,13), fill_value=0)
        
        bars = ax.bar(meses, s_mes.values, color=COLOR_PRIMARY, width=0.4)
        for b in bars:
            if b.get_height() > 0: ax.text(b.get_x()+b.get_width()/2, b.get_height(), int(b.get_height()), ha='center', va='bottom', fontweight='bold')
        self._formatar_eixo(ax, "Pareceres Gerados por Mês", 'y')

        # G2: Decisões
        ax = axs[0, 1]
        if not self.df_f.empty:
            counts = self.df_f['decisao'].value_counts()
            if not counts.empty:
                ax.pie(counts, labels=counts.index, autopct=lambda p: f"{int(p*sum(counts)/100)} un\n({p:.1f}%)", 
                       startangle=140, colors=[COLOR_PRIMARY, COLOR_SECONDARY], textprops={'fontweight':'bold'})
        ax.set_title("Proporção de Decisões", fontsize=12, fontweight='bold', pad=15)

        # G3: Top 10 Solicitantes
        ax = axs[1, 0]
        if not self.df_f.empty:
            solic = self.df_f['solicitante'].value_counts().head(10)
            if not solic.empty:
                labels = [textwrap.fill(str(s), 20) for s in solic.index]
                ax.barh(labels, solic.values, color=COLOR_PRIMARY, height=0.4)
                ax.invert_yaxis()
                for i, v in enumerate(solic.values): ax.text(v, i, f' {int(v)}', va='center', fontweight='bold')
        self._formatar_eixo(ax, "Top 10 Solicitantes (Geral)", 'x')

        # G4: Assuntos Mais Frequentes
        ax = axs[1, 1]
        if not self.df_f.empty:
            assuntos = self.df_f['assunto'].value_counts().head(5)
            if not assuntos.empty:
                ax.pie(assuntos, labels=[textwrap.fill(str(a), 15) for a in assuntos.index], autopct='%1.1f%%', \
                       startangle=90, colors=plt.cm.Oranges(np.linspace(0.1, 0.5, len(assuntos))), textprops={'fontweight':'bold'})
        ax.set_title("Top 5 Assuntos Demandados", fontsize=12, fontweight='bold', pad=15)

        canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _formatar_eixo(self, ax, titulo, eixo_int):
        ax.set_title(titulo, fontsize=12, fontweight='bold', pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        if eixo_int == 'y': ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        else: ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_facecolor(COLOR_CARD)
        ax.grid(axis=eixo_int, linestyle='--', alpha=0.3)

def renderizar(frame_destino, usuario_logado):
    return DashboardPMView(master=frame_destino, usuario_logado=usuario_logado)