import os
import shutil
import sys
import subprocess
from datetime import datetime
import pandas as pd
from src.modulos.quadro_horario.relatorios.repository import RelatorioQuadroHorarioRepository

class RelatorioQuadroHorarioService:
    def __init__(self):
        self.repo = RelatorioQuadroHorarioRepository()

    def buscar_sugestoes_linhas(self):
        return self.repo.buscar_linhas()

    def buscar_dados(self, tipo_relatorio, filtros):
        if tipo_relatorio == "PARECER":
            dados_brutos = self.repo.buscar_pareceres(filtros)
            return self._formatar_dados_parecer(dados_brutos)
        elif tipo_relatorio == "PESQUISA":
            dados_brutos = self.repo.buscar_pesquisas(filtros)
            return self._formatar_dados_pesquisa(dados_brutos)
        return []

    def _formatar_dados_parecer(self, dados_brutos):
        dados_formatados = []
        for linha in dados_brutos:
            (id_banco, num, tipo, proc, assun, solic, evt, lin, dt_evt, resp, dt_criacao, caminho) = linha
            dt_str = dt_criacao.strftime("%d/%m/%Y") if dt_criacao else "-"
            dados_formatados.append([
                id_banco, # 0 -> Oculto
                num, tipo, proc or "-", assun or "-", solic or "-", 
                evt or "-", lin or "-", dt_evt or "-", dt_str, resp or "-", caminho
            ])
        return dados_formatados

    def _formatar_dados_pesquisa(self, dados_brutos):
        dados_formatados = []
        for linha in dados_brutos:
            (id_banco, titulo, tipo, criado_por, dt_criacao, json_dados) = linha
            dt_str = dt_criacao.strftime("%d/%m/%Y %H:%M") if dt_criacao else "-"
            tipo_fmt = "Tempo de Viagem" if "tempo" in str(tipo).lower() else "Demanda"
            
            # Extrai datas do JSON para resumo, se existirem
            datas_str = "-"
            if json_dados and isinstance(json_dados, dict) and "datas" in json_dados:
                datas_str = ", ".join(json_dados["datas"])
                
            dados_formatados.append([
                id_banco, # 0 -> Oculto
                id_banco, titulo or "-", tipo_fmt, datas_str, dt_str, criado_por or "-", "None" # Caminho Falso p/ download
            ])
        return dados_formatados

    def abrir_arquivo(self, caminho):
        if not caminho or caminho == "None" or not os.path.exists(caminho):
            return False, f"Arquivo não encontrado ou registro sem documento físico."
        try:
            if os.name == "nt": os.startfile(caminho)
            else: subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", caminho])
            return True, "Aberto com sucesso"
        except Exception as e: return False, f"Erro ao abrir: {e}"

    def baixar_arquivo(self, caminho_origem, caminho_destino):
        if not caminho_origem or caminho_origem == "None" or not os.path.exists(caminho_origem):
            return False, "O documento original não foi encontrado na rede."
        try:
            shutil.copy2(caminho_origem, caminho_destino)
            return True, "Download concluído com sucesso!"
        except Exception as e:
            return False, f"Erro ao fazer download: {str(e)}"

    def excluir_registro(self, tipo_relatorio, id_banco, motivo, usuario_logado):
        if tipo_relatorio == "PARECER":
            return self.repo.excluir_e_logar_parecer(id_banco, motivo, usuario_logado)
        else:
            return self.repo.excluir_e_logar_pesquisa(id_banco, motivo, usuario_logado)

    def exportar_excel(self, filepath, dados, colunas, titulo, texto_filtros):
        try:
            df = pd.DataFrame(dados, columns=colunas)
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                workbook = writer.book
                worksheet = writer.sheets.setdefault('Relatorio', workbook.add_worksheet('Relatorio'))
                
                bold_format = workbook.add_format({'bold': True, 'font_size': 14})
                worksheet.write('A1', titulo, bold_format)
                worksheet.write('A2', f"Filtros Aplicados: {texto_filtros}")
                worksheet.write('A3', f"Total de Resultados: {len(dados)} registro(s)")
                
                df.to_excel(writer, sheet_name='Relatorio', startrow=4, index=False)
                
                for i, col in enumerate(colunas):
                    max_len = max(df[col].astype(str).map(len).max() if not df.empty else 0, len(col)) + 2
                    worksheet.set_column(i, i, min(max_len, 50))
                    
            return True, "Relatório Excel exportado com sucesso!"
        except Exception as e:
            return False, f"Ocorreu um erro ao exportar o Excel: {e}"

    def exportar_pdf(self, filepath, dados, colunas, titulo, texto_filtros):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except ImportError:
            return False, "A biblioteca 'reportlab' não está instalada. Instale com: pip install reportlab"

        try:
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()
            
            style_title = ParagraphStyle(name='TitleStyle', parent=styles['Title'], fontSize=16, textColor=colors.HexColor("#0F8C75"), fontName='Helvetica-Bold')
            style_normal = ParagraphStyle(name='NormalStyle', parent=styles['Normal'], fontSize=10)
            style_cell = ParagraphStyle(name='CellText', fontSize=7.5, leading=9, fontName='Helvetica', alignment=0)
            style_header = ParagraphStyle(name='CellHeader', fontSize=8.5, leading=10, fontName='Helvetica-Bold', textColor=colors.whitesmoke, alignment=0)
            
            elements.append(Paragraph(f"<b>{titulo}</b>", style_title))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>Filtros Utilizados:</b> {texto_filtros}", style_normal))
            elements.append(Paragraph(f"<b>Total de Resultados Encontrados:</b> {len(dados)}", style_normal))
            elements.append(Spacer(1, 20))
            
            headers_formatados = [Paragraph(c, style_header) for c in colunas]
            dados_tabela = [headers_formatados]
            
            for row in dados:
                linha_limpa = []
                for item in row:
                    txt = str(item) if item and str(item) != 'None' else '-'
                    txt = txt[:100] + '...' if len(txt) > 100 else txt 
                    linha_limpa.append(Paragraph(txt, style_cell)) 
                dados_tabela.append(linha_limpa)
            
            largura_disp = landscape(A4)[0] - 60 
            
            if "Pareceres" in titulo:
                # 10 Colunas Parecer: Nº, Situação, Processo, Assunto, Solicitante, Evento, Linha, Data Evt, Data, Resp
                pesos = [0.05, 0.09, 0.08, 0.16, 0.12, 0.12, 0.10, 0.08, 0.08, 0.12]
            else:
                # 6 Colunas Pesquisa: ID, Linha, Tipo, Datas, Data Criação, Resp
                pesos = [0.08, 0.25, 0.12, 0.25, 0.15, 0.15]
                
            col_widths = [largura_disp * p for p in pesos]
            
            t = Table(dados_tabela, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F8C75")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F3F5")]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            
            elements.append(t)
            doc.build(elements)
            return True, "Relatório PDF gerado com sucesso!"
        except Exception as e:
            return False, f"Erro interno ao gerar PDF: {e}"