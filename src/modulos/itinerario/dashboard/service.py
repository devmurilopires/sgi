import pandas as pd
import math
from datetime import datetime

class DashboardItinerarioService:
    def __init__(self, repository):
        self.repo = repository

    def carregar_dados_brutos(self):
        df_os = self.repo.buscar_dados_os()
        df_par = self.repo.buscar_dados_pareceres()

        if not df_os.empty:
            df_os['data_dt'] = pd.to_datetime(df_os['data_dt'], errors='coerce')
        if not df_par.empty:
            df_par['data_dt'] = pd.to_datetime(df_par['data_dt'], errors='coerce')

        return df_os, df_par

    def filtrar_dados(self, df_os, df_par, dt_inicio, dt_fim):
        df_os_f = df_os.copy()
        df_par_f = df_par.copy()

        dt_inicio_pd = pd.to_datetime(dt_inicio)
        dt_fim_pd = pd.to_datetime(dt_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        if not df_os_f.empty and 'data_dt' in df_os_f.columns:
            df_os_f = df_os_f[(df_os_f['data_dt'] >= dt_inicio_pd) & (df_os_f['data_dt'] <= dt_fim_pd)]
        if not df_par_f.empty and 'data_dt' in df_par_f.columns:
            df_par_f = df_par_f[(df_par_f['data_dt'] >= dt_inicio_pd) & (df_par_f['data_dt'] <= dt_fim_pd)]

        return df_os_f, df_par_f

    def calcular_kpis(self, df_os_f, df_par_f):
        c_os = int(len(df_os_f))
        c_par = int(len(df_par_f))
        
        c_def = 0
        c_indef = 0
        
        if not df_par_f.empty and 'tipo' in df_par_f.columns:
            s_tipo = df_par_f['tipo'].astype(str).str.upper()
            c_indef = int(s_tipo.str.contains('INDEFERIDO', na=False).sum())
            c_def = int(s_tipo.str.contains('DEFERIDO', na=False).sum()) - c_indef
        
        return c_os, c_par, c_def, c_indef

    def preparar_tabela_mensal_pareceres(self, df_par_f):
        meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        tabela = []
        for m_num, m_nome in meses.items():
            if df_par_f.empty or 'data_dt' not in df_par_f.columns:
                tabela.append([m_nome, 0, 0, 0])
                continue
                
            mes_data = df_par_f[df_par_f['data_dt'].dt.month == m_num]
            total_mes = int(len(mes_data))
            
            deferidos, indeferidos = 0, 0
            if not mes_data.empty and 'tipo' in mes_data.columns:
                s_tipo = mes_data['tipo'].astype(str).str.upper()
                indeferidos = int(s_tipo.str.contains('INDEFERIDO', na=False).sum())
                deferidos = int(s_tipo.str.contains('DEFERIDO', na=False).sum()) - indeferidos
                
            tabela.append([m_nome, deferidos, indeferidos, total_mes])
        return tabela

    def preparar_tabela_mensal_os(self, df_os_f):
        meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        tabela = []
        for m_num, m_nome in meses.items():
            if df_os_f.empty or 'data_dt' not in df_os_f.columns:
                tabela.append([m_nome, 0, 0, 0, 0, 0])
                continue
                
            mes_data = df_os_f[df_os_f['data_dt'].dt.month == m_num]
            total_mes = int(len(mes_data))
            
            eventos, corrida, obras = 0, 0, 0
            if not mes_data.empty and 'tipo_os' in mes_data.columns:
                s_tipo = mes_data['tipo_os'].astype(str).str.upper()
                eventos = int(s_tipo.str.contains('EVENTO', na=False).sum())
                corrida = int(s_tipo.str.contains('CORRIDA', na=False).sum())
                obras = int(s_tipo.str.contains('OBRA', na=False).sum())
                
            outros = total_mes - (eventos + corrida + obras)
            tabela.append([m_nome, eventos, corrida, obras, outros, total_mes])
        return tabela

    def exportar_dashboard_pdf(self, filepath, periodo_str, kpis, selecoes, imagens):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except ImportError:
            return False, "Biblioteca 'reportlab' não encontrada. Instale usando: pip install reportlab"

        try:
            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            elements = []
            styles = getSampleStyleSheet()

            # Estilos Executivos
            title_style = ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontSize=18, textColor=colors.HexColor("#0F8C75"), spaceAfter=20, fontName='Helvetica-Bold')
            heading_style = ParagraphStyle(name='CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor("#333333"), spaceBefore=20, spaceAfter=10, fontName='Helvetica-Bold')
            normal_style = ParagraphStyle(name='CustomNormal', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor("#444444"), leading=14)

            # Cabeçalho
            elements.append(Paragraph(f"Relatório Executivo de Desempenho - Itinerário ({periodo_str})", title_style))
            data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
            elements.append(Paragraph(f"Documento gerado automaticamente pelo Sistema de Gestão Integrado (SGI) em {data_atual}. Este relatório apresenta a análise estruturada da produtividade e volume de demandas tratadas pelo setor de Itinerário.", normal_style))
            elements.append(Spacer(1, 20))

            # Seção 1: KPIs Granulares
            kpis_selecionados = any([selecoes.get("kpi_total_os"), selecoes.get("kpi_total_par"), selecoes.get("kpi_def"), selecoes.get("kpi_indef")])
            
            if kpis_selecionados:
                elements.append(Paragraph("1. Indicadores Gerais de Produção", heading_style))
                elements.append(Paragraph("A tabela abaixo consolida os volumes absolutos dos indicadores selecionados durante o período filtrado.", normal_style))
                elements.append(Spacer(1, 10))
                
                data_kpi = [["Métrica de Produtividade", "Volume Processado"]]
                
                if selecoes.get("kpi_total_os"): 
                    data_kpi.append(["Total de Ordens de Serviço (OS) Emitidas", str(kpis['total_os'])])
                if selecoes.get("kpi_total_par"): 
                    data_kpi.append(["Total de Pareceres Técnicos Avaliados", str(kpis['total_par'])])
                if selecoes.get("kpi_def"): 
                    data_kpi.append(["Demandas Deferidas (Aprovadas)", str(kpis['deferidos'])])
                if selecoes.get("kpi_indef"): 
                    data_kpi.append(["Demandas Indeferidas (Recusadas)", str(kpis['indeferidos'])])
                
                if len(data_kpi) > 1:
                    t = Table(data_kpi, colWidths=[350, 150])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F8C75")),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('ALIGN', (1,1), (1,-1), 'CENTER'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                        ('TOPPADDING', (0,0), (-1,-1), 8),
                        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8F9FA")),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                    ]))
                    elements.append(t)
                    elements.append(Spacer(1, 20))

            def add_grafico_ao_doc(img_stream, titulo, explicacao):
                elements.append(Paragraph(titulo, heading_style))
                elements.append(Paragraph(explicacao, normal_style))
                elements.append(Spacer(1, 10))
                img_stream.seek(0)
                img = RLImage(img_stream, width=460, height=260)
                elements.append(img)
                elements.append(Spacer(1, 20))

            # Seção 2: Gráficos
            if selecoes.get("g1"):
                add_grafico_ao_doc(imagens["g1"], "Evolução Mensal de Ordens de Serviço", 
                                   "O gráfico a seguir mapeia a distribuição temporal de emissão de Ordens de Serviço ao longo do período selecionado.")
            
            if selecoes.get("g2"):
                add_grafico_ao_doc(imagens["g2"], "Evolução Mensal de Pareceres Técnicos", 
                                   "Esta visualização apresenta o fluxo de análise de Pareceres Técnicos por mês.")

            if selecoes.get("g3"):
                add_grafico_ao_doc(imagens["g3"], "Principais Entidades Solicitantes", 
                                   "O ranking destaca os 10 maiores emissores de demandas para o setor de Itinerário.")

            if selecoes.get("g4"):
                add_grafico_ao_doc(imagens["g4"], "Volume de Produção Cruzada por Técnico", 
                                   "Comparativo direto da carga de trabalho entre os técnicos, dividindo o esforço empenhado entre OS e Pareceres.")

            if selecoes.get("g5"):
                add_grafico_ao_doc(imagens["g5"], "Ranking de Produtividade Total", 
                                   "Consolidação absoluta de todos os documentos gerados no sistema por membro da equipa técnica.")

            if selecoes.get("g6"):
                add_grafico_ao_doc(imagens["g6"], "Indicador de Desempenho Relativo (Média da Equipe)", 
                                   "Este painel traduz a produção bruta em percentagens relativas à média de entrega ideal da equipa.")

            doc.build(elements)
            return True, "Relatório gerencial em PDF exportado com sucesso!"
        except Exception as e:
            return False, f"Ocorreu um erro interno ao compilar o PDF: {str(e)}"