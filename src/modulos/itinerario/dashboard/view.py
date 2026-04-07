import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
import textwrap
import numpy as np
import io
import os
from datetime import datetime
from tkinter import filedialog, messagebox
from src.modulos.itinerario.dashboard.service import DashboardItinerarioService
from src.modulos.itinerario.dashboard.repository import DashboardItinerarioRepository

# --- Cores Padrão (Verde e Laranja) ---
COLOR_PRIMARY = "#0F8C75"     
COLOR_SECONDARY = "#F24822"   
COLOR_BG = "#F8F9FA"          
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
        self.fig = None # Para exportação

        self._construir_interface()
        self.atualizar_completo()

    def _construir_interface(self):
        # Topo com Filtros e Exportação
        frame_topo = ctk.CTkFrame(self, fg_color=COLOR_CARD_BG, height=70, corner_radius=0)
        frame_topo.pack(fill="x", side="top")
        frame_topo.pack_propagate(False)
        
        ctk.CTkLabel(frame_topo, text="DASHBOARD ITINERÁRIO", font=("Arial Black", 18), text_color=COLOR_PRIMARY).pack(side="left", padx=20, pady=20)
        
        # Botões de Exportação
        self.btn_pdf = ctk.CTkButton(frame_topo, text="📄 PDF", font=("Arial Bold", 13), fg_color=COLOR_SECONDARY, width=80, height=35, command=self.exportar_pdf)
        self.btn_pdf.pack(side="right", padx=10, pady=17)

        self.btn_excel = ctk.CTkButton(frame_topo, text="📥 EXCEL", font=("Arial Bold", 13), fg_color="#28A745", width=90, height=35, command=self.exportar_excel)
        self.btn_excel.pack(side="right", padx=5, pady=17)

        # Filtros
        ctk.CTkButton(frame_topo, text="🔄 Atualizar", fg_color=COLOR_PRIMARY, font=("Arial Bold", 13), width=100, height=35, command=self.atualizar_completo).pack(side="right", padx=20)
        
        self.cb_ano = ctk.CTkComboBox(frame_topo, values=[str(a) for a in range(2024, 2030)], width=100, height=35)
        self.cb_ano.set(str(datetime.now().year))
        self.cb_ano.pack(side="right", padx=10)
        ctk.CTkLabel(frame_topo, text="Ano:", text_color="#555", font=("Arial Bold", 13)).pack(side="right")

        # Scroll principal
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_cards = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_cards.pack(fill="x", pady=(0, 15))

        self.frame_tabelas = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_tabelas.pack(fill="x", pady=10)

        self.frame_graficos = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.frame_graficos.pack(fill="both", expand=True, pady=10)

    def exportar_pdf(self):
        if self.fig is None: return messagebox.showwarning("Aviso", "Não há gráficos para exportar.")
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if filepath:
            try:
                with PdfPages(filepath) as pdf:
                    pdf.savefig(self.fig, bbox_inches='tight', pad_inches=0.3)  
                messagebox.showinfo("Sucesso", "Relatório PDF Gerado!")
                os.startfile(filepath)
            except Exception as e: messagebox.showerror("Erro", str(e))

    def exportar_excel(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not filepath: return
        try:
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                if not self.df_os_f.empty: self.df_os_f.to_excel(writer, sheet_name='OS_Itinerario', index=False)
                if not self.df_par_f.empty: self.df_par_f.to_excel(writer, sheet_name='Pareceres_Itinerario', index=False)
                
                if self.fig is not None:
                    ws_graficos = writer.book.add_worksheet('Graficos')
                    img_io = io.BytesIO()
                    self.fig.savefig(img_io, format='png', bbox_inches='tight', dpi=100)
                    img_io.seek(0)
                    ws_graficos.insert_image('A1', 'grafico.png', {'image_data': img_io})
            messagebox.showinfo("Sucesso", "Ficheiro Excel gerado com sucesso!")
            os.startfile(filepath)
        except Exception as e: messagebox.showerror("Erro", str(e))

    def criar_tabela(self, parent, titulo, headers, dados):
        container = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=10, border_width=1, border_color="#E0E0E0")
        container.pack(side="left", fill="both", expand=True, padx=8)
        
        ctk.CTkLabel(container, text=titulo, font=("Arial Bold", 13), text_color=COLOR_PRIMARY).pack(pady=10)
        
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
        
        ctk.CTkFrame(container, fg_color="transparent", height=10).pack()

    def atualizar_completo(self):
        self.df_os_raw, self.df_par_raw = self.service.carregar_dados_brutos()
        self.renderizar_conteudo()

    def renderizar_conteudo(self):
        try: ano = int(self.cb_ano.get())
        except: ano = datetime.now().year
        
        self.df_os_f, self.df_par_f = self.service.filtrar_dados(self.df_os_raw, self.df_par_raw, ano)

        # 1. RENDERIZAR CARDS
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

        add_card("TOTAL OS", c_os, COLOR_PRIMARY)
        add_card("TOTAL PARECERES", c_par, COLOR_PRIMARY)
        add_card("DEFERIDOS", c_def, "#28A745")
        add_card("INDEFERIDOS", c_indef, COLOR_SECONDARY)

        # 2. RENDERIZAR TABELAS MENSAIS
        for w in self.frame_tabelas.winfo_children(): w.destroy()
        try:
            tab_par = self.service.preparar_tabela_mensal_pareceres(self.df_par_f)
            tab_os = self.service.preparar_tabela_mensal_os(self.df_os_f)
        except:
            tab_par, tab_os = [], [] 
        
        self.criar_tabela(self.frame_tabelas, "BALANÇO MENSAL DE PARECERES", ["Mês", "Deferidos", "Indeferidos", "Total"], tab_par)
        self.criar_tabela(self.frame_tabelas, "CATEGORIZAÇÃO MENSAL DE OS", ["Mês", "Eventos", "Corridas", "Obras", "Outros", "Total"], tab_os)

        # 3. RENDERIZAR GRÁFICOS
        self.renderizar_graficos(self.df_os_f, self.df_par_f)

    def _configurar_eixo(self, ax, titulo):
        ax.set_title(titulo, fontsize=11, fontweight='bold', color=COLOR_TEXT, pad=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#DDDDDD')
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(colors='#555555', labelsize=8)
        ax.grid(axis='y', linestyle='--', alpha=0.3, color='#DDDDDD') 
        ax.set_facecolor(COLOR_CARD_BG)

    def renderizar_graficos(self, df_os_f, df_par_f):
        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        self.fig, axs = plt.subplots(3, 2, figsize=(14, 16), facecolor=COLOR_BG)
        self.fig.patch.set_facecolor(COLOR_BG)
        plt.subplots_adjust(hspace=0.5, wspace=0.2)
        
        def plot_bar(ax, x, y, title, color):
            ax.bar(x, y, color=color, width=0.4)
            self._configurar_eixo(ax, title)
            if len(x) > 0 and isinstance(x[0], str):
                ax.tick_params(axis='x', rotation=45)

        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        os_m = pd.Series(0, index=range(1,13))
        if not df_os_f.empty and 'data_dt' in df_os_f.columns:
            os_valid = df_os_f.dropna(subset=['data_dt'])
            if not os_valid.empty: os_m = os_valid['data_dt'].dt.month.value_counts().reindex(range(1,13), fill_value=0)
        
        par_m = pd.Series(0, index=range(1,13))
        if not df_par_f.empty and 'data_dt' in df_par_f.columns:
            par_valid = df_par_f.dropna(subset=['data_dt'])
            if not par_valid.empty: par_m = par_valid['data_dt'].dt.month.value_counts().reindex(range(1,13), fill_value=0)

        # Gráficos 1 e 2
        plot_bar(axs[0,0], meses, os_m.values, "EVOLUÇÃO MENSAL DE OS", COLOR_PRIMARY)
        plot_bar(axs[0,1], meses, par_m.values, "EVOLUÇÃO MENSAL DE PARECERES", COLOR_SECONDARY)

        # Gráfico 3
        if not df_par_f.empty and 'solicitante' in df_par_f.columns:
            solic = df_par_f['solicitante'].value_counts().head(10)
            labels = [textwrap.fill(str(s), 12) for s in solic.index]
            plot_bar(axs[1,0], labels, solic.values, "TOP 10 SOLICITANTES (PARECERES)", "#555555")
        else:
            self._configurar_eixo(axs[1,0], "TOP 10 SOLICITANTES (PARECERES)")

        u_os = df_os_f['criado_por'].value_counts() if not df_os_f.empty else pd.Series(dtype=int)
        u_par = df_par_f['criado_por'].value_counts() if not df_par_f.empty else pd.Series(dtype=int)
        total_prod = u_os.add(u_par, fill_value=0).sort_values(ascending=False).head(7)

        # Gráfico 4
        if not total_prod.empty:
            x = np.arange(len(total_prod))
            width = 0.35 
            val_os = [u_os.get(u, 0) for u in total_prod.index]
            val_par = [u_par.get(u, 0) for u in total_prod.index]
            
            axs[1,1].bar(x - width/2, val_os, width, label='OS', color=COLOR_PRIMARY)
            axs[1,1].bar(x + width/2, val_par, width, label='Parecer', color=COLOR_SECONDARY)
            axs[1,1].set_xticks(x)
            axs[1,1].set_xticklabels([textwrap.fill(str(u), 10) for u in total_prod.index], rotation=45)
            axs[1,1].legend(fontsize=9)
            self._configurar_eixo(axs[1,1], "COMPARAÇÃO DE PRODUTIVIDADE: OS vs PARECER")
        else:
            self._configurar_eixo(axs[1,1], "COMPARAÇÃO DE PRODUTIVIDADE: OS vs PARECER")

        # Gráfico 5
        if not total_prod.empty:
            labels = [textwrap.fill(str(u), 12) for u in total_prod.index]
            plot_bar(axs[2,0], labels, total_prod.values, "PRODUTIVIDADE TOTAL (OS + PARECER)", COLOR_PRIMARY)
        else:
            self._configurar_eixo(axs[2,0], "PRODUTIVIDADE TOTAL (OS + PARECER)")

        # Gráfico 6: PRODUTIVIDADE RELATIVA (COM STATUS E MÉDIA IDEAL)
        if not total_prod.empty:
            total_geral = total_prod.sum()
            media_ideal = total_geral / len(total_prod)
            
            labels_prod = []
            cores_prod = []
            
            for u, val in total_prod.items():
                labels_prod.append(textwrap.fill(str(u), 12))
                # Define cor pelo status (Verde = Acima/Ideal | Laranja/Vermelho = Abaixo)
                if val >= media_ideal:
                    cores_prod.append(COLOR_PRIMARY) 
                else:
                    cores_prod.append(COLOR_SECONDARY)

            bars = axs[2,1].bar(labels_prod, total_prod.values, color=cores_prod, width=0.4)
            self._configurar_eixo(axs[2,1], "PRODUTIVIDADE RELATIVA: ANÁLISE DE DESEMPENHO")
            
            # Linha da Produtividade Ideal
            axs[2,1].axhline(y=media_ideal, color='#333333', linestyle='--', linewidth=1.5, label=f'Produtividade Ideal: {media_ideal:.1f}')
            axs[2,1].legend(fontsize=9, loc="upper right")
            
            # Textos em cima da barra (Quantidade, %, Status)
            for bar, val in zip(bars, total_prod.values):
                pct = (val / total_geral) * 100 if total_geral > 0 else 0
                status_txt = "Acima" if val > media_ideal else "Ideal" if val == media_ideal else "Abaixo"
                
                texto_anotacao = f"{int(val)} ({pct:.1f}%)\\n[{status_txt}]"
                axs[2,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + (total_prod.max() * 0.02), 
                              texto_anotacao, ha='center', va='bottom', fontsize=8, fontweight='bold', color='#444444')
                
            axs[2,1].set_ylim(0, total_prod.max() * 1.25) # Dá espaço para o texto
            axs[2,1].tick_params(axis='x', rotation=45)
        else:
            self._configurar_eixo(axs[2,1], "PRODUTIVIDADE RELATIVA: ANÁLISE DE DESEMPENHO")
            
        canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def renderizar(frame_destino, usuario_logado):
    return DashboardItinerarioView(master=frame_destino, usuario_logado=usuario_logado)