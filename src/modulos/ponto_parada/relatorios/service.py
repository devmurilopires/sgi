import os
import pandas as pd
from reportlab.lib import colors
import shutil
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from src.modulos.ponto_parada.relatorios.repository import RelatorioRepository

class RelatorioService:
    def __init__(self):
        self.repo = RelatorioRepository()

    def obter_bairros(self): return self.repo.obter_bairros()
    def obter_todos_itens(self): return self.repo.obter_todos_itens()

    def abrir_documento(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return False, "Arquivo não encontrado no diretório de rede."
        try:
            os.startfile(caminho)
            return True, "Abrindo documento..."
        except Exception as e:
            return False, f"Erro ao abrir o arquivo: {e}"

    def excluir(self, tipo_doc, registro_id, motivo, excluido_por_nome, caminho_arquivo=None):
        # 1. Apaga do banco de dados e joga na lixeira lógica
        sucesso, msg = self.repo.excluir_registro(tipo_doc, registro_id, motivo, excluido_por_nome)
        
        # 2. BLINDAGEM SÊNIOR: Se apagou do banco, apaga a PASTA física inteira da rede!
        if sucesso and caminho_arquivo and os.path.exists(caminho_arquivo):
            try:
                # Como no Ponto de Parada a OS tem uma pasta própria, pegamos o caminho dessa pasta
                pasta_os = os.path.dirname(caminho_arquivo)
                
                # Apagamos a pasta inteira e tudo o que estiver lá dentro (Word, Imagens anexas, etc)
                if os.path.exists(pasta_os):
                    shutil.rmtree(pasta_os)
            except Exception as e:
                print(f"[Aviso] Banco atualizado, mas falha ao excluir pasta física: {e}")
                
        return sucesso, msg
    
    def atualizar_registro(self, tipo_doc, registro_id, dados):
        return self.repo.atualizar_registro(tipo_doc, registro_id, dados)

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
            
            titulo = Paragraph(f"Relatório Gerencial - {tipo_doc} (Ponto de Parada)", estilos['Heading1'])
            elementos.append(titulo)
            elementos.append(Spacer(1, 15))

            if tipo_doc == "OS":
                cabecalho = ["Nº OS", "Processo", "ID Ponto", "Origem", "Empresa", "Ação", "Item", "Endereço", "Status", "Data"]
                dados_tabela = [cabecalho]
                for d in dados:
                    dt = d.get('data_criacao').strftime("%d/%m/%Y") if d.get('data_criacao') else "-"
                    dados_tabela.append([
                        str(d.get('numero_os','')), str(d.get('processo','')), str(d.get('ponto_principal_id','')), 
                        str(d.get('origem','')), str(d.get('empresa','')), str(d.get('acao','')), str(d.get('item','')), 
                        str(d.get('endereco',''))[:25], str(d.get('status','')), dt
                    ])
                col_widths = [40, 65, 55, 60, 70, 75, 115, 140, 65, 65]
            else:
                # ADICIONADO: Ação e Item no PDF do Parecer
                cabecalho = ["Nº Parecer", "Processo", "Origem", "Decisão", "Ação", "Item", "Endereço", "Responsável", "Data"]
                dados_tabela = [cabecalho]
                for d in dados:
                    dt = d.get('data_criacao').strftime("%d/%m/%Y") if d.get('data_criacao') else "-"
                    dados_tabela.append([
                        str(d.get('numero_completo','')), str(d.get('processo','')), str(d.get('origem','')), 
                        str(d.get('decisao','')), str(d.get('acao','')), str(d.get('item','')), 
                        str(d.get('endereco',''))[:30], str(d.get('responsavel',''))[:15], dt
                    ])
                col_widths = [65, 75, 65, 65, 75, 95, 160, 85, 65]

            tabela = Table(dados_tabela, colWidths=col_widths)
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F8C75")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9F9F9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.silver),
            ]))
            
            elementos.append(tabela)
            doc.build(elementos)
            return True, "Relatório PDF gerado com sucesso!"
        except Exception as e:
            return False, f"Erro ao gerar PDF: {e}"