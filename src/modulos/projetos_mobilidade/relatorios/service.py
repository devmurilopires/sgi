import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from src.modulos.projetos_mobilidade.relatorios.repository import RelatorioProjetosMobilidadeRepository

class RelatorioProjetosMobilidadeService:
    def __init__(self):
        self.repo = RelatorioProjetosMobilidadeRepository()

    # MODIFICAÇÃO: Função de Abertura Inserida!
    def abrir_documento(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return False, "Arquivo não encontrado no diretório de rede."
        try:
            os.startfile(caminho)
            return True, "Abrindo documento..."
        except Exception as e:
            return False, f"Erro ao abrir o arquivo: {e}"

    def excluir(self, registro_id, motivo, excluido_por_nome):
        return self.repo.excluir_registro(registro_id, motivo, excluido_por_nome)
    
    def atualizar_registro(self, registro_id, dados):
        return self.repo.atualizar_registro(registro_id, dados)

    def exportar_excel(self, filtros, destino):
        dados = self.repo.buscar_dados_paginados(filtros, limit=10000)
        if not dados: return False, "Nenhum dado encontrado para os filtros atuais."
        try:
            df = pd.DataFrame(dados)
            if 'id' in df.columns: df.drop(columns=['id'], inplace=True)
            if 'caminho_arquivo' in df.columns: df.drop(columns=['caminho_arquivo'], inplace=True)
            
            if 'data_criacao' in df.columns:
                df['data_criacao'] = pd.to_datetime(df['data_criacao']).dt.strftime("%d/%m/%Y")
            
            df.columns = [str(c).replace("_", " ").title() for c in df.columns]
            df.to_excel(destino, index=False)
            return True, "Relatório Excel exportado com sucesso."
        except Exception as e:
            return False, f"Erro ao gerar Excel: {e}"

    def exportar_pdf(self, filtros, destino):
        dados = self.repo.buscar_dados_paginados(filtros, limit=10000)
        if not dados: return False, "Nenhum dado encontrado para os filtros atuais."
        try:
            doc = SimpleDocTemplate(destino, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elementos = []
            estilos = getSampleStyleSheet()

            elementos.append(Paragraph("Relatório Gerencial - Pareceres (Projetos de Mobilidade)", estilos['Title']))
            elementos.append(Spacer(1, 20))

            cabecalho = ["Nº Parecer", "Processo", "Origem", "Assunto", "Decisão", "Solicitante", "Data Criação"]
            dados_tabela = [cabecalho]
            
            for d in dados:
                dt = d.get('data_criacao').strftime("%d/%m/%Y") if d.get('data_criacao') else "-"
                dados_tabela.append([
                    str(d.get('numero_completo', '')), 
                    str(d.get('processo', '')), 
                    str(d.get('origem', '')),
                    str(d.get('assunto', ''))[:35],
                    str(d.get('decisao', '')), 
                    str(d.get('solicitante', ''))[:20], 
                    dt
                ])
                
            col_widths = [80, 90, 100, 200, 80, 130, 80]

            tabela = Table(dados_tabela, colWidths=col_widths)
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F8C75")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD"))
            ]))
            
            elementos.append(tabela)
            doc.build(elementos)
            return True, "Relatório PDF exportado com sucesso."
        except Exception as e:
            return False, f"Erro ao gerar PDF: {e}"