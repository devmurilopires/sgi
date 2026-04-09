import os
import subprocess
import sys
import shutil
import pandas as pd
from src.modulos.itinerario.relatorios.repository import RelatorioItinerarioRepository

class RelatorioItinerarioService:
    def __init__(self):
        self.repo = RelatorioItinerarioRepository()

    def buscar_sugestoes(self, tipo):
        if tipo == "EMPRESAS": return self.repo.buscar_empresas()
        if tipo == "LINHAS": return self.repo.buscar_linhas()
        return []

    def buscar_dados(self, tipo_relatorio, filtros):
        if tipo_relatorio == "OS":
            return self.repo.buscar_ordens_servico(filtros)
        elif tipo_relatorio == "PARECER":
            return self.repo.buscar_pareceres(filtros)
        return []

    def buscar_detalhes(self, tipo_relatorio, id_banco):
        if tipo_relatorio == "OS":
            return self.repo.buscar_detalhes_os(id_banco)
        return self.repo.buscar_detalhes_parecer(id_banco)

    def excluir_registro(self, tipo_relatorio, id_banco, motivo, usuario_logado):
        return self.repo.excluir_e_logar(id_banco, tipo_relatorio, motivo, usuario_logado)

    def abrir_arquivo(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return False, "O arquivo não foi encontrado na rede ou foi movido."
        try:
            if os.name == 'nt':
                os.startfile(caminho)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.Popen([opener, caminho])
            return True, ""
        except Exception as e:
            return False, f"Não foi possível abrir: {str(e)}"

    def baixar_arquivo(self, caminho_origem, caminho_destino):
        if not caminho_origem or not os.path.exists(caminho_origem):
            return False, "O arquivo original não foi encontrado na rede."
        try:
            shutil.copy2(caminho_origem, caminho_destino)
            return True, "Download concluído com sucesso!"
        except Exception as e:
            return False, f"Erro ao fazer download: {str(e)}"

    def exportar_excel(self, filepath, dados, colunas, titulo, texto_filtros):
        try:
            df = pd.DataFrame(dados, columns=colunas)
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                workbook = writer.book
                worksheet = writer.sheets.setdefault('Relatorio', workbook.add_worksheet('Relatorio'))
                
                bold_format = workbook.add_format({'bold': True, 'font_size': 14})
                normal_bold = workbook.add_format({'bold': True})
                
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
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            return False, "A biblioteca 'reportlab' não está instalada no sistema.\nAbra o terminal e digite:\npip install reportlab"

        try:
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()
            
            elements.append(Paragraph(f"<b><font size=16>{titulo}</font></b>", styles['Title']))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>Filtros Utilizados:</b> {texto_filtros}", styles['Normal']))
            elements.append(Paragraph(f"<b>Total de Resultados Encontrados:</b> {len(dados)}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            dados_tabela = [colunas]
            for row in dados:
                linha_limpa = []
                for item in row:
                    txt = str(item) if item and str(item) != 'None' else '-'
                    linha_limpa.append(txt[:40] + '...' if len(txt) > 40 else txt) # Trunca textos muito longos
                dados_tabela.append(linha_limpa)
            
            largura_disp = landscape(A4)[0] - 60
            col_widths = [largura_disp / len(colunas)] * len(colunas)
            
            t = Table(dados_tabela, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F8C75")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F3F5")]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(t)
            doc.build(elements)
            return True, "Relatório PDF gerado com sucesso!"
        except Exception as e:
            return False, f"Erro interno ao gerar PDF: {e}"