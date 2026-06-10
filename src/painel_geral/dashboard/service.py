import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Image as RLImage

from src.painel_geral.dashboard.repository import DashboardGeralRepository

class DashboardGeralService:
    def __init__(self):
        self.repo = DashboardGeralRepository()

    def carregar_dados_brutos(self):
        df_os = self.repo.buscar_dados_os_global()
        df_par = self.repo.buscar_dados_pareceres_global()
        df_pesq = self.repo.buscar_dados_pesquisas_global()

        if not df_os.empty: df_os['data_dt'] = pd.to_datetime(df_os['data_dt'], errors='coerce')
        if not df_par.empty: df_par['data_dt'] = pd.to_datetime(df_par['data_dt'], errors='coerce')
        if not df_pesq.empty: df_pesq['data_dt'] = pd.to_datetime(df_pesq['data_dt'], errors='coerce')

        return df_os, df_par, df_pesq

    def filtrar_dados(self, df_os, df_par, df_pesq, data_inicio, data_fim):
        dt_ini = pd.to_datetime(data_inicio)
        dt_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        df_os_f = df_os[(df_os['data_dt'] >= dt_ini) & (df_os['data_dt'] <= dt_fim)] if not df_os.empty else df_os
        df_par_f = df_par[(df_par['data_dt'] >= dt_ini) & (df_par['data_dt'] <= dt_fim)] if not df_par.empty else df_par
        df_pesq_f = df_pesq[(df_pesq['data_dt'] >= dt_ini) & (df_pesq['data_dt'] <= dt_fim)] if not df_pesq.empty else df_pesq

        return df_os_f, df_par_f, df_pesq_f

    def calcular_kpis(self, df_os_f, df_par_f, df_pesq_f):
        c_os = len(df_os_f)
        c_par = len(df_par_f)
        c_pesq = len(df_pesq_f)
        c_total = c_os + c_par + c_pesq

        s_os = df_os_f['criado_por'].value_counts() if not df_os_f.empty else pd.Series(dtype=int)
        s_par = df_par_f['criado_por'].value_counts() if not df_par_f.empty else pd.Series(dtype=int)
        s_pesq = df_pesq_f['criado_por'].value_counts() if not df_pesq_f.empty else pd.Series(dtype=int)
        
        prod_total = s_os.add(s_par, fill_value=0).add(s_pesq, fill_value=0).sort_values(ascending=False)
        campeao = prod_total.index[0] if not prod_total.empty else "Nenhum"

        return c_total, c_os, c_par, c_pesq, campeao

    def gerar_relatorio_pdf(self, filepath, imagens, graficos_meta, kpis, data_ini, data_fim):
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos Customizados
        title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=18, spaceAfter=15, textColor=colors.HexColor("#0F8C75"), alignment=1)
        subtitle_style = ParagraphStyle(name='SubTitle', parent=styles['Normal'], fontSize=11, spaceAfter=20, alignment=1)
        
        heading_style = ParagraphStyle(name='Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=5, textColor=colors.HexColor("#0F8C75"))
        normal_style = ParagraphStyle(name='NormalDesc', parent=styles['Normal'], fontSize=10, spaceAfter=15, textColor=colors.HexColor("#555555"), alignment=4)
        
        heading_side = ParagraphStyle(name='HeadingSide', parent=styles['Heading2'], fontSize=12, spaceAfter=5, textColor=colors.HexColor("#0F8C75"), alignment=1)
        normal_side = ParagraphStyle(name='NormalSide', parent=styles['Normal'], fontSize=9, spaceAfter=10, textColor=colors.HexColor("#555555"), alignment=1)

        # Capa do Relatório
        elements.append(Paragraph("Relatório Executivo de Produtividade Global", title_style))
        periodo_texto = f"Período Analisado: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(periodo_texto, subtitle_style))
        elements.append(Spacer(1, 10))

        # Tabela de KPIs (Resumo Global - 5 Colunas)
        c_total, c_os, c_par, c_pesq, champ = kpis
        dados_kpi = [
            ["Total Geral", "OS", "Pareceres", "Pesquisas", "Destaque Produtividade"],
            [str(c_total), str(c_os), str(c_par), str(c_pesq), str(champ.split()[0] if isinstance(champ, str) else champ)]
        ]
        
        tabela_kpi = Table(dados_kpi, colWidths=[90, 80, 80, 80, 160])
        tabela_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F8C75")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F4F6F9")),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor("#333333")),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E0E0E0"))
        ]))
        elements.append(tabela_kpi)
        elements.append(Spacer(1, 30))

        # Organização Dinâmica de Layout (1 Único ou Múltiplos)
        chaves_imgs = list(imagens.keys())
        
        # Inteligência: Se escolheu apenas 1 gráfico, desenha grande!
        if len(chaves_imgs) == 1:
            k1 = chaves_imgs[0]
            elements.append(Paragraph(graficos_meta[k1][0], heading_style))
            elements.append(Paragraph(graficos_meta[k1][1], normal_style))
            elements.append(RLImage(imagens[k1], width=450, height=220, kind='proportional'))
            elements.append(Spacer(1, 20))
        
        else:
            # Renderização Lado a Lado para múltiplos gráficos
            pares_processados = 0
            for i in range(0, len(chaves_imgs), 2):
                k1 = chaves_imgs[i]
                c1 = [Paragraph(graficos_meta[k1][0], heading_side), Paragraph(graficos_meta[k1][1], normal_side), Spacer(1, 5), RLImage(imagens[k1], width=240, height=180, kind='proportional')]
                
                if i + 1 < len(chaves_imgs):
                    k2 = chaves_imgs[i+1]
                    c2 = [Paragraph(graficos_meta[k2][0], heading_side), Paragraph(graficos_meta[k2][1], normal_side), Spacer(1, 5), RLImage(imagens[k2], width=240, height=180, kind='proportional')]
                else:
                    c2 = [] # Célula vazia segura

                t_graf = Table([[c1, c2]], colWidths=[260, 260])
                t_graf.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'), 
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0), 
                    ('RIGHTPADDING', (0,0), (-1,-1), 0)
                ]))
                
                elements.append(KeepTogether([t_graf]))
                elements.append(Spacer(1, 20))
                
                pares_processados += 1
                # Quebra a página a cada 2 pares para manter a folha organizada
                if pares_processados % 2 == 0 and i + 2 < len(chaves_imgs):
                    elements.append(PageBreak())

        doc.build(elements)