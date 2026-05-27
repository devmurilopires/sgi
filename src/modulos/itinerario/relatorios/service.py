import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from src.modulos.itinerario.relatorios.repository import RelatoriosItinerarioRepository

class RelatoriosItinerarioService:
    def __init__(self):
        self.repo = RelatoriosItinerarioRepository()

    def obter_empresas(self): return self.repo.obter_empresas()
    def obter_linhas(self): return self.repo.obter_linhas()

    def abrir_documento(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return False, "Arquivo não encontrado no diretório de rede."
        try:
            os.startfile(caminho)
            return True, "Abrindo documento..."
        except Exception as e:
            return False, f"Erro ao abrir o arquivo: {e}"

    def excluir(self, tipo_doc, registro_id):
        return self.repo.excluir_registro(tipo_doc, registro_id)

    def exportar_excel(self, tipo_doc, filtros, destino):
        dados = self.repo.buscar_dados_paginados(tipo_doc, filtros, limit=10000)
        if not dados: return False, "Nenhum dado encontrado para os filtros atuais."
        try:
            df = pd.DataFrame(dados)
            if 'id' in df.columns: df = df.drop(columns=['id'])
            df.to_excel(destino, index=False)
            return True, "Relatório Excel gerado com sucesso."
        except Exception as e:
            return False, f"Erro ao gerar Excel: {e}"

    def exportar_pdf(self, tipo_doc, filtros, destino):
        dados = self.repo.buscar_dados_paginados(tipo_doc, filtros, limit=1000)
        if not dados: return False, "Nenhum dado encontrado."
        try:
            doc = SimpleDocTemplate(destino, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
            elementos = []
            estilos = getSampleStyleSheet()
            
            titulo = Paragraph(f"Relatório Gerencial - {tipo_doc} (Itinerário)", estilos['Heading1'])
            elementos.append(titulo)
            elementos.append(Spacer(1, 15))

            if tipo_doc == "OS":
                cabecalho = ["Nº OS", "Solicitante", "Processo", "Tipo", "Evento", "Empresa", "Responsável", "Data"]
                dados_tabela = [cabecalho]
                for d in dados:
                    dt = d.get('data_criacao').strftime("%d/%m/%Y") if d.get('data_criacao') else "-"
                    dados_tabela.append([str(d.get('numero_os','')), str(d.get('solicitante',''))[:25], str(d.get('processo','')), str(d.get('tipo','')), str(d.get('evento',''))[:25], str(d.get('empresa',''))[:30], str(d.get('responsavel','')), dt])
                col_widths = [60, 110, 90, 80, 120, 150, 120, 70]
            else:
                cabecalho = ["Nº Parecer", "Assunto", "Processo", "Decisão", "Solicitante", "Data"]
                dados_tabela = [cabecalho]
                for d in dados:
                    dt = d.get('data_criacao').strftime("%d/%m/%Y") if d.get('data_criacao') else "-"
                    dados_tabela.append([str(d.get('numero_completo','')), str(d.get('assunto',''))[:30], str(d.get('processo','')), str(d.get('decisao','')), str(d.get('solicitante',''))[:25], dt])
                col_widths = [80, 220, 100, 90, 180, 80]

            tabela = Table(dados_tabela, colWidths=col_widths)
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F8C75")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9F9F9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.silver),
            ]))
            
            elementos.append(tabela)
            doc.build(elementos)
            return True, "Relatório PDF gerado com sucesso!"
        except Exception as e:
            return False, f"Erro ao gerar PDF: {e}"