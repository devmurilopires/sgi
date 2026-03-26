import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import textwrap
import io
from datetime import datetime
from tkinter import filedialog, messagebox
from src.modulos.quadro_horario.dashboard.service import DashboardQuadroHorarioService

COLOR_BG = "#F4F6F9"          
COLOR_WHITE = "#FFFFFF"       
COLOR_PRIMARY = "#0F8C75"     
COLOR_SECONDARY = "#F24822"   
COLOR_TEXT = "#333333"

class DashboardQuadroHorarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardQuadroHorarioService()
        self.df_par_raw = pd.DataFrame()
        self.df_pesq_raw = pd.DataFrame()
        self.df_par_f = pd.DataFrame()
        self.df_pesq_f = pd.DataFrame()
        self.fig = None 

        self._construir_interface()
        self.atualizar_completo()

    def _construir_interface(self):
        frame_filtros = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        frame_filtros.pack(fill="x", side="top")
        frame_filtros.pack_propagate(False)

        ctk.CTkLabel(frame_filtros, text="Painel Analítico - Quadro de Horários", font=("Arial Black", 22), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)
        
        self.btn_excel = ctk.CTkButton(frame_filtros, text="📥 EXCEL", font=("Arial Bold", 13), fg_color=COLOR_SECONDARY, width=80, height=35, command=self.exportar_excel)
        self.btn_excel.pack(side="right", padx=10, pady=17)

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

    def exportar_excel(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not filepath: return
        try:
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                if not self.df_par_f.empty:
                    self.df_par_f.to_excel(writer, sheet_name='Pareceres', index=False)
                if not self.df_pesq_f.empty:
                    self.df_pesq_f.to_excel(writer, sheet_name='Pesquisas', index=False)
                
                if self.fig is not None:
                    ws_graficos = writer.book.add_worksheet('Gráficos_SPR')
                    img_io = io.BytesIO()
                    self.fig.savefig(img_io, format='png', bbox_inches='tight', dpi=100)
                    img_io.seek(0)
                    ws_graficos.insert_image('A1', 'grafico.png', {'image_data': img_io})
            messagebox.showinfo("Sucesso", "Ficheiro Excel gerado com sucesso!")
        except Exception as e: messagebox.showerror("Erro", str(e))

    def criar_card(self, parent, titulo, valor, cor_destaque, icone):
        card = ctk.CTkFrame(parent, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        ctk.CTkFrame(card, fg_color=cor_destaque, width=6, height=60, corner_radius=8).pack(side="left", fill="y")
        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(conteudo, text=titulo, font=("Arial Bold", 13), text_color="#777777").pack(anchor="w")
        linha = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha.pack(fill="x", expand=True)
        ctk.CTkLabel(linha, text=valor, font=("Arial Black", 32), text_color=COLOR_TEXT).pack(side="left", pady=(5,0))
        ctk.CTkLabel(linha, text=icone, font=("Arial", 28)).pack(side="right", pady=(5,0))
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

    def atualizar_completo(self):
        self.df_par_raw, self.df_pesq_raw = self.service.carregar_dados_brutos()
        self.atualizar_dashboard()

    def atualizar_dashboard(self):
        try: ano_sel = int(self.cb_ano.get())
        except: ano_sel = datetime.now().year
        
        mes_str = self.cb_mes.get()
        mes_sel = int(mes_str.split(" - ")[0]) if mes_str != "Todos" else None

        self.df_par_f, self.df_pesq_f = self.service.filtrar_dados(self.df_par_raw, self.df_pesq_raw, ano_sel, mes_sel)

        for w in self.frame_kpis.winfo_children(): w.destroy()
        c_par, c_pesq, c_def, c_indef = self.service.calcular_kpis(self.df_par_f, self.df_pesq_f)
        
        self.frame_kpis.columnconfigure((0,1,2,3), weight=1)
        self.criar_card(self.frame_kpis, "TOTAL PARECERES (SPR)", f"{c_par}", COLOR_PRIMARY, "📋").grid(row=0, column=0, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "TOTAL PESQUISAS", f"{c_pesq}", "#14B5D9", "📊").grid(row=0, column=1, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES DEFERIDOS", f"{c_def}", "#28a745", "✅").grid(row=0, column=2, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES INDEFERIDOS", f"{c_indef}", "#dc3545", "❌").grid(row=0, column=3, padx=8, sticky="ew")

        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        self.fig, axs = plt.subplots(3, 2, figsize=(14, 18), facecolor=COLOR_WHITE)
        self.fig.patch.set_facecolor(COLOR_WHITE)

        if self.df_par_f.empty and self.df_pesq_f.empty:
            axs[0,0].text(0.5, 0.5, "Sen dados para o filtro aplicado", ha='center', fontsize=14)
        else:
            meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            meses_en = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

            # LINHA 1: Evolución
            ax = axs[0, 0]
            if not self.df_par_f.empty:
                counts = self.df_par_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0)
                bars = ax.bar(meses_pt, counts.values, color=COLOR_PRIMARY, width=0.6)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h, f'{int(h)}', ha='center', va='bottom', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, f"Evolução de Pareceres ({ano_sel})", grid_axis='y')

            ax = axs[0, 1]
            if not self.df_pesq_f.empty:
                counts = self.df_pesq_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0)
                bars = ax.bar(meses_pt, counts.values, color="#14B5D9", width=0.6)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h, f'{int(h)}', ha='center', va='bottom', fontweight='bold', color="#14B5D9")
            self._configurar_eixo(ax, f"Evolução de Pesquisas ({ano_sel})", grid_axis='y')

            # LINHA 2: Assuntos e Solicitantes
            ax = axs[1, 0]
            if not self.df_par_f.empty and 'assunto' in self.df_par_f.columns:
                counts = self.df_par_f['assunto'].replace("", "Não Informado").fillna("Não Informado").value_counts().head(5)
                labels = [textwrap.fill(str(nome), width=25) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color=COLOR_SECONDARY)
                ax.invert_yaxis()
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_SECONDARY)
            self._configurar_eixo(ax, "Top 5 Assuntos (Pareceres)", grid_axis='x')

            ax = axs[1, 1]
            if not self.df_par_f.empty and 'solicitante' in self.df_par_f.columns:
                counts = self.df_par_f['solicitante'].replace("", "Não Informado").fillna("Não Informado").value_counts().head(5)
                labels = [textwrap.fill(str(nome), width=25) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color=COLOR_PRIMARY)
                ax.invert_yaxis()
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, "Top 5 Solicitantes", grid_axis='x')

            # LINHA 3: Produtividade (Pareceres e Pesquisas)
            ax = axs[2, 0]
            if not self.df_par_f.empty and 'criado_por' in self.df_par_f.columns:
                counts = self.df_par_f['criado_por'].value_counts().head(5)
                labels = [textwrap.fill(str(nome), width=20) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color="#28a745")
                ax.invert_yaxis()
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color="#28a745")
            self._configurar_eixo(ax, "Produtividade: Pareceres por Técnico", grid_axis='x')

            ax = axs[2, 1]
            if not self.df_pesq_f.empty and 'criado_por' in self.df_pesq_f.columns:
                counts = self.df_pesq_f['criado_por'].value_counts().head(5)
                labels = [textwrap.fill(str(nome), width=20) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color="#14B5D9")
                ax.invert_yaxis()
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color="#14B5D9")
            self._configurar_eixo(ax, "Produtividade: Pesquisas por Técnico", grid_axis='x')

        self.fig.tight_layout(pad=4.0, h_pad=5.0)
        canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def renderizar(frame_destino, usuario_logado):
    return DashboardQuadroHorarioView(master=frame_destino, usuario_logado=usuario_logado)