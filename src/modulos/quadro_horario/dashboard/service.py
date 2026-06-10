import pandas as pd
import unicodedata
from datetime import datetime
from src.modulos.quadro_horario.dashboard.repository import DashboardQuadroHorarioRepository

class DashboardQuadroHorarioService:
    def __init__(self):
        self.repo = DashboardQuadroHorarioRepository()

    def normalizar(self, texto: str) -> str:
        if not texto or not isinstance(texto, str): return ""
        nfkd = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()

    def carregar_dados_brutos(self):
        df_par = self.repo.buscar_dados_pareceres()
        df_pesq = self.repo.buscar_dados_pesquisas()

        if not df_par.empty: df_par['data_dt'] = pd.to_datetime(df_par['data_dt'], errors='coerce')
        if not df_pesq.empty: df_pesq['data_dt'] = pd.to_datetime(df_pesq['data_dt'], errors='coerce')

        return df_par, df_pesq

    def filtrar_dados(self, df_par, df_pesq, dt_inicio, dt_fim):
        df_par_f = df_par.copy()
        df_pesq_f = df_pesq.copy()

        dt_inicio_pd = pd.to_datetime(dt_inicio)
        dt_fim_pd = pd.to_datetime(dt_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        if not df_par_f.empty and 'data_dt' in df_par_f.columns:
            df_par_f = df_par_f[(df_par_f['data_dt'] >= dt_inicio_pd) & (df_par_f['data_dt'] <= dt_fim_pd)]
        if not df_pesq_f.empty and 'data_dt' in df_pesq_f.columns:
            df_pesq_f = df_pesq_f[(df_pesq_f['data_dt'] >= dt_inicio_pd) & (df_pesq_f['data_dt'] <= dt_fim_pd)]

        return df_par_f, df_pesq_f

    def calcular_kpis(self, df_par_f, df_pesq_f):
        c_par = len(df_par_f)
        c_pesq = len(df_pesq_f)
        
        c_def, c_indef = 0, 0
        if not df_par_f.empty and 'tipo' in df_par_f.columns:
            s_tipo = df_par_f['tipo'].astype(str).str.strip().str.upper()
            c_indef = len(df_par_f[s_tipo == 'INDEFERIDO'])
            c_def = len(df_par_f[s_tipo == 'DEFERIDO'])
            
        return c_par, c_pesq, c_def, c_indef

    def preparar_tabela_resumo_mensal(self, df_par_f, df_pesq_f):
        meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        tabela = []
        for m_num, m_nome in meses.items():
            def_cnt, indef_cnt = 0, 0
            t_cnt, d_cnt = 0, 0
            
            if not df_par_f.empty and 'data_dt' in df_par_f.columns:
                m_par = df_par_f[df_par_f['data_dt'].dt.month == m_num]
                if not m_par.empty:
                    s_tipo = m_par['tipo'].astype(str).str.upper()
                    indef_cnt = int((s_tipo == 'INDEFERIDO').sum())
                    def_cnt = int((s_tipo == 'DEFERIDO').sum())

            if not df_pesq_f.empty and 'data_dt' in df_pesq_f.columns:
                m_pesq = df_pesq_f[df_pesq_f['data_dt'].dt.month == m_num]
                if not m_pesq.empty:
                    s_pesq = m_pesq['tipo'].astype(str).str.lower()
                    t_cnt = int(s_pesq.str.contains('tempo').sum())
                    d_cnt = int(s_pesq.str.contains('demanda').sum())

            total_mes = def_cnt + indef_cnt + t_cnt + d_cnt
            tabela.append([m_nome, def_cnt, indef_cnt, t_cnt, d_cnt, total_mes])
        return tabela

    def exportar_dashboard_pdf(self, filepath, periodo_str, kpis, selecoes, imagens, dados_tabela=None):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, KeepTogether
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except ImportError:
            return False, "Biblioteca 'reportlab' não encontrada. Instale usando: pip install reportlab"

        try:
            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontSize=18, textColor=colors.HexColor("#0F8C75"), spaceAfter=15, fontName='Helvetica-Bold')
            heading_style = ParagraphStyle(name='CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor("#333333"), spaceBefore=15, spaceAfter=8, fontName='Helvetica-Bold')
            normal_style = ParagraphStyle(name='CustomNormal', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#444444"), leading=14)
            heading_side = ParagraphStyle(name='HeadingSide', parent=styles['Heading3'], fontSize=11, textColor=colors.HexColor("#333333"), spaceBefore=5, spaceAfter=5, fontName='Helvetica-Bold')
            normal_side = ParagraphStyle(name='NormalSide', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor("#555555"), leading=11)

            elements.append(Paragraph(f"Relatório Executivo Analítico - Quadro de Horário ({periodo_str})", title_style))
            data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
            elements.append(Paragraph(f"Documento gerado automaticamente pelo Sistema de Gestão Integrado (SGI) em {data_atual}. Este documento consolida os indicadores de desempenho e o fluxo de pesquisas do setor de Quadro de Horários (SPR).", normal_style))
            elements.append(Spacer(1, 15))

            if selecoes.get("kpis"):
                data_kpi = [
                    ["Métrica de Produtividade", "Volume Processado"],
                    ["Total de Pareceres Técnicos Avaliados", str(kpis['total_par'])],
                    ["Total de Pesquisas de Campo Realizadas", str(kpis['total_pesq'])],
                    ["Pareceres Deferidos (Aprovados)", str(kpis['deferidos'])],
                    ["Pareceres Indeferidos (Recusados)", str(kpis['indeferidos'])]
                ]
                t_kpi = Table(data_kpi, colWidths=[385, 150])
                t_kpi.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F8C75")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('ALIGN', (1,1), (1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                    ('TOPPADDING', (0,0), (-1,-1), 7),
                    ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F8F9FA")),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ]))
                elements.append(KeepTogether([Paragraph("1. Indicadores Gerais de Produção", heading_style), t_kpi]))
                elements.append(Spacer(1, 15))

            if selecoes.get("tabela_resumo") and dados_tabela:
                headers = ["Mês", "Pareceres\nDeferidos", "Pareceres\nIndeferidos", "Pesquisas\n(Tempo)", "Pesquisas\n(Demanda)", "Total Geral\nMensal"]
                data_tab = [headers] + dados_tabela
                
                # Somatório final
                totais = ["TOTAL", sum(r[1] for r in dados_tabela), sum(r[2] for r in dados_tabela), sum(r[3] for r in dados_tabela), sum(r[4] for r in dados_tabela), sum(r[5] for r in dados_tabela)]
                data_tab.append(totais)

                t_resumo = Table(data_tab, colWidths=[95, 88, 88, 88, 88, 88])
                t_resumo.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F8C75")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#E0E4E8")),
                    ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ]))
                elements.append(KeepTogether([Paragraph("2. Balanço Mensal Consolidado (Pareceres e Pesquisas)", heading_style), Spacer(1, 5), t_resumo]))
                elements.append(Spacer(1, 15))

            graficos_meta = {
                "g1": ("Evolução Mensal de Pareceres", "Fluxo de análise e vistorias de Pareceres ao longo dos meses."),
                "g2": ("Evolução Mensal de Pesquisas", "Mapeamento da distribuição temporal da execução de pesquisas de campo."),
                "g3": ("Top Solicitantes Institucionais", "Ranking dos principais emissores de demanda de análise."),
                "g4": ("Assuntos Mais Recorrentes", "Distribuição das temáticas principais exigidas nos pareceres."),
                "g5": ("Taxa de Aprovação (Pareceres)", "Índice de deferimento vs indeferimento."),
                "g6": ("Proporção de Tipos de Pesquisa", "Comparativo entre Pesquisas de Tempo de Viagem e Demanda."),
                "g7": ("Linhas Mais Pesquisadas", "Ranking das rotas de transporte com maior índice de análise de campo."),
                "g8": ("Natureza da Afetação", "Origem da necessidade do Parecer (Eventos Urbanos vs Alteração direta em Linhas)."),
                "g9": ("Carga Operacional de Pareceres", "Distribuição interna da responsabilidade técnica por Pareceres."),
                "g10": ("Carga Operacional de Pesquisas", "Distribuição interna do esforço focado nas pesquisas de campo."),
                "g11": ("Produtividade Total (Parecer + Pesq.)", "Consolidação bruta da entrega de cada membro do setor."),
                "g12": ("Desempenho Relativo", "Variação percentual em relação à média de produção do setor.")
            }

            def add_grafico_full(chave):
                img_stream = imagens[chave]; img_stream.seek(0)
                img = RLImage(img_stream, width=480, height=270)
                elements.append(KeepTogether([
                    Paragraph(graficos_meta[chave][0], heading_style),
                    Paragraph(graficos_meta[chave][1], normal_style),
                    Spacer(1, 5), img
                ]))
                elements.append(Spacer(1, 15))

            def add_graficos_lado_a_lado(k1, k2):
                imagens[k1].seek(0); imagens[k2].seek(0)
                c1 = [Paragraph(graficos_meta[k1][0], heading_side), Paragraph(graficos_meta[k1][1], normal_side), Spacer(1, 5), RLImage(imagens[k1], width=250, height=140, kind='proportional')]
                c2 = [Paragraph(graficos_meta[k2][0], heading_side), Paragraph(graficos_meta[k2][1], normal_side), Spacer(1, 5), RLImage(imagens[k2], width=250, height=140, kind='proportional')]
                t = Table([[c1, c2]], colWidths=[265, 265])
                t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
                elements.append(KeepTogether([t]))
                elements.append(Spacer(1, 15))

            # Separação Inteligente: Gráficos de Pizza Lado a Lado
            pie_charts = ["g5", "g6", "g8"]
            pies_escolhidos = [k for k in pie_charts if selecoes.get(k)]
            
            for i in range(0, len(pies_escolhidos), 2):
                if i + 1 < len(pies_escolhidos): add_graficos_lado_a_lado(pies_escolhidos[i], pies_escolhidos[i+1])
                else: add_grafico_full(pies_escolhidos[i]) 

            for i in range(1, 13):
                k = f"g{i}"
                if k not in pie_charts and selecoes.get(k): add_grafico_full(k)

            doc.build(elements)
            return True, "Relatório gerencial em PDF exportado com sucesso!"
        except Exception as e:
            return False, f"Ocorreu um erro interno ao compilar o PDF: {str(e)}"