import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MaxNLocator
import textwrap
import io
from datetime import datetime
from tkinter import filedialog, messagebox
from src.modulos.itinerario.dashboard.service import DashboardItinerarioService

# --- Paleta de Cores ---
COLOR_BG = "#F4F6F9"          
COLOR_WHITE = "#FFFFFF"       
COLOR_PRIMARY = "#0F8C75"     
COLOR_SECONDARY = "#F24822"   
COLOR_TEXT = "#333333"

class DashboardItinerarioView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardItinerarioService()
        self.df_os_raw = pd.DataFrame()
        self.df_par_raw = pd.DataFrame()
        self.df_os_f = pd.DataFrame()
        self.df_par_f = pd.DataFrame()
        self.fig = None 

        self._construir_interface()
        self.atualizar_completo()

    def _construir_interface(self):
        frame_filtros = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=0, height=70)
        frame_filtros.pack(fill="x", side="top")
        frame_filtros.pack_propagate(False)

        ctk.CTkLabel(frame_filtros, text="Painel Analítico - Itinerários", font=("Arial Black", 22), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)
        
        self.btn_pdf = ctk.CTkButton(frame_filtros, text="📄 PDF", font=("Arial Bold", 13), fg_color=COLOR_SECONDARY, width=70, height=35, command=self.exportar_pdf)
        self.btn_pdf.pack(side="right", padx=10, pady=17)

        self.btn_excel = ctk.CTkButton(frame_filtros, text="📥 EXCEL", font=("Arial Bold", 13), fg_color=COLOR_PRIMARY, width=80, height=35, command=self.exportar_excel)
        self.btn_excel.pack(side="right", padx=5, pady=17)

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

        self.frame_tabela = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_tabela.pack(fill="x", pady=10)

        self.frame_graficos = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True, pady=10)

    # LÓGICA DE EXPORTAÇÃO E TABELA
    def _gerar_dataframe_resumo(self):
        meses_pt = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        categorias = ["DEFERIDO", "INDEFERIDO", "EVENTOS", "CORRIDA", "OBRAS"]
        
        dados_tabela = []
        for item in categorias:
            linha = {"CATEGORIA DE SERVIÇO": item}
            for mes in meses_pt: linha[mes] = 0
            linha["TOTAL"] = 0
            dados_tabela.append(linha)
            
        df_resumo = pd.DataFrame(dados_tabela)

        def preencher_contagem(df, coluna, valor_procurado, nome_categoria):
            if df.empty: return
            df_filtro = df[df[coluna].fillna("").str.strip().str.upper() == valor_procurado]
            idx = df_resumo[df_resumo['CATEGORIA DE SERVIÇO'] == nome_categoria].index[0]
            for _, row in df_filtro.iterrows():
                try:
                    mes_nome = meses_pt[row['data_dt'].month - 1]
                    df_resumo.at[idx, mes_nome] += 1
                    df_resumo.at[idx, "TOTAL"] += 1
                except: pass

        preencher_contagem(self.df_par_f, 'tipo', 'DEFERIDO', 'DEFERIDO')
        preencher_contagem(self.df_par_f, 'tipo', 'INDEFERIDO', 'INDEFERIDO')
        preencher_contagem(self.df_os_f, 'tipo_os', 'EVENTOS', 'EVENTOS')
        preencher_contagem(self.df_os_f, 'tipo_os', 'CORRIDA', 'CORRIDA')
        preencher_contagem(self.df_os_f, 'tipo_os', 'OBRAS', 'OBRAS')

        total_row = {"CATEGORIA DE SERVIÇO": "TOTAL GERAL"}
        for col in meses_pt + ["TOTAL"]:
            total_row[col] = df_resumo[col].sum()
        df_resumo.loc[len(df_resumo)] = total_row

        return df_resumo

    def exportar_pdf(self):
        if self.fig is None: return messagebox.showwarning("Aviso", "Não há gráficos.")
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if filepath:
            try:
                df_resumo = self._gerar_dataframe_resumo()
                fig_table, ax_table = plt.subplots(figsize=(16, 5), facecolor='#FFFFFF')
                ax_table.axis('off')
                fig_table.suptitle("Resumo Consolidado de Itinerários", fontsize=22, fontweight='bold', color="#333333", y=0.92)
                
                cell_text = [[row[0]] + [str(int(x)) for x in row[1:]] for row in df_resumo.values]
                table = ax_table.table(cellText=cell_text, colLabels=df_resumo.columns, cellLoc='center', loc='center')
                table.auto_set_font_size(False); table.set_fontsize(11); table.scale(1, 1.8) 
                
                for (row, col), cell in table.get_celld().items():
                    if row == 0: cell.set_text_props(weight='bold', color='white'); cell.set_facecolor(COLOR_PRIMARY) 
                    elif row == len(df_resumo): cell.set_text_props(weight='bold'); cell.set_facecolor('#E0E4E8')
                    if col == 0: cell._loc = 'left'; cell.set_width(0.25) 
                    else: cell.set_width(0.055) 

                with PdfPages(filepath) as pdf:
                    pdf.savefig(fig_table, bbox_inches='tight', pad_inches=0.3) 
                    pdf.savefig(self.fig, bbox_inches='tight', pad_inches=0.3)  
                plt.close(fig_table)
                messagebox.showinfo("Sucesso", "PDF Gerado!")
            except Exception as e: messagebox.showerror("Erro", str(e))

    def exportar_excel(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not filepath: return
        try:
            df_resumo = self._gerar_dataframe_resumo()
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
                worksheet = writer.sheets['Resumo']
                fmt_header = writer.book.add_format({'bold': True, 'bg_color': COLOR_PRIMARY, 'font_color': 'white', 'align': 'center'})
                for col_num, value in enumerate(df_resumo.columns.values): worksheet.write(0, col_num, value, fmt_header)
                worksheet.set_column('A:A', 25)
                worksheet.set_column('B:N', 10)
                if self.fig is not None:
                    ws_graficos = writer.book.add_worksheet('Gráficos')
                    img_io = io.BytesIO()
                    self.fig.savefig(img_io, format='png', bbox_inches='tight', dpi=100)
                    img_io.seek(0)
                    ws_graficos.insert_image('A1', 'grafico.png', {'image_data': img_io})
            messagebox.showinfo("Sucesso", "Excel Gerado!")
        except Exception as e: messagebox.showerror("Erro", str(e))

    # COMPONENTES UI
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

    def _desenhar_tabela(self, df_os):
        for w in self.frame_tabela.winfo_children(): w.destroy()
        if df_os.empty: return

        df_resumo = self._gerar_dataframe_resumo()
        container = ctk.CTkFrame(self.frame_tabela, fg_color=COLOR_WHITE, corner_radius=8, border_width=1, border_color="#E0E0E0")
        container.pack(fill="x", padx=5)

        header = ctk.CTkFrame(container, fg_color=COLOR_PRIMARY, corner_radius=6, height=35)
        header.pack(fill="x", padx=2, pady=2)
        for i, col in enumerate(df_resumo.columns):
            ctk.CTkLabel(header, text=col, font=("Arial Bold", 11), text_color="white", width=200 if i==0 else 50, anchor="w" if i==0 else "center").pack(side="left", fill="x", expand=True, padx=2)
        
        for idx, row in df_resumo.iloc[:-1].iterrows():
            row_frame = ctk.CTkFrame(container, fg_color="#F9F9F9" if idx % 2 == 0 else "#FFFFFF", corner_radius=0, height=28)
            row_frame.pack(fill="x", padx=2)
            for i, col in enumerate(df_resumo.columns):
                ctk.CTkLabel(row_frame, text=str(row[col]), font=("Arial Bold" if col=="TOTAL" else "Arial", 11), text_color="#000" if col=="TOTAL" else "#333", width=200 if i==0 else 50, anchor="w" if i==0 else "center").pack(side="left", fill="x", expand=True, padx=2)

        total_frame = ctk.CTkFrame(container, fg_color="#E0E4E8", corner_radius=0, height=35)
        total_frame.pack(fill="x", padx=2, pady=(0, 2))
        for i, col in enumerate(df_resumo.columns):
            ctk.CTkLabel(total_frame, text="TOTAL GERAL" if i==0 else str(df_resumo.iloc[-1][col]), font=("Arial Black", 12), text_color=COLOR_PRIMARY, width=200 if i==0 else 50, anchor="w" if i==0 else "center").pack(side="left", fill="x", expand=True, padx=2)

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
        self.df_os_raw, self.df_par_raw = self.service.carregar_dados_brutos()
        self.atualizar_dashboard()

    def atualizar_dashboard(self):
        try: ano_sel = int(self.cb_ano.get())
        except: ano_sel = datetime.now().year
        
        mes_str = self.cb_mes.get()
        mes_sel = int(mes_str.split(" - ")[0]) if mes_str != "Todos" else None

        self.df_os_f, self.df_par_f = self.service.filtrar_dados(self.df_os_raw, self.df_par_raw, ano_sel, mes_sel)

        # CARDS
        for w in self.frame_kpis.winfo_children(): w.destroy()
        c_os, c_par, c_def, c_indef = self.service.calcular_kpis(self.df_os_f, self.df_par_f)
        
        self.frame_kpis.columnconfigure((0,1,2,3), weight=1)
        self.criar_card(self.frame_kpis, "TOTAL OS (ITINERÁRIO)", f"{c_os}", COLOR_PRIMARY, "📋").grid(row=0, column=0, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES (ITINERÁRIO)", f"{c_par}", "#14B5D9", "📝").grid(row=0, column=1, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "DEFERIDOS", f"{c_def}", "#28a745", "✅").grid(row=0, column=2, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "INDEFERIDOS", f"{c_indef}", "#dc3545", "❌").grid(row=0, column=3, padx=8, sticky="ew")

        self._desenhar_tabela(self.df_os_f)

        # GRÁFICOS (3 Linhas x 2 Colunas)
        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        self.fig, axs = plt.subplots(3, 2, figsize=(14, 18), facecolor=COLOR_WHITE)
        self.fig.patch.set_facecolor(COLOR_WHITE)

        if self.df_os_f.empty and self.df_par_f.empty:
            axs[0,0].text(0.5, 0.5, "Sem dados para o filtro", ha='center', fontsize=14)
        else:
            meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            meses_en = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

            # LINHA 1: Evolução
            ax = axs[0, 0]
            if not self.df_os_f.empty:
                counts = self.df_os_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0)
                bars = ax.bar(meses_pt, counts.values, color=COLOR_PRIMARY, width=0.6)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h, f'{int(h)}', ha='center', va='bottom', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, f"Evolução de OS ({ano_sel})", grid_axis='y')

            ax = axs[0, 1]
            if not self.df_par_f.empty:
                counts = self.df_par_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0)
                bars = ax.bar(meses_pt, counts.values, color="#17a2b8", width=0.6)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h, f'{int(h)}', ha='center', va='bottom', fontweight='bold', color="#17a2b8")
            self._configurar_eixo(ax, f"Evolução de Pareceres ({ano_sel})", grid_axis='y')

            # LINHA 2: Solicitantes e OS por Usuário
            ax = axs[1, 0]
            if not self.df_par_f.empty and 'solicitante' in self.df_par_f.columns:
                counts = self.df_par_f['solicitante'].replace("", "Não Informado").fillna("Não Informado").value_counts().head(10)
                labels = [textwrap.fill(str(nome), width=25) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color=COLOR_SECONDARY)
                ax.invert_yaxis()
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_SECONDARY)
            self._configurar_eixo(ax, "Top 10 Solicitantes (Pareceres)", grid_axis='x')

            ax = axs[1, 1]
            if not self.df_os_f.empty and 'criado_por' in self.df_os_f.columns:
                counts = self.df_os_f['criado_por'].value_counts().head(10)
                labels = [textwrap.fill(str(nome), width=20) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color=COLOR_PRIMARY)
                ax.invert_yaxis()
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, "Quantidade de OS por Técnico", grid_axis='x')

            # LINHA 3: Pareceres por Usuário e Produtividade
            ax = axs[2, 0]
            if not self.df_par_f.empty and 'criado_por' in self.df_par_f.columns:
                counts = self.df_par_f['criado_por'].value_counts().head(10)
                labels = [textwrap.fill(str(nome), width=20) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color="#14B5D9")
                ax.invert_yaxis()
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color="#14B5D9")
            self._configurar_eixo(ax, "Quantidade de Pareceres por Técnico", grid_axis='x')

            ax = axs[2, 1]
            s1 = self.df_os_f['criado_por'].value_counts() if not self.df_os_f.empty else pd.Series(dtype=int)
            s2 = self.df_par_f['criado_por'].value_counts() if not self.df_par_f.empty else pd.Series(dtype=int)
            prod_total = s1.add(s2, fill_value=0).sort_values(ascending=False).head(10)
            
            if not prod_total.empty:
                labels = [textwrap.fill(str(nome), width=20) for nome in prod_total.index]
                bars = ax.barh(labels, prod_total.values, color=COLOR_SECONDARY)
                ax.invert_yaxis()
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w, bar.get_y() + bar.get_height()/2, f' {int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_SECONDARY)
            self._configurar_eixo(ax, "Top Produtividade Relativa (OS + Parecer)", grid_axis='x')

        self.fig.tight_layout(pad=4.0, h_pad=5.0)
        canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def renderizar(frame_destino, usuario_logado):
    return DashboardItinerarioView(master=frame_destino, usuario_logado=usuario_logado)