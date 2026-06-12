import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
import textwrap
import os
from datetime import date
from tkcalendar import DateEntry
from tkinter import filedialog, messagebox

from src.modulos.projetos_mobilidade.dashboard.service import DashboardPMService
from src.modulos.projetos_mobilidade.dashboard.repository import DashboardPMRepository

from src.core.shared.colors import COLOR_PRIMARY, COLOR_BG, COLOR_WHITE, COLOR_HOVER, COLOR_TEXT, COLOR_SECONDARY

class DashboardPMView(ctk.CTkFrame):
    def __init__(self, master, usuario_logado):
        super().__init__(master, fg_color=COLOR_BG)
        self.pack(fill="both", expand=True)

        self.service = DashboardPMService(DashboardPMRepository())
        self.df_raw = pd.DataFrame()
        self.df_f = pd.DataFrame()
        
        self.fig = None
        self.axs = None

        self._construir_interface()
        self.atualizar_completo()

    def _criar_date_wrapper(self, parent, width):
        container = ctk.CTkFrame(parent, width=width, height=35, fg_color=COLOR_WHITE, border_width=1, border_color=COLOR_PRIMARY, corner_radius=6)
        container.pack_propagate(False) 
        date_entry = DateEntry(container, date_pattern="dd/mm/yyyy", font=("Arial", 11), background=COLOR_PRIMARY, foreground="white", borderwidth=0)
        date_entry.pack(fill="both", expand=True, padx=2, pady=2)
        return container, date_entry

    def _construir_interface(self):
        # TOP BAR
        topo = ctk.CTkFrame(self, fg_color=COLOR_BG, height=70, corner_radius=0)
        topo.pack(fill="x", side="top")
        topo.pack_propagate(False)

        ctk.CTkLabel(topo, text="DASHBOARD ESTRATÉGICO | PROJETOS DE MOBILIDADE", font=("Arial Black", 18), text_color=COLOR_PRIMARY).pack(side="left", padx=20)

        self.btn_exportar = ctk.CTkButton(topo, text="📄 Exportar PDF", font=("Arial Bold", 13), fg_color="#d41212", hover_color="#b40c0c", width=120, height=35, command=self.abrir_popup_exportacao)
        self.btn_exportar.pack(side="right", padx=10)

        ctk.CTkButton(topo, text="🔄 Atualizar", font=("Arial Bold", 12), fg_color=COLOR_PRIMARY, hover_color=COLOR_HOVER, width=100, height=35, command=self.atualizar_completo).pack(side="right", padx=20)

        self.btn_limpar_filtro = ctk.CTkButton(topo, text="Limpar Filtro", font=("Arial Bold", 13), fg_color="transparent", text_color=COLOR_PRIMARY, hover_color="#E9ECEF", border_width=1, border_color=COLOR_PRIMARY, width=110, height=35, command=self.limpar_filtros_data)
        self.btn_limpar_filtro.pack(side="right", padx=10)

        f_datas = ctk.CTkFrame(topo, fg_color="transparent")
        f_datas.pack(side="right", padx=10)
        
        ctk.CTkLabel(f_datas, text="Período:", font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(side="left", padx=5)
        w_ini, self.data_ini = self._criar_date_wrapper(f_datas, 110)
        self.data_ini.set_date(date(date.today().year, 1, 1))
        w_ini.pack(side="left", padx=2)
        
        ctk.CTkLabel(f_datas, text="até", font=("Arial Bold", 12), text_color=COLOR_TEXT).pack(side="left", padx=5)
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

    def limpar_filtros_data(self):
        hoje = date.today()
        self.data_ini.set_date(date(hoje.year, 1, 1))
        self.data_fim.set_date(hoje)
        self.atualizar_completo()

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
        c = ctk.CTkFrame(self.frame_cards, fg_color=COLOR_BG, height=90, corner_radius=10, border_width=1, border_color="#E0E0E0")
        c.pack(side="left", fill="x", expand=True, padx=8)
        c.pack_propagate(False)
        ctk.CTkFrame(c, fg_color=cor, width=6, corner_radius=10).pack(side="left", fill="y")
        ctk.CTkLabel(c, text=tit, font=("Arial Bold", 11), text_color=COLOR_TEXT).pack(anchor="w", padx=15, pady=(4,0))
        ctk.CTkLabel(c, text=str(val), font=("Arial Black", 18), text_color=COLOR_TEXT).pack(anchor="w", padx=15, pady=(0,2))

    def _criar_tabela_balanco(self, parent, titulo, headers, dados):
        container = ctk.CTkFrame(parent, fg_color=COLOR_BG, corner_radius=10, border_width=1, border_color="#E0E0E0")
        container.pack(fill="x", padx=8)
        ctk.CTkLabel(container, text=titulo, font=("Arial Bold", 14), text_color=COLOR_PRIMARY).pack(pady=10)
        
        h_frame = ctk.CTkFrame(container, fg_color="#F1F3F5", height=35)
        h_frame.pack(fill="x", padx=15, pady=5)
        for i, h in enumerate(headers):
            h_frame.columnconfigure(i, weight=1, uniform="col")
            ctk.CTkLabel(h_frame, text=h, font=("Arial Bold", 11), text_color=COLOR_TEXT).grid(row=0, column=i, pady=5, sticky="nsew")

        for r_idx, row in enumerate(dados):
            r_f = ctk.CTkFrame(container, fg_color="transparent")
            r_f.pack(fill="x", padx=15)
            for c_idx, v in enumerate(row):
                r_f.columnconfigure(c_idx, weight=1, uniform="col")
                ctk.CTkLabel(r_f, text=str(v), font=("Arial", 12), text_color=COLOR_TEXT).grid(row=0, column=c_idx, pady=3, sticky="nsew")

    def _renderizar_graficos(self):
        for w in self.frame_graficos.winfo_children(): w.destroy()
        
        fig, axs = plt.subplots(2, 2, figsize=(14, 12), facecolor=COLOR_BG)
        self.fig = fig
        self.axs = axs
        
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
                       startangle=90, colors=plt.cm.Oranges(np.linspace(0.5, 0.7, len(assuntos))), textprops={'fontweight':'bold'})
        ax.set_title("Top 5 Assuntos Demandados", fontsize=12, fontweight='bold', pad=15)

        canvas = FigureCanvasTkAgg(self.fig, master=self.frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _formatar_eixo(self, ax, titulo, eixo_int):
        ax.set_title(titulo, fontsize=12, fontweight='bold', pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        if eixo_int == 'y': ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        else: ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_facecolor(COLOR_BG)
        ax.grid(axis=eixo_int, linestyle='--', alpha=0.3)

    # --- MÉTODOS DE EXPORTAÇÃO EXECUTIVA ---
    def abrir_popup_exportacao(self):
        if self.fig is None:
            messagebox.showwarning("Aviso", "Não há gráficos gerados para exportar.")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Exportar Relatório PDF")
        popup.geometry("450x380")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        ctk.CTkLabel(popup, text="Selecione os gráficos para o Relatório:", font=("Arial", 14, "bold")).pack(pady=15)

        self.vars_export = {}
        
        self.graficos_meta = {
            "g1": ("Pareceres Gerados por Mês", "Apresenta o volume de pareceres técnicos emitidos ao longo de cada mês do período selecionado, permitindo identificar picos de demanda e sazonalidades no setor de Projetos de Mobilidade."),
            "g2": ("Proporção de Decisões", "Ilustra o percentual de pareceres deferidos e indeferidos, fornecendo uma visão macro sobre a taxa de aprovação das solicitações analisadas pelo departamento."),
            "g3": ("Top 10 Solicitantes (Geral)", "Destaca os dez requerentes com o maior volume de solicitações, facilitando o mapeamento dos principais atores que demandam serviços e avaliações do setor."),
            "g4": ("Top 5 Assuntos Demandados", "Exibe os cinco temas mais recorrentes nos processos analisados, evidenciando as principais frentes de trabalho da equipe de Projetos.")
        }

        for key, meta in self.graficos_meta.items():
            var = ctk.BooleanVar(value=True)
            self.vars_export[key] = var
            chk = ctk.CTkCheckBox(popup, text=meta[0], variable=var, fg_color=COLOR_PRIMARY)
            chk.pack(anchor="w", padx=40, pady=8)

        ctk.CTkButton(popup, text="Gerar Relatório Completo", fg_color=COLOR_PRIMARY, command=lambda: self.iniciar_geracao_pdf(popup)).pack(pady=25)

    def iniciar_geracao_pdf(self, popup):
        selecionados = {k: v.get() for k, v in self.vars_export.items()}
        if not any(selecionados.values()):
            messagebox.showwarning("Aviso", "Selecione pelo menos um gráfico.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Salvar Relatório PDF",
            initialfile="Relatorio_Executivo_Mobilidade.pdf"  
        )
        if not filepath: return

        popup.destroy()

        import tempfile
        import os
        temp_dir = tempfile.gettempdir()
        imagens_salvas = {}
        
        # Mapeamento Seguro por Linha e Coluna EXATA
        axs_map = {"g1": (0,0), "g2": (0,1), "g3": (1,0), "g4": (1,1)}

        try:
            for key in selecionados:
                if selecionados[key]:
                    # Acessando linha e coluna individualmente (BLINDAGEM CONTRA O SLICE ERROR)
                    linha, coluna = axs_map[key]
                    ax = self.axs[linha, coluna]
                    
                    caminho_img = os.path.join(temp_dir, f"temp_pm_{key}.png")
                    extent = ax.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
                    self.fig.savefig(caminho_img, bbox_inches=extent.expanded(1.25, 1.25), dpi=150)
                    imagens_salvas[key] = caminho_img
            
            kpis = self.service.calcular_kpis(self.df_f)
            d_ini = self.data_ini.get_date()
            d_fim = self.data_fim.get_date()
            
            self.service.gerar_relatorio_pdf(filepath, imagens_salvas, self.graficos_meta, kpis, d_ini, d_fim)
            messagebox.showinfo("Sucesso", "Relatório Executivo gerado com sucesso!")
            os.startfile(filepath) # Abre o arquivo final automaticamente!
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {e}")
        finally:
            for img in imagens_salvas.values():
                if os.path.exists(img): os.remove(img)

def renderizar(frame_destino, usuario_logado):
    return DashboardPMView(master=frame_destino, usuario_logado=usuario_logado)