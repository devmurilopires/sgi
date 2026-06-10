import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Image as RLImage

class DashboardPMService:
    def __init__(self, repository):
        self.repo = repository

    def carregar_dados_brutos(self):
        df = self.repo.buscar_dados_pareceres()
        if not df.empty:
            df['data_dt'] = pd.to_datetime(df['data_dt'])
        return df

    def filtrar_dados(self, df, data_ini, data_fim):
        if df.empty: return df
        mask = (df['data_dt'].dt.date >= data_ini) & (df['data_dt'].dt.date <= data_fim)
        return df.loc[mask]

    def calcular_kpis(self, df):
        if df.empty: return 0, 0, 0, "Nenhum"
        total = len(df)
        def_qte = len(df[df['decisao'] == 'DEFERIDO'])
        ind_qte = len(df[df['decisao'] == 'INDEFERIDO'])
        top_solicitante = df['solicitante'].mode()[0] if not df['solicitante'].empty else "Nenhum"
        return total, def_qte, ind_qte, top_solicitante

    def preparar_tabela_mensal(self, df):
        if df.empty: return []
        meses_nomes = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
                       7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
        
        df['mes_num'] = df['data_dt'].dt.month
        resumo = df.groupby(['mes_num', 'decisao']).size().unstack(fill_value=0)
        
        for col in ['DEFERIDO', 'INDEFERIDO']:
            if col not in resumo.columns: resumo[col] = 0
            
        resumo['Total'] = resumo['DEFERIDO'] + resumo['INDEFERIDO']
        lista_final = []
        for mes_idx in range(1, 13):
            nome = meses_nomes[mes_idx]
            if mes_idx in resumo.index:
                row = resumo.loc[mes_idx]
                lista_final.append([nome, int(row['DEFERIDO']), int(row['INDEFERIDO']), int(row['Total'])])
            else:
                lista_final.append([nome, 0, 0, 0])
        return lista_final

    def gerar_relatorio_pdf(self, filepath, imagens, graficos_meta, kpis, data_ini, data_fim):
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos Customizados Elegantes
        title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=18, spaceAfter=15, textColor=colors.HexColor("#0F8C75"), alignment=1)
        subtitle_style = ParagraphStyle(name='SubTitle', parent=styles['Normal'], fontSize=11, spaceAfter=20, alignment=1)
        
        heading_style = ParagraphStyle(name='Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=5, textColor=colors.HexColor("#0F8C75"))
        normal_style = ParagraphStyle(name='NormalDesc', parent=styles['Normal'], fontSize=10, spaceAfter=15, textColor=colors.HexColor("#555555"), alignment=4)
        
        heading_side = ParagraphStyle(name='HeadingSide', parent=styles['Heading2'], fontSize=12, spaceAfter=5, textColor=colors.HexColor("#0F8C75"), alignment=1)
        normal_side = ParagraphStyle(name='NormalSide', parent=styles['Normal'], fontSize=9, spaceAfter=10, textColor=colors.HexColor("#555555"), alignment=1)

        # Capa do Relatório
        elements.append(Paragraph("Relatório Gerencial Detalhado - Projetos de Mobilidade", title_style))
        periodo_texto = f"Período Analisado: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(periodo_texto, subtitle_style))
        elements.append(Spacer(1, 10))

        # Tabela de KPIs (Resumo Geral)
        total, def_qte, ind_qte, top_solicitante = kpis
        dados_kpi = [
            ["Total de Pareceres", "Deferidos", "Indeferidos", "Top Solicitante"],
            [str(total), str(def_qte), str(ind_qte), str(top_solicitante)]
        ]
        tabela_kpi = Table(dados_kpi, colWidths=[120, 100, 100, 180])
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
                    c2 = [] # Célula Vazia Segura

                t_graf = Table([[c1, c2]], colWidths=[260, 260])
                t_graf.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'), 
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('LEFTPADDING', (0,0), (-1,-1), 0), 
                    ('RIGHTPADDING', (0,0), (-1,-1), 0)
                ]))
                
                elements.append(KeepTogether([t_graf]))
                elements.append(Spacer(1, 15))
                
                pares_processados += 1
                # Quebra a página a cada 2 pares para manter a folha respirável
                if pares_processados % 2 == 0 and i + 2 < len(chaves_imgs):
                    elements.append(PageBreak())

        doc.build(elements)