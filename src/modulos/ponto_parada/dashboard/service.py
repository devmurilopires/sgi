import pandas as pd
import unicodedata
from datetime import datetime
from src.modulos.ponto_parada.dashboard.repository import DashboardRepository

class DashboardService:
    def __init__(self):
        self.repo = DashboardRepository()

    def normalizar(self, texto: str) -> str:
        """Remove acentos e deixa caixa alta para agrupamento na tabela."""
        if not texto or not isinstance(texto, str): return ""
        nfkd = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()

    def carregar_dados_brutos(self):
        df_os = self.repo.buscar_dados_os()
        df_par = self.repo.buscar_dados_pareceres()

        if not df_os.empty:
            df_os['data_dt'] = pd.to_datetime(df_os['data_dt'], errors='coerce')
            if 'origem' in df_os.columns:
                df_os['origem'] = df_os['origem'].fillna('SPU').astype(str).str.upper().str.strip()
                
        if not df_par.empty:
            df_par['data_dt'] = pd.to_datetime(df_par['data_dt'], errors='coerce')
            if 'origem' in df_par.columns:
                df_par['origem'] = df_par['origem'].fillna('SPU').astype(str).str.upper().str.strip()

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
        count_os = len(df_os_f)
        count_par = len(df_par_f)
        
        if not df_par_f.empty and 'tipo' in df_par_f.columns:
            count_def = len(df_par_f[df_par_f['tipo'].astype(str).str.strip().str.upper() == 'DEFERIDO'])
            count_indef = len(df_par_f[df_par_f['tipo'].astype(str).str.strip().str.upper() == 'INDEFERIDO'])
        else:
            count_def = 0
            count_indef = 0
            
        return count_os, count_par, count_def, count_indef

    def exportar_dashboard_pdf(self, filepath, periodo_str, kpis, selecoes, imagens, df_resumo=None):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, KeepTogether
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except ImportError:
            return False, "Biblioteca 'reportlab' não encontrada. Instale usando: pip install reportlab"

        try:
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()

            # Estilos Customizados
            title_style = ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontSize=18, textColor=colors.HexColor("#0F8C75"), spaceAfter=15, fontName='Helvetica-Bold')
            heading_style = ParagraphStyle(name='CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor("#333333"), spaceBefore=15, spaceAfter=8, fontName='Helvetica-Bold')
            normal_style = ParagraphStyle(name='CustomNormal', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#444444"), leading=14)
            
            # Estilos para os Gráficos Emparelhados Lado-a-Lado
            heading_side = ParagraphStyle(name='HeadingSide', parent=styles['Heading3'], fontSize=11, textColor=colors.HexColor("#333333"), spaceBefore=5, spaceAfter=5, fontName='Helvetica-Bold')
            normal_side = ParagraphStyle(name='NormalSide', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor("#555555"), leading=11)

            # Cabeçalho
            elements.append(Paragraph(f"Relatório Executivo Analítico - Ponto de Parada ({periodo_str})", title_style))
            data_atual = datetime.now().strftime("%d/%m/%Y às %H:%M")
            elements.append(Paragraph(f"Documento gerado automaticamente pelo Sistema de Gestão Integrado (SGI) em {data_atual}. Este documento consolida os indicadores de desempenho, produtividade e intervenções estruturais do setor.", normal_style))
            elements.append(Spacer(1, 15))

            # Seção 1: KPIs
            kpis_selecionados = any([selecoes.get("kpi_total_os"), selecoes.get("kpi_total_par"), selecoes.get("kpi_def"), selecoes.get("kpi_indef")])
            if kpis_selecionados:
                data_kpi = [["Métrica de Produtividade", "Volume Processado"]]
                if selecoes.get("kpi_total_os"): data_kpi.append(["Total de Ordens de Serviço (OS) Emitidas", str(kpis['total_os'])])
                if selecoes.get("kpi_total_par"): data_kpi.append(["Total de Pareceres Técnicos Avaliados", str(kpis['total_par'])])
                if selecoes.get("kpi_def"): data_kpi.append(["Demandas Deferidas (Aprovadas)", str(kpis['deferidos'])])
                if selecoes.get("kpi_indef"): data_kpi.append(["Demandas Indeferidas (Recusadas)", str(kpis['indeferidos'])])
                
                if len(data_kpi) > 1:
                    t_kpi = Table(data_kpi, colWidths=[400, 150])
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

            # Seção 2: Tabela de Resumo com BLINDAGEM de Corte (KeepTogether)
            if selecoes.get("tabela_resumo") and df_resumo is not None and not df_resumo.empty:
                data_tab = [df_resumo.columns.tolist()] + df_resumo.values.tolist()
                for i in range(1, len(data_tab)):
                    for j in range(1, len(data_tab[i])):
                        val = data_tab[i][j]
                        data_tab[i][j] = str(int(val)) if isinstance(val, (int, float)) and val == int(val) else str(val)
                
                # Ajuste cirúrgico das 14 colunas para Landscape A4 (Largura disponível ~782 pontos)
                col_widths = [200] + [40] * 12 + [55]
                t_resumo = Table(data_tab, colWidths=col_widths)
                t_resumo.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F8C75")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 7), # Fonte ajustada para não quebrar linha
                    ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#E0E4E8")),
                    ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ]))
                
                # KeepTogether: Obriga o ReportLab a renderizar tudo numa folha só sem quebrar ao meio
                elements.append(KeepTogether([Paragraph("2. Resumo Consolidado de Intervenções no Mobiliário (OS)", heading_style), Spacer(1, 5), t_resumo]))
                elements.append(Spacer(1, 15))

            graficos_meta = {
                "g1": ("Evolução Mensal de OS", "Mapeamento da distribuição temporal de emissão de OS."),
                "g2": ("Evolução Mensal de Pareceres", "Fluxo de análise e vistorias de Pareceres ao longo dos meses."),
                "g3": ("Top Bairros com Mais Intervenções", "Mapeamento geográfico das zonas da cidade."),
                "g4": ("Top Solicitantes Institucionais", "Ranking dos principais emissores de demanda de análise."),
                "g5": ("Status de Conclusão das Obras", "Percentagem de OS concluídas vs abortadas."),
                "g6": ("Taxa de Aprovação de Pareceres", "Índice de deferimento vs indeferimento."),
                "g7": ("Natureza da Ação (OS)", "Classificação do tipo macro de serviço."),
                "g8": ("Mobiliário Mais Demandado", "Equipamentos que mais exigem recursos."),
                "g9": ("Carga Operacional OS", "Distribuição interna do esforço de geração de OS."),
                "g10": ("Carga Operacional Pareceres", "Distribuição interna da responsabilidade."),
                "g11": ("Produtividade Total", "Consolidação bruta da entrega de cada membro."),
                "g12": ("Desempenho Relativo", "Variação percentual em relação à média."),
                "g13": ("Origem da Demanda (OS)", "Distribuição entre os sistemas (ex: SISGEP vs SPU)."),
                "g14": ("Origem da Demanda (Pareceres)", "Distribuição entre os sistemas (ex: SISGEP vs SPU).")
            }

            def add_grafico_full(chave):
                img_stream = imagens[chave]; img_stream.seek(0)
                img = RLImage(img_stream, width=540, height=300) 
                elements.append(KeepTogether([
                    Paragraph(graficos_meta[chave][0], heading_style),
                    Paragraph(graficos_meta[chave][1], normal_style),
                    Spacer(1, 5), img
                ]))
                elements.append(Spacer(1, 15))

            def add_graficos_lado_a_lado(k1, k2):
                imagens[k1].seek(0); imagens[k2].seek(0)
                c1 = [Paragraph(graficos_meta[k1][0], heading_side), Paragraph(graficos_meta[k1][1], normal_side), Spacer(1, 5), RLImage(imagens[k1], width=360, height=200, kind='proportional')]
                c2 = [Paragraph(graficos_meta[k2][0], heading_side), Paragraph(graficos_meta[k2][1], normal_side), Spacer(1, 5), RLImage(imagens[k2], width=360, height=200, kind='proportional')]
                t = Table([[c1, c2]], colWidths=[385, 385])
                t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
                elements.append(KeepTogether([t]))
                elements.append(Spacer(1, 15))

            # Separação Inteligente: Gráficos de Pizza ou Menores em Pares Lado-a-Lado
            pie_charts = ["g5", "g6", "g13", "g14"]
            pies_escolhidos = [k for k in pie_charts if selecoes.get(k)]
            
            # Processa os Pizzas (Lado a Lado)
            for i in range(0, len(pies_escolhidos), 2):
                if i + 1 < len(pies_escolhidos): add_graficos_lado_a_lado(pies_escolhidos[i], pies_escolhidos[i+1])
                else: add_grafico_full(pies_escolhidos[i]) # Se sobrar um ímpar, põe grande

            # Processa o Resto
            for i in range(1, 15):
                k = f"g{i}"
                if k not in pie_charts and selecoes.get(k): add_grafico_full(k)

            doc.build(elements)
            return True, "Relatório gerencial em PDF exportado com sucesso!"
        except Exception as e:
            return False, f"Ocorreu um erro interno ao compilar o PDF: {str(e)}"