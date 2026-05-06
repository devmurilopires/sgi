import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MaxNLocator
import textwrap
import os
from datetime import date
from tkcalendar import DateEntry
from tkinter import filedialog, messagebox
from src.painel_geral.dashboard.service import DashboardGeralService

# --- Cores Definidas ---
COLOR_BG = "#F4F6F9"          
COLOR_WHITE = "#FFFFFF"       
COLOR_PRIMARY = "#0F8C75"     # Verde
COLOR_SECONDARY = "#F24822"   # Laranja
COLOR_TEXT = "#333333"

class DashboardGeralView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardGeralService()
        self.df_os_raw = pd.DataFrame()
        self.df_par_raw = pd.DataFrame()
        self.df_pesq_raw = pd.DataFrame()
        
        self.fig = None 

        self._construir_interface()
        self.atualizar_completo()

    def _criar_date_wrapper(self, parent, width):
        """Cria um contorno estilizado em volta do calendário"""
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color="#FFFFFF", border_width=1, border_color="#AAAAAA", corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 11), background="#0F8C75", foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _construir_interface(self):
        frame_filtros = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        frame_filtros.pack(fill="x", side="top")
        frame_filtros.pack_propagate(False)

        ctk.CTkLabel(frame_filtros, text="DASHBOARD EXECUTIVO - Produtividade Global", font=("Arial Black", 20), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)
        
        self.btn_pdf = ctk.CTkButton(frame_filtros, text="📄 Exportar PDF", font=("Arial Bold", 13), fg_color="#333333", width=120, height=35, command=self.exportar_pdf)
        self.btn_pdf.pack(side="right", padx=15, pady=17)

        self.btn_filtrar = ctk.CTkButton(frame_filtros, text="🔍 Aplicar Filtro", font=("Arial Bold", 13), fg_color=COLOR_PRIMARY, width=120, height=35, command=self.atualizar_dashboard)
        self.btn_filtrar.pack(side="right", padx=10, pady=17)

        # Filtros de Data com calendário estilizado
        f_data = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        f_data.pack(side="right", padx=10, pady=17)
        
        ctk.CTkLabel(f_data, text="Data Fim:", text_color="#555", font=("Arial Bold", 12)).pack(side="left", padx=(10, 5))
        wrapper_fim, self.date_fim = self._criar_date_wrapper(f_data, 120)
        self.date_fim.set_date(date.today())
        wrapper_fim.pack(side="left")

        ctk.CTkLabel(f_data, text="Data Início:", text_color="#555", font=("Arial Bold", 12)).pack(side="left", padx=(10, 5))
        wrapper_ini, self.date_ini = self._criar_date_wrapper(f_data, 120)
        self.date_ini.set_date(date(date.today().year, 1, 1))
        wrapper_ini.pack(side="left")

        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_kpis = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_kpis.pack(fill="x", pady=(0, 15))

        self.frame_graficos = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True, pady=10)

    def criar_card(self, parent, titulo, valor, cor_destaque, icone):
        card = ctk.CTkFrame(parent, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        ctk.CTkFrame(card, fg_color=cor_destaque, width=6, height=60, corner_radius=8).pack(side="left", fill="y")
        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(conteudo, text=titulo, font=("Arial Bold", 11), text_color="#777777").pack(anchor="w")
        linha = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha.pack(fill="x", expand=True)
        ctk.CTkLabel(linha, text=valor, font=("Arial Black", 24), text_color=COLOR_TEXT).pack(side="left", pady=(5,0))
        ctk.CTkLabel(linha, text=icone, font=("Arial", 26)).pack(side="right", pady=(5,0))
        return card

    def _configurar_eixo(self, ax, titulo, grid_axis='y', is_pie=False):
        ax.set_title(titulo, fontsize=12, fontweight='bold', color=COLOR_TEXT, pad=15)
        if not is_pie:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#DDDDDD')
            ax.spines['bottom'].set_color('#DDDDDD')
            ax.grid(axis=grid_axis, linestyle='--', alpha=0.4, color='#EEEEEE')
            
            # Força o eixo a ter apenas números inteiros (sem decimais)
            if grid_axis == 'y':
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            elif grid_axis == 'x':
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))
                
        ax.set_facecolor(COLOR_WHITE)

    def exportar_pdf(self):
        if self.fig is None: return messagebox.showwarning("Aviso", "Não há gráficos gerados.")
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if filepath:
            try:
                with PdfPages(filepath) as pdf:
                    pdf.savefig(self.fig, bbox_inches='tight', pad_inches=0.3)  
                messagebox.showinfo("Sucesso", "Relatório PDF Executivo Gerado!")
                os.startfile(filepath)
            except Exception as e: messagebox.showerror("Erro", str(e))

    def atualizar_completo(self):
        self.df_os_raw, self.df_par_raw, self.df_pesq_raw = self.service.carregar_dados_brutos()
        self.atualizar_dashboard()

    def atualizar_dashboard(self):
        dt_ini = self.date_ini.get_date()
        dt_fim = self.date_fim.get_date()

        df_os_f, df_par_f, df_pesq_f = self.service.filtrar_dados(self.df_os_raw, self.df_par_raw, self.df_pesq_raw, dt_ini, dt_fim)

        for w in self.frame_kpis.winfo_children(): w.destroy()
        c_tot, c_os, c_par, c_pesq, champ = self.service.calcular_kpis(df_os_f, df_par_f, df_pesq_f)
        
        self.frame_kpis.columnconfigure((0,1,2,3,4), weight=1)
        self.criar_card(self.frame_kpis, "TOTAL DE DOCUMENTOS", f"{c_tot}", "#333333", "📁").grid(row=0, column=0, padx=5, sticky="ew")
        self.criar_card(self.frame_kpis, "ORDENS DE SERVIÇO", f"{c_os}", COLOR_PRIMARY, "📋").grid(row=0, column=1, padx=5, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES TÉCNICOS", f"{c_par}", COLOR_SECONDARY, "📝").grid(row=0, column=2, padx=5, sticky="ew")
        self.criar_card(self.frame_kpis, "PESQUISAS (SPR)", f"{c_pesq}", COLOR_PRIMARY, "📊").grid(row=0, column=3, padx=5, sticky="ew")
        self.criar_card(self.frame_kpis, "DESTAQUE PRODUTIVIDADE", f"{champ.split()[0]}", "#F29C1F", "🏆").grid(row=0, column=4, padx=5, sticky="ew")

        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        # GRID 5x2 (2 COLUNAS LARGAS) PARA 10 GRÁFICOS
        self.fig, axs = plt.subplots(5, 2, figsize=(16, 26), facecolor=COLOR_WHITE)
        self.fig.patch.set_facecolor(COLOR_WHITE)
        
        # Ajuste de Layout para não cortar textos
        plt.subplots_adjust(left=0.18, right=0.95, top=0.96, bottom=0.04, wspace=0.3, hspace=0.6) 

        # --- FUNÇÕES DE DESENHO COM COR ÚNICA FIXA E MESES COMPLETOS ---
        def plotar_colunas_mes(ax, df, titulo, cor):
            meses_labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            s = pd.Series(0, index=range(1, 13)) # Garante 12 posições
            
            if not df.empty and 'data_dt' in df.columns:
                df_valid = df.dropna(subset=['data_dt'])
                if not df_valid.empty:
                    counts = df_valid['data_dt'].dt.month.value_counts()
                    s = counts.reindex(range(1, 13), fill_value=0) # Preenche os meses sem dados com 0
                    
            bars = ax.bar(meses_labels, s.values, width=0.35, color=cor)
            for bar in bars:
                h = bar.get_height()
                if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h, f'{int(h)}', ha='center', va='bottom', fontsize=9, fontweight='bold', color=COLOR_TEXT)
            ax.tick_params(axis='x', rotation=45)
            self._configurar_eixo(ax, titulo, grid_axis='y')

        def plotar_barras_horizontais(ax, s_dados, titulo, cor):
            if not s_dados.empty:
                # Textwrap maior e labelsize reduzido evitam que os nomes se sobreponham verticalmente
                labels = [textwrap.fill(str(n), width=28) for n in s_dados.index]
                bars = ax.barh(labels, s_dados.values, height=0.35, color=cor) 
                ax.invert_yaxis()
                for i, v in enumerate(s_dados.values): 
                    ax.text(v, i, f' {int(v)}', va='center', fontweight='bold', color=COLOR_TEXT)
                ax.tick_params(axis='y', labelsize=8) 
            self._configurar_eixo(ax, titulo, grid_axis='x')

        def plot_pizza(ax, counts, labels, colors, titulo):
            if sum(counts) > 0:
                def fmt_pizza(pct, allvals):
                    absolute = int(round(pct/100.*sum(allvals)))
                    return f"{absolute} un\n({pct:.1f}%)"
                ax.pie(counts, labels=labels, autopct=lambda pct: fmt_pizza(pct, counts), startangle=140, colors=colors, textprops={'fontweight': 'bold'})
            else: ax.text(0.5, 0.5, "Sem dados", ha='center')
            self._configurar_eixo(ax, titulo, is_pie=True)

        # =========================================================
        # LINHA 1 (Evoluções Mensais OS e Parecer)
        # =========================================================
        plotar_colunas_mes(axs[0, 0], df_os_f, "Evolução de OS por Mês", COLOR_PRIMARY)
        plotar_colunas_mes(axs[0, 1], df_par_f, "Evolução de Pareceres por Mês", COLOR_SECONDARY)

        # =========================================================
        # LINHA 2 (Evolução Pesquisas e Quantidade de Origem)
        # =========================================================
        plotar_colunas_mes(axs[1, 0], df_pesq_f, "Evolução de Pesquisas por Mês", COLOR_PRIMARY)
        
        origens = pd.concat([
            df_os_f['origem'] if 'origem' in df_os_f.columns else pd.Series(dtype=str),
            df_par_f['origem'] if 'origem' in df_par_f.columns else pd.Series(dtype=str)
        ]).dropna().value_counts()
        plotar_barras_horizontais(axs[1, 1], origens, "Quantidade Total por Origem", COLOR_SECONDARY)

        # =========================================================
        # LINHA 3 (Setor e Decisões)
        # =========================================================
        vols = [
            len(df_os_f[df_os_f['modulo'] == 'Ponto de Parada']) + len(df_par_f[df_par_f['modulo'] == 'Ponto de Parada']) if not df_os_f.empty else 0,
            len(df_os_f[df_os_f['modulo'] == 'Itinerário']) + len(df_par_f[df_par_f['modulo'] == 'Itinerário']) if not df_os_f.empty else 0,
            len(df_par_f[df_par_f['modulo'] == 'Quadro de Horário']) + len(df_pesq_f) if not df_par_f.empty else 0
        ]
        labels_setor = ["Ponto de Parada", "Itinerário", "Quadro de Horário"]
        vols_plot = [v for v in vols if v > 0]
        labels_plot = [l for l, v in zip(labels_setor, vols) if v > 0]
        plot_pizza(axs[2, 0], vols_plot, labels_plot, [COLOR_PRIMARY, COLOR_SECONDARY, "#555555"], "Volume de Trabalho por Setor")

        ax_decisao = axs[2, 1]
        if not df_par_f.empty and 'decisao' in df_par_f.columns:
            c_dec = df_par_f['decisao'].value_counts()
            if not c_dec.empty:
                cores_decisao = [COLOR_PRIMARY if "DEF" in str(x).upper() else COLOR_SECONDARY for x in c_dec.index]
                plot_pizza(ax_decisao, c_dec.values, c_dec.index, cores_decisao, "Decisões: Deferido vs Indeferido")
        else: self._configurar_eixo(ax_decisao, "Decisões: Deferido vs Indeferido", is_pie=True)

        # =========================================================
        # LINHA 4 (Top 5 OS Lado a Lado com Top 5 Pareceres)
        # =========================================================
        s_os_tec = df_os_f['criado_por'].value_counts().head(5) if not df_os_f.empty else pd.Series(dtype=int)
        plotar_barras_horizontais(axs[3, 0], s_os_tec, "Top 5 Técnicos (OS)", COLOR_PRIMARY)

        s_par_tec = df_par_f['criado_por'].value_counts().head(5) if not df_par_f.empty else pd.Series(dtype=int)
        plotar_barras_horizontais(axs[3, 1], s_par_tec, "Top 5 Técnicos (Pareceres)", COLOR_SECONDARY)

        # =========================================================
        # LINHA 5 (Solicitantes Lado a Lado com Ranking Global TODOS)
        # =========================================================
        solicitantes = pd.concat([
            df_os_f['solicitante'] if 'solicitante' in df_os_f.columns else pd.Series(dtype=str),
            df_par_f['solicitante'] if 'solicitante' in df_par_f.columns else pd.Series(dtype=str)
        ]).dropna().value_counts().head(10)
        plotar_barras_horizontais(axs[4, 0], solicitantes, "Top 10 Solicitantes Global", COLOR_PRIMARY)

        s_os_all = df_os_f['criado_por'].value_counts() if not df_os_f.empty else pd.Series(dtype=int)
        s_par_all = df_par_f['criado_por'].value_counts() if not df_par_f.empty else pd.Series(dtype=int)
        # Removido o .head() para mostrar TODOS os usuários no Ranking Global
        prod_total = s_os_all.add(s_par_all, fill_value=0).sort_values(ascending=False)
        plotar_barras_horizontais(axs[4, 1], prod_total, "Ranking Global (Todos os Usuários)", COLOR_SECONDARY)

        canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def renderizar(frame_destino, usuario_logado):
    return DashboardGeralView(master=frame_destino, usuario_logado=usuario_logado)