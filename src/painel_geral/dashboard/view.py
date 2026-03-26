import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
import textwrap
import io
from datetime import datetime
from tkinter import filedialog, messagebox
from src.painel_geral.dashboard.service import DashboardGeralService

# --- Cores Executivas ---
COLOR_BG = "#F4F6F9"          
COLOR_WHITE = "#FFFFFF"       
COLOR_PRIMARY = "#0F8C75"     
COLOR_SECONDARY = "#F24822"   
COLOR_TEXT = "#333333"

class DashboardGeralView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardGeralService()
        self.df_os_raw = pd.DataFrame()
        self.df_par_raw = pd.DataFrame()
        self.df_pesq_raw = pd.DataFrame()
        
        self.df_os_f = pd.DataFrame()
        self.df_par_f = pd.DataFrame()
        self.df_pesq_f = pd.DataFrame()
        self.fig = None 

        self._construir_interface()
        self.atualizar_completo()

    def _construir_interface(self):
        frame_filtros = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        frame_filtros.pack(fill="x", side="top")
        frame_filtros.pack_propagate(False)

        ctk.CTkLabel(frame_filtros, text="VISÃO GLOBAL DIPLA - Raio-X Operacional", font=("Arial Black", 22), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)
        
        self.btn_pdf = ctk.CTkButton(frame_filtros, text="📄 PDF Executivo", font=("Arial Bold", 13), fg_color=COLOR_SECONDARY, width=120, height=35, command=self.exportar_pdf)
        self.btn_pdf.pack(side="right", padx=10, pady=17)

        self.btn_filtrar = ctk.CTkButton(frame_filtros, text="🔍 ATUALIZAR", font=("Arial Bold", 13), fg_color=COLOR_PRIMARY, width=110, height=35, command=self.atualizar_completo)
        self.btn_filtrar.pack(side="right", padx=(20, 5), pady=17)

        self.cb_mes = ctk.CTkComboBox(frame_filtros, values=["Todos", "01 - Jan", "02 - Fev", "03 - Mar", "04 - Abr", "05 - Mai", "06 - Jun", "07 - Jul", "08 - Ago", "09 - Set", "10 - Out", "11 - Nov", "12 - Dez"], width=130, height=35)
        self.cb_mes.set("Todos")
        self.cb_mes.pack(side="right", padx=10, pady=17)
        ctk.CTkLabel(frame_filtros, text="Mês:", text_color="#555", font=("Arial Bold", 13)).pack(side="right")

        self.cb_ano = ctk.CTkComboBox(frame_filtros, values=[str(a) for a in range(2024, 2030)], width=100, height=35)
        self.cb_ano.set(str(datetime.now().year))
        self.cb_ano.pack(side="right", padx=10, pady=17)
        ctk.CTkLabel(frame_filtros, text="Ano:", text_color="#555", font=("Arial Bold", 13)).pack(side="right")

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
        ctk.CTkLabel(conteudo, text=titulo, font=("Arial Bold", 12), text_color="#777777").pack(anchor="w")
        linha = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha.pack(fill="x", expand=True)
        ctk.CTkLabel(linha, text=valor, font=("Arial Black", 28), text_color=COLOR_TEXT).pack(side="left", pady=(5,0))
        ctk.CTkLabel(linha, text=icone, font=("Arial", 26)).pack(side="right", pady=(5,0))
        return card

    def _configurar_eixo(self, ax, titulo, grid_axis='y'):
        ax.set_title(titulo, fontsize=13, fontweight='bold', color=COLOR_TEXT, pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#DDDDDD')
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(colors='#555555')
        ax.grid(axis=grid_axis, linestyle='--', alpha=0.3, color='#DDDDDD') 
        ax.set_facecolor(COLOR_WHITE)

    def exportar_pdf(self):
        if self.fig is None: return messagebox.showwarning("Aviso", "Não há gráficos.")
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if filepath:
            try:
                with PdfPages(filepath) as pdf:
                    pdf.savefig(self.fig, bbox_inches='tight', pad_inches=0.3)  
                messagebox.showinfo("Sucesso", "Relatório PDF Gerado!")
                os.startfile(filepath)
            except Exception as e: messagebox.showerror("Erro", str(e))

    def atualizar_completo(self):
        self.df_os_raw, self.df_par_raw, self.df_pesq_raw = self.service.carregar_dados_brutos()
        self.atualizar_dashboard()

    def atualizar_dashboard(self):
        try: ano_sel = int(self.cb_ano.get())
        except: ano_sel = datetime.now().year
        
        mes_str = self.cb_mes.get()
        mes_sel = int(mes_str.split(" - ")[0]) if mes_str != "Todos" else None

        self.df_os_f, self.df_par_f, self.df_pesq_f = self.service.filtrar_dados(self.df_os_raw, self.df_par_raw, self.df_pesq_raw, ano_sel, mes_sel)

        for w in self.frame_kpis.winfo_children(): w.destroy()
        c_tot, c_os, c_par, c_pesq, champ = self.service.calcular_kpis(self.df_os_f, self.df_par_f, self.df_pesq_f)
        
        self.frame_kpis.columnconfigure((0,1,2,3,4), weight=1)
        self.criar_card(self.frame_kpis, "DOCUMENTOS GERADOS", f"{c_tot}", "#333333", "📁").grid(row=0, column=0, padx=5, sticky="ew")
        self.criar_card(self.frame_kpis, "ORDENS DE SERVIÇO", f"{c_os}", COLOR_PRIMARY, "📋").grid(row=0, column=1, padx=5, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES TÉCNICOS", f"{c_par}", "#14B5D9", "📝").grid(row=0, column=2, padx=5, sticky="ew")
        self.criar_card(self.frame_kpis, "PESQUISAS (SPR)", f"{c_pesq}", "#28a745", "📊").grid(row=0, column=3, padx=5, sticky="ew")
        self.criar_card(self.frame_kpis, "DESTAQUE PRODUTIVIDADE", f"{champ.split()[0]}", "#F29C1F", "🏆").grid(row=0, column=4, padx=5, sticky="ew")

        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        self.fig, axs = plt.subplots(3, 2, figsize=(14, 18), facecolor=COLOR_WHITE)
        self.fig.patch.set_facecolor(COLOR_WHITE)

        meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        meses_en = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

        # LINHA 1: Evolução Global vs Distribuição por Módulo
        ax = axs[0, 0]
        s1 = self.df_os_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0) if not self.df_os_f.empty else pd.Series(0, index=meses_en)
        s2 = self.df_par_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0) if not self.df_par_f.empty else pd.Series(0, index=meses_en)
        s3 = self.df_pesq_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0) if not self.df_pesq_f.empty else pd.Series(0, index=meses_en)
        
        ax.plot(meses_pt, s1.values, marker='o', color=COLOR_PRIMARY, label='OS', linewidth=2)
        ax.plot(meses_pt, s2.values, marker='s', color="#14B5D9", label='Pareceres', linewidth=2)
        ax.plot(meses_pt, s3.values, marker='^', color="#28a745", label='Pesquisas', linewidth=2)
        ax.legend()
        self._configurar_eixo(ax, f"Evolução de Produção da DIPLA ({ano_sel})", grid_axis='y')

        ax = axs[0, 1]
        modulos = ["Ponto de Parada (SIGP)", "Itinerário (SIGA)", "Horários (SPR)"]
        vol_sigp = len(self.df_os_f[self.df_os_f['modulo'] == 'Ponto de Parada']) + len(self.df_par_f[self.df_par_f['modulo'] == 'sigp'])
        vol_siga = len(self.df_os_f[self.df_os_f['modulo'] == 'Itinerário']) + len(self.df_par_f[self.df_par_f['modulo'] == 'siga'])
        vol_spr = len(self.df_par_f[self.df_par_f['modulo'] == 'spr']) + len(self.df_pesq_f)
        
        if sum([vol_sigp, vol_siga, vol_spr]) > 0:
            ax.pie([vol_sigp, vol_siga, vol_spr], labels=modulos, autopct='%1.1f%%', startangle=140, colors=[COLOR_PRIMARY, COLOR_SECONDARY, "#14B5D9"], textprops={'fontweight': 'bold'})
            ax.set_title("Volume de Trabalho por Setor", fontsize=13, fontweight='bold', pad=15)
        else:
            self._configurar_eixo(ax, "Volume de Trabalho por Setor")
            ax.text(0.5, 0.5, "Sem dados", ha='center')

        # LINHA 2: Produtividade Setorial
        ax = axs[1, 0]
        if not self.df_os_f.empty:
            counts = self.df_os_f['criado_por'].value_counts().head(5)
            labels = [textwrap.fill(str(nome), width=25) for nome in counts.index]
            bars = ax.barh(labels, counts.values, color=COLOR_PRIMARY)
            ax.invert_yaxis()
            for bar in bars:
                w = bar.get_width()
                if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_PRIMARY)
        self._configurar_eixo(ax, "Top 5 Técnicos (Apenas OS)", grid_axis='x')

        ax = axs[1, 1]
        if not self.df_par_f.empty:
            counts = self.df_par_f['criado_por'].value_counts().head(5)
            labels = [textwrap.fill(str(nome), width=25) for nome in counts.index]
            bars = ax.barh(labels, counts.values, color="#14B5D9")
            ax.invert_yaxis()
            for bar in bars:
                w = bar.get_width()
                if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color="#14B5D9")
        self._configurar_eixo(ax, "Top 5 Técnicos (Apenas Pareceres)", grid_axis='x')

        # LINHA 3: Ranking Global e Decisões
        ax = axs[2, 0]
        s_os = self.df_os_f['criado_por'].value_counts() if not self.df_os_f.empty else pd.Series(dtype=int)
        s_par = self.df_par_f['criado_por'].value_counts() if not self.df_par_f.empty else pd.Series(dtype=int)
        s_pesq = self.df_pesq_f['criado_por'].value_counts() if not self.df_pesq_f.empty else pd.Series(dtype=int)
        prod_total = s_os.add(s_par, fill_value=0).add(s_pesq, fill_value=0).sort_values(ascending=False).head(10)
        
        if not prod_total.empty:
            labels = [textwrap.fill(str(nome), width=20) for nome in prod_total.index]
            bars = ax.barh(labels, prod_total.values, color="#333333")
            ax.invert_yaxis()
            for bar in bars:
                w = bar.get_width()
                if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color="#333333")
        self._configurar_eixo(ax, "RANKING GLOBAL (Toda a Empresa)", grid_axis='x')

        ax = axs[2, 1]
        if not self.df_par_f.empty and 'decisao' in self.df_par_f.columns:
            counts = self.df_par_f['decisao'].value_counts()
            if not counts.empty:
                ax.bar(counts.index, counts.values, color=["#28a745" if "DEF" in str(x).upper() else "#dc3545" for x in counts.index], width=0.5)
                for i, v in enumerate(counts.values):
                    ax.text(i, v, f'{int(v)}', ha='center', va='bottom', fontweight='bold')
        self._configurar_eixo(ax, "Volume de Deferimento vs Indeferimento", grid_axis='y')

        self.fig.tight_layout(pad=4.0, h_pad=5.0)
        canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def renderizar(frame_destino, usuario_logado):
    return DashboardGeralView(master=frame_destino, usuario_logado=usuario_logado)