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
from src.dashboard.service import DashboardService

# --- Paleta de Cores Institucional ---
COLOR_BG = "#F4F6F9"          
COLOR_WHITE = "#FFFFFF"       
COLOR_PRIMARY = "#0F8C75"     # Verde Petróleo
COLOR_SECONDARY = "#F24822"   # Laranja/Vermelho
COLOR_TEXT = "#333333"
COLOR_WARNING = "#F29C1F"     # Amarelo (Apenas para exceções)


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardService()
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

        ctk.CTkLabel(frame_filtros, text="Painel Analítico Gerencial", font=("Arial Black", 22), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)
        
        # Botões de Ação (Exportar PDF, Exportar Excel, Atualizar)
        self.btn_pdf = ctk.CTkButton(frame_filtros, text="📄 PDF", font=("Arial Bold", 13), fg_color=COLOR_SECONDARY, hover_color="#D33F1D", width=70, height=35, command=self.exportar_pdf)
        self.btn_pdf.pack(side="right", padx=10, pady=17)

        self.btn_excel = ctk.CTkButton(frame_filtros, text="📥 EXCEL", font=("Arial Bold", 13), fg_color=COLOR_PRIMARY, hover_color="#0B6B59", width=80, height=35, command=self.exportar_excel)
        self.btn_excel.pack(side="right", padx=5, pady=17)

        self.btn_filtrar = ctk.CTkButton(frame_filtros, text="🔍 ATUALIZAR", font=("Arial Bold", 13), fg_color=COLOR_PRIMARY, hover_color="#0B6B59", width=110, height=35, command=self.atualizar_completo)
        self.btn_filtrar.pack(side="right", padx=(20, 5), pady=17)

        # Filtros de Ano e Mês
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

    # INTELIGÊNCIA DE EXPORTAÇÃO
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
        
        total_row = {"OPERAÇÃO / PONTO DE PARADA": "TOTAL GERAL"}
        for col in meses_pt + ["TOTAL"]:
            total_row[col] = df_resumo[col].sum()
        df_resumo.loc[len(df_resumo)] = total_row

        return df_resumo

    def exportar_pdf(self):
        if self.fig is None:
            messagebox.showwarning("Aviso", "Não há gráficos para exportar.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Arquivo PDF", "*.pdf")], title="Salvar Relatório em PDF")
        if filepath:
            try:
                df_resumo = self._gerar_dataframe_resumo()
                
                fig_table, ax_table = plt.subplots(figsize=(16, 9), facecolor='#FFFFFF')
                fig_table.patch.set_facecolor('#FFFFFF')
                ax_table.axis('off')
                
                fig_table.suptitle("Resumo Consolidado de Intervenções (OS)", fontsize=22, fontweight='bold', color="#333333", y=0.92)
                
                cell_text = []
                for row in df_resumo.values:
                    formatted_row = [row[0]] + [str(int(x)) if x == int(x) else str(x) for x in row[1:]]
                    cell_text.append(formatted_row)

                table = ax_table.table(cellText=cell_text, colLabels=df_resumo.columns, cellLoc='center', loc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(11) 
                table.scale(1, 1.8) 
                
                for (row, col), cell in table.get_celld().items():
                    if row == 0: 
                        cell.set_text_props(weight='bold', color='white')
                        cell.set_facecolor(COLOR_PRIMARY) 
                    elif row == len(df_resumo): 
                        cell.set_text_props(weight='bold')
                        cell.set_facecolor('#E0E4E8')
                    
                    if col == 0: 
                        cell._loc = 'left' 
                        cell.set_width(0.38) 
                    else:
                        cell.set_width(0.045) 

                fig_table.tight_layout(rect=[0.05, 0.05, 0.98, 0.88])

                with PdfPages(filepath) as pdf:
                    pdf.savefig(fig_table, bbox_inches='tight', pad_inches=0.3) 
                    pdf.savefig(self.fig, bbox_inches='tight', pad_inches=0.3)  
                    
                plt.close(fig_table)
                messagebox.showinfo("Sucesso", "Relatório Executivo PDF gerado com sucesso!\n\nPágina 1: Tabela Resumo\nPágina 2: Gráficos Analíticos")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar PDF:\n{e}")

    def exportar_excel(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Planilha Excel", "*.xlsx")], title="Salvar Relatório em Excel")
        if not filepath: return

        try:
            df_resumo = self._gerar_dataframe_resumo()
            
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                df_resumo.to_excel(writer, sheet_name='Resumo_Produção', index=False)
                worksheet = writer.sheets['Resumo_Produção']
                
                header_format = workbook.add_format({'bold': True, 'bg_color': COLOR_PRIMARY, 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                cell_format = workbook.add_format({'border': 1, 'align': 'center'})
                first_col_format = workbook.add_format({'border': 1, 'align': 'left'})
                total_format = workbook.add_format({'bold': True, 'bg_color': '#E0E4E8', 'border': 1, 'align': 'center'})
                total_first_col = workbook.add_format({'bold': True, 'bg_color': '#E0E4E8', 'border': 1, 'align': 'left'})
                
                for col_num, value in enumerate(df_resumo.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                worksheet.set_column('A:A', 38, first_col_format) 
                worksheet.set_column('B:N', 9, cell_format)       
                
                last_row_idx = len(df_resumo)
                worksheet.write(last_row_idx, 0, df_resumo.iloc[-1, 0], total_first_col)
                for col_num in range(1, len(df_resumo.columns)):
                    worksheet.write(last_row_idx, col_num, df_resumo.iloc[-1, col_num], total_format)
                
                if not self.df_os_f.empty:
                    df_os_export = self.df_os_f.copy()
                    df_os_export['data_dt'] = df_os_export['data_dt'].dt.strftime('%d/%m/%Y')
                    df_os_export.to_excel(writer, sheet_name='Dados_Brutos_OS', index=False)
                
                if not self.df_par_f.empty:
                    df_par_export = self.df_par_f.copy()
                    df_par_export['data_dt'] = df_par_export['data_dt'].dt.strftime('%d/%m/%Y')
                    df_par_export.to_excel(writer, sheet_name='Dados_Brutos_Parecer', index=False)
                
                if self.fig is not None:
                    ws_graficos = workbook.add_worksheet('Gráficos_Individuais')
                    renderer = self.fig.canvas.get_renderer()
                    linha_atual = 1
                    
                    for i, ax in enumerate(self.fig.axes):
                        if ax.has_data() or len(ax.patches) > 0 or len(ax.lines) > 0:
                            bbox = ax.get_tightbbox(renderer).transformed(self.fig.dpi_scale_trans.inverted())
                            img_io = io.BytesIO()
                            self.fig.savefig(img_io, format='png', bbox_inches=bbox, dpi=120) 
                            img_io.seek(0)
                            
                            coluna = 'A' if i % 2 == 0 else 'I'
                            ws_graficos.insert_image(f'{coluna}{linha_atual}', 'grafico.png', {'image_data': img_io})
                            if i % 2 != 0: linha_atual += 22 

            messagebox.showinfo("Sucesso", "Planilha Excel Gerada e Formatada com Sucesso!")
        except Exception as e:
            messagebox.showerror("Erro de Exportação", f"Erro ao gerar o arquivo Excel:\n{e}")

    # RENDERIZAÇÃO DE COMPONENTES UI
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

    def _desenhar_tabela(self, df_os):
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
        
        # Corpo da Tabela
        for idx, row in df_corpo.iterrows():
            bg_color = "#F9F9F9" if idx % 2 == 0 else "#FFFFFF"
            row_frame = ctk.CTkFrame(container, fg_color=bg_color, corner_radius=0, height=28)
            row_frame.pack(fill="x", padx=2)
            for i, col in enumerate(df_corpo.columns):
                largura = 280 if i == 0 else 50
                val = row[col]
                
                if i == 0: 
                    texto_val = str(val)
                else:
                    texto_val = str(int(val)) if val > 0 and val == int(val) else str(val) if val > 0 else "-"
                
                ctk.CTkLabel(row_frame, text=texto_val, font=("Arial Bold" if col=="TOTAL" else "Arial", 11), text_color="#000" if col=="TOTAL" else "#333", anchor="w" if i==0 else "center", width=largura).pack(side="left", fill="x", expand=True, padx=(10 if i==0 else 1))

        total_frame = ctk.CTkFrame(container, fg_color="#E0E4E8", corner_radius=0, height=35)
        total_frame.pack(fill="x", padx=2, pady=(0, 2))
        for i, col in enumerate(df_resumo.columns):
            largura = 280 if i == 0 else 50
            val = linha_total[col]
            
            if i == 0: 
                texto_val = "TOTAL GERAL POR MÊS"
            else:
                texto_val = str(int(val)) if val == int(val) else str(val)
                
            ctk.CTkLabel(total_frame, text=texto_val, font=("Arial Black", 12), text_color=COLOR_PRIMARY, anchor="w" if i==0 else "center", width=largura).pack(side="left", fill="x", expand=True, padx=(10 if i==0 else 1))

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
        self.criar_card(self.frame_kpis, "TOTAL DE ORDENS (OS)", f"{c_os}", COLOR_PRIMARY, "📋").grid(row=0, column=0, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "TOTAL DE PARECERES", f"{c_par}", COLOR_SECONDARY, "📝").grid(row=0, column=1, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES DEFERIDOS", f"{c_def}", COLOR_PRIMARY, "✅").grid(row=0, column=2, padx=8, sticky="ew")
        self.criar_card(self.frame_kpis, "PARECERES INDEFERIDOS", f"{c_indef}", COLOR_SECONDARY, "❌").grid(row=0, column=3, padx=8, sticky="ew")

        # TABELA
        self._desenhar_tabela(self.df_os_f)

        # GRÁFICOS
        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        self.fig, axs = plt.subplots(7, 2, figsize=(14, 40), facecolor=COLOR_WHITE)
        self.fig.patch.set_facecolor(COLOR_WHITE)

        if self.df_os_f.empty and self.df_par_f.empty:
            axs[0,0].text(0.5, 0.5, "Sem dados para o filtro selecionado", ha='center', fontsize=14)
        else:
            meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            meses_en = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

            # Evolução Mensal
            ax = axs[0, 0]
            if not self.df_os_f.empty:
                counts = self.df_os_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0)
                counts.index = meses_pt
                bars = ax.bar(counts.index, counts.values, color=COLOR_PRIMARY, width=0.6)
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_ylim(0, max_val * 1.15)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + (max_val*0.02), f'{int(h)}', ha='center', va='bottom', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, f"Evolução de OS ({ano_sel})", grid_axis='y')

            ax = axs[0, 1]
            if not self.df_par_f.empty:
                counts = self.df_par_f['data_dt'].dt.month_name().value_counts().reindex(meses_en, fill_value=0)
                counts.index = meses_pt
                bars = ax.bar(counts.index, counts.values, color=COLOR_SECONDARY, width=0.6)
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_ylim(0, max_val * 1.15)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + (max_val*0.02), f'{int(h)}', ha='center', va='bottom', fontweight='bold', color=COLOR_SECONDARY)
            self._configurar_eixo(ax, f"Evolução de Pareceres  ({ano_sel})", grid_axis='y')

            # Bairros e Solicitantes
            ax = axs[1, 0]
            if not self.df_os_f.empty and 'bairro' in self.df_os_f.columns:
                counts = self.df_os_f['bairro'].replace("", "Não Informado").fillna("Não Informado").value_counts().head(8)
                labels = [textwrap.fill(str(nome), width=25) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color=COLOR_PRIMARY)
                ax.invert_yaxis()
                ax.xaxis.set_major_locator(MaxNLocator(integer=True)) 
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_xlim(0, max_val * 1.2)
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w + (max_val*0.02), bar.get_y() + bar.get_height()/2, f'{int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, "Top 8 Bairros com Mais OS", grid_axis='x')

            ax = axs[1, 1]
            if not self.df_par_f.empty and 'solicitante' in self.df_par_f.columns:
                counts = self.df_par_f['solicitante'].replace("", "Não Informado").fillna("Não Informado").value_counts().head(8)
                labels = [textwrap.fill(str(nome), width=25) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color=COLOR_SECONDARY)
                ax.invert_yaxis()
                ax.xaxis.set_major_locator(MaxNLocator(integer=True)) 
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_xlim(0, max_val * 1.25) 
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w + (max_val*0.02), bar.get_y() + bar.get_height()/2, f'{int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_SECONDARY)
            self._configurar_eixo(ax, "Top 8 Solicitantes (Pareceres)", grid_axis='x')

            # Status (ATUALIZADO COM NÚMERO E PORCENTAGEM)
            ax = axs[2, 0]
            if not self.df_os_f.empty and 'status_conclusao' in self.df_os_f.columns:
                status_counts = self.df_os_f['status_conclusao'].fillna("NÃO").value_counts()
                if not status_counts.empty:
                    cores_map = {"SIM": COLOR_PRIMARY, "NÃO": COLOR_SECONDARY, "NÃO AUTORIZADA": COLOR_WARNING}
                    cores_grafico = [cores_map.get(str(x).upper(), "#999999") for x in status_counts.index]
                    
                    formato_rotulo = lambda p: f'{int(round(p * sum(status_counts.values) / 100))}\n({p:.1f}%)'
                    ax.pie(status_counts.values, labels=status_counts.index, autopct=formato_rotulo, startangle=90, colors=cores_grafico, textprops={'fontsize': 10, 'fontweight': 'bold'}, wedgeprops=dict(width=0.4, edgecolor='w'))
                    ax.set_title("Status das Ordens de Serviço", fontsize=12, fontweight='bold', color=COLOR_TEXT, pad=15)
            else:
                self._configurar_eixo(ax, "Status das Ordens de Serviço")
                ax.text(0.5, 0.5, "Sem dados", ha='center')

            ax = axs[2, 1]
            if not self.df_par_f.empty and 'tipo' in self.df_par_f.columns:
                taxa_counts = self.df_par_f['tipo'].str.upper().value_counts()
                if not taxa_counts.empty:
                    cores_map = {"DEFERIDO": COLOR_PRIMARY, "INDEFERIDO": COLOR_SECONDARY}
                    cores_grafico = [cores_map.get(str(x), "#999999") for x in taxa_counts.index]
                    
                    formato_rotulo = lambda p: f'{int(round(p * sum(taxa_counts.values) / 100))}\n({p:.1f}%)'
                    ax.pie(taxa_counts.values, labels=taxa_counts.index, autopct=formato_rotulo, startangle=90, colors=cores_grafico, textprops={'fontsize': 10, 'fontweight': 'bold'}, wedgeprops=dict(width=0.4, edgecolor='w'))
                    ax.set_title("Taxa de Aprovação (Pareceres)", fontsize=12, fontweight='bold', color=COLOR_TEXT, pad=15)
            else:
                self._configurar_eixo(ax, "Taxa de Aprovação (Pareceres)")
                ax.text(0.5, 0.5, "Sem dados", ha='center')

            # Natureza e Tipo
            ax = axs[3, 0]
            if not self.df_os_f.empty and 'tipo_os' in self.df_os_f.columns:
                counts = self.df_os_f['tipo_os'].str.upper().value_counts().head(5)
                labels = [textwrap.fill(str(nome), width=12) for nome in counts.index]
                bars = ax.bar(labels, counts.values, color=COLOR_PRIMARY, width=0.5)
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_ylim(0, max_val * 1.2)
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + (max_val*0.02), f'{int(h)}', ha='center', va='bottom', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, "Natureza da Ação (OS)", grid_axis='y')

            ax = axs[3, 1]
            if not self.df_os_f.empty and 'tipo_item' in self.df_os_f.columns:
                counts = self.df_os_f['tipo_item'].str.upper().value_counts().head(5)
                labels = [textwrap.fill(str(nome), width=15) for nome in counts.index] 
                bars = ax.bar(labels, counts.values, color=COLOR_SECONDARY, width=0.5)
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_ylim(0, max_val * 1.2)
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
                for bar in bars:
                    h = bar.get_height()
                    if h > 0: ax.text(bar.get_x() + bar.get_width()/2, h + (max_val*0.02), f'{int(h)}', ha='center', va='bottom', fontweight='bold', color=COLOR_SECONDARY)
            self._configurar_eixo(ax, "Tipos de Itens Mais Demandados (OS)", grid_axis='y')

            # Produção Individual
            ax = axs[4, 0]
            if not self.df_os_f.empty and 'criado_por' in self.df_os_f.columns:
                counts = self.df_os_f['criado_por'].value_counts().head(8)
                labels = [textwrap.fill(str(nome), width=20) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color=COLOR_PRIMARY)
                ax.invert_yaxis()
                ax.xaxis.set_major_locator(MaxNLocator(integer=True)) 
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_xlim(0, max_val * 1.25)
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w + (max_val*0.02), bar.get_y() + bar.get_height()/2, f'{int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, "Quantidade de OS por Técnico", grid_axis='x')

            ax = axs[4, 1]
            if not self.df_par_f.empty and 'criado_por' in self.df_par_f.columns:
                counts = self.df_par_f['criado_por'].value_counts().head(8)
                labels = [textwrap.fill(str(nome), width=20) for nome in counts.index]
                bars = ax.barh(labels, counts.values, color=COLOR_SECONDARY)
                ax.invert_yaxis()
                ax.xaxis.set_major_locator(MaxNLocator(integer=True)) 
                max_val = max(counts.values) if len(counts)>0 else 1
                ax.set_xlim(0, max_val * 1.25)
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w + (max_val*0.02), bar.get_y() + bar.get_height()/2, f'{int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_SECONDARY)
            self._configurar_eixo(ax, "Quantidade de Pareceres por Técnico", grid_axis='x')

            # Produtividade
            ax = axs[5, 0]
            s1 = self.df_os_f['criado_por'].value_counts() if not self.df_os_f.empty else pd.Series(dtype=int)
            s2 = self.df_par_f['criado_por'].value_counts() if not self.df_par_f.empty else pd.Series(dtype=int)
            prod_total = s1.add(s2, fill_value=0).sort_values(ascending=False).head(8)
            total_geral_sistema = len(self.df_os_f) + len(self.df_par_f)
            
            if not prod_total.empty:
                labels = [textwrap.fill(str(nome), width=20) for nome in prod_total.index]
                bars = ax.barh(labels, prod_total.values, color=COLOR_PRIMARY)
                ax.invert_yaxis()
                ax.xaxis.set_major_locator(MaxNLocator(integer=True)) 
                max_val = max(prod_total.values) if len(prod_total)>0 else 1
                ax.set_xlim(0, max_val * 1.25)
                for bar in bars:
                    w = bar.get_width()
                    if w > 0: ax.text(w + (max_val*0.02), bar.get_y() + bar.get_height()/2, f'{int(w)}', va='center', ha='left', fontweight='bold', color=COLOR_PRIMARY)
            self._configurar_eixo(ax, "Total por Técnico (OS + Parecer)", grid_axis='x')

            ax = axs[5, 1]
            if not prod_total.empty and total_geral_sistema > 0:
                labels = [textwrap.fill(str(nome), width=20) for nome in prod_total.index]
                prod_pct = (prod_total / total_geral_sistema) * 100
                bars = ax.barh(labels, prod_pct.values, color=COLOR_SECONDARY)
                ax.invert_yaxis()
                
                max_val = max(prod_pct.values) if len(prod_pct)>0 else 1
                ax.set_xlim(0, max_val * 1.90) 
                
                num_tecnicos = len(prod_total)
                media_docs = int(round(total_geral_sistema / num_tecnicos))
                media_pct = (media_docs / total_geral_sistema) * 100

                texto_legenda = f"Média Ideal da Equipe:\n{media_docs} Docs/Téc\n({media_pct:.1f}%)"
                ax.text(1.2, 0.03, texto_legenda, transform=ax.transAxes, ha='right', va='bottom',
                        fontsize=9, fontweight='bold', color='#333333',
                        bbox=dict(facecolor='#F4F6F9', alpha=0.9, edgecolor=COLOR_PRIMARY, boxstyle='round,pad=0.4'))

                for bar in bars:
                    w = bar.get_width() 
                    if w > 0: 
                        pct = w
                        diff = pct - media_pct
                        
                        if diff > 0.1:
                            status = f"Acima (+{diff:.1f}%)"
                            color_status = COLOR_PRIMARY 
                        elif diff < -0.1:
                            status = f"Abaixo ({diff:.1f}%)"
                            color_status = COLOR_SECONDARY 
                        else:
                            status = "Na Média"
                            color_status = "#777777" 
                            
                        texto_final = f"{pct:.1f}%  |  {status}"
                        ax.text(w + (max_val*0.03), bar.get_y() + bar.get_height()/2, texto_final, 
                                va='center', ha='left', fontweight='bold', color=color_status, fontsize=11)
            
            self._configurar_eixo(ax, "Produtividade Relativa vs Média da Equipe (%)", grid_axis='x')

            # ORIGEM DA DEMANDA
            ax = axs[6, 0]
            if not self.df_os_f.empty and 'origem' in self.df_os_f.columns:
                counts = self.df_os_f['origem'].value_counts()
                if not counts.empty:
                    cores_map = {"SPU": COLOR_PRIMARY, "SISGEP": COLOR_SECONDARY}
                    cores_grafico = [cores_map.get(str(x), COLOR_TEXT) for x in counts.index]
                    
                    formato_rotulo = lambda p: f'{int(round(p * sum(counts.values) / 100))}\n({p:.1f}%)'
                    ax.pie(counts.values, labels=counts.index, autopct=formato_rotulo, startangle=90, colors=cores_grafico, textprops={'fontsize': 10, 'fontweight': 'bold'}, wedgeprops=dict(width=0.4, edgecolor='w'))
                    ax.set_title("Origem da Demanda (OS)", fontsize=12, fontweight='bold', color=COLOR_TEXT, pad=15)
            else:
                self._configurar_eixo(ax, "Origem da Demanda (OS)")
                ax.text(0.5, 0.5, "Sem dados", ha='center')

            ax = axs[6, 1]
            if not self.df_par_f.empty and 'origem' in self.df_par_f.columns:
                counts = self.df_par_f['origem'].value_counts()
                if not counts.empty:
                    cores_map = {"SPU": COLOR_PRIMARY, "SISGEP": COLOR_SECONDARY}
                    cores_grafico = [cores_map.get(str(x), COLOR_TEXT) for x in counts.index]
                    
                    formato_rotulo = lambda p: f'{int(round(p * sum(counts.values) / 100))}\n({p:.1f}%)'
                    ax.pie(counts.values, labels=counts.index, autopct=formato_rotulo, startangle=90, colors=cores_grafico, textprops={'fontsize': 10, 'fontweight': 'bold'}, wedgeprops=dict(width=0.4, edgecolor='w'))
                    ax.set_title("Origem da Demanda (Pareceres)", fontsize=12, fontweight='bold', color=COLOR_TEXT, pad=15)
            else:
                self._configurar_eixo(ax, "Origem da Demanda (Pareceres)")
                ax.text(0.5, 0.5, "Sem dados", ha='center')

        self.fig.tight_layout(pad=4.0, h_pad=5.0)

        canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def renderizar(frame_destino, usuario_logado):
    return DashboardView(master=frame_destino, usuario_logado=usuario_logado)