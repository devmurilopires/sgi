import os
import shutil
import sys
import subprocess
from datetime import datetime
import pandas as pd
from src.modulos.ponto_parada.relatorios.repository import RelatorioRepository
from config.settings import RAIZ_REDE

class RelatorioService:
    def __init__(self):
        self.repo = RelatorioRepository()

    def buscar_dados(self, tipo_relatorio, filtros):
        if tipo_relatorio == "OS":
            dados_brutos = self.repo.buscar_ordens_servico(filtros)
            return self._formatar_dados_os(dados_brutos)
        elif tipo_relatorio == "PARECER":
            dados_brutos = self.repo.buscar_pareceres(filtros)
            return self._formatar_dados_parecer(dados_brutos)
        return []

    def _formatar_dados_os(self, dados_brutos):
        dados_formatados = []
        for linha in dados_brutos:
            (id_banco, numero, dt_criacao, id_princ, ids_adicionais, acao, item, logradouro, bairro, status_conclusao, dt_conclusao, pasta, resp, origem) = linha
            
            todos_ids = [id_princ] if id_princ else []
            if ids_adicionais and ids_adicionais != 'None':
                todos_ids.extend([i.strip() for i in ids_adicionais.split('-') if i.strip() != id_princ])
            
            status = status_conclusao or "NÃO"
            if dt_criacao:
                d_criacao = dt_criacao.date() if type(dt_criacao) is datetime else dt_criacao
                if status == "NÃO":
                    dias_aberto = f"{(datetime.now().date() - d_criacao).days} dias"
                    status_formatado = f"🔴 Aberta ({dias_aberto})"
                elif status in ["SIM", "NÃO AUTORIZADA"] and dt_conclusao:
                    d_conclusao = dt_conclusao.date() if type(dt_conclusao) is datetime else dt_conclusao
                    dias_aberto = f"{(d_conclusao - d_criacao).days} dias"
                    status_formatado = f"✅ SIM ({dias_aberto})" if status == "SIM" else f"🚫 Não Aut. ({dias_aberto})"
                else:
                    status_formatado = "✅ SIM" if status == "SIM" else ("🚫 Não Aut." if status == "NÃO AUTORIZADA" else "🔴 Aberta")
            else:
                status_formatado = status

            caminho_arquivo = self._reconstruir_caminho_os(pasta, numero, dt_criacao, todos_ids)
            
            origem_fmt = str(origem).upper() if origem else "SPU"
            acao_fmt = str(acao).upper() if acao else "-"
            item_fmt = str(item).upper() if item else "-"
            end_fmt = str(logradouro) if logradouro else "-"

            dados_formatados.append([
                id_banco, # 0 -> ID verdadeiro escondido
                numero, dt_criacao.strftime("%d/%m/%Y") if dt_criacao else "-",
                ", ".join(todos_ids), origem_fmt, acao_fmt, item_fmt, end_fmt, status_formatado, 
                pasta, resp, caminho_arquivo
            ])
        return dados_formatados

    def _formatar_dados_parecer(self, dados_brutos):
        dados_formatados = []
        for linha in dados_brutos:
            (id_banco, num, tipo, proc, assun, ids, solic, endereco, origem, dt_criacao, resp, caminho) = linha
            dt_str = dt_criacao.strftime("%d/%m/%Y") if dt_criacao else "-"
            origem_fmt = str(origem).upper() if origem else "SPU"
            
            dados_formatados.append([
                id_banco, # 0 -> ID verdadeiro escondido
                num, tipo, origem_fmt, proc or "-", assun or "-", ids or "-", solic or "-", endereco or "-", dt_str, resp or "-", caminho
            ])
        return dados_formatados

    def _reconstruir_caminho_os(self, pasta, numero, dt_criacao, ids_list):
        if not pasta or pasta == "-": return None
        if not dt_criacao: return None
        mes, ano = dt_criacao.strftime("%m"), dt_criacao.strftime("%Y")
        if "URBMIDIA" in pasta.upper():
            base = rf"{RAIZ_REDE}\SIGP\{ano}\ORDENS DE SERVICO\URBMIDIA"
        else:
            base = rf"{RAIZ_REDE}\SIGP\{ano}\ORDENS DE SERVICO\PROXIMA PARADA"
        str_ids = "-".join(ids_list) if ids_list else "EMERGENCIA"
        return os.path.join(base, f"{str(numero).zfill(3)}-{mes}-{ano}-ID{str_ids}", f"O.S {str(numero).zfill(3)}-{ano}-ID{str_ids}.docx")

    def abrir_arquivo(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return False, f"Arquivo não encontrado no caminho:\n{caminho}"
        try:
            if os.name == "nt": os.startfile(caminho)
            else: subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", caminho])
            return True, "Aberto com sucesso"
        except Exception as e: return False, f"Erro ao abrir: {e}"

    def baixar_arquivo(self, caminho_origem, caminho_destino):
        if not caminho_origem or not os.path.exists(caminho_origem):
            return False, "O arquivo original não foi encontrado."
        try:
            shutil.copy2(caminho_origem, caminho_destino)
            return True, "Download concluído com sucesso!"
        except Exception as e:
            return False, f"Erro ao fazer download: {str(e)}"

    def buscar_detalhes_para_edicao(self, tipo_relatorio, id_banco):
        if tipo_relatorio == "OS": return self.repo.buscar_detalhes_os(id_banco)
        else: return self.repo.buscar_detalhes_parecer(id_banco)

    def salvar_edicao(self, tipo_relatorio, id_banco, dados_novos):
        if tipo_relatorio == "OS": return self.repo.atualizar_os(id_banco, dados_novos)
        else: return self.repo.atualizar_parecer(id_banco, dados_novos)

    def excluir_registro(self, tipo_relatorio, id_banco, motivo, usuario_logado):
        import json 
        if tipo_relatorio == "OS":
            dados_completos = self.repo.buscar_detalhes_os(id_banco)
            if not dados_completos: return False, "Não foi possível resgatar os dados para o Log."
            pasta_para_deletar = None
            dados_os = self.repo.obter_dados_para_caminho_os(id_banco)
            if dados_os:
                numero_real, dt_criacao, id_princ, ids_adicionais, pasta = dados_os
                todos_ids = [id_princ] if id_princ else []
                if ids_adicionais and ids_adicionais != 'None':
                    todos_ids.extend([i.strip() for i in ids_adicionais.split('-') if i.strip() != id_princ])
                caminho_arquivo = self._reconstruir_caminho_os(pasta, numero_real, dt_criacao, todos_ids)
                if caminho_arquivo: pasta_para_deletar = os.path.dirname(caminho_arquivo)
            sucesso, msg = self.repo.excluir_e_logar_os(id_banco, dados_completos, caminho_arquivo, motivo, usuario_logado)
            if sucesso and pasta_para_deletar and os.path.exists(pasta_para_deletar):
                try: shutil.rmtree(pasta_para_deletar)
                except: pass
            return sucesso, msg
        else: 
            dados_completos = self.repo.buscar_detalhes_parecer(id_banco)
            caminho_arquivo = self.repo.obter_caminho_parecer(id_banco)
            sucesso, msg = self.repo.excluir_e_logar_parecer(id_banco, dados_completos, caminho_arquivo, motivo, usuario_logado)
            if sucesso and caminho_arquivo and os.path.exists(caminho_arquivo):
                try: os.remove(caminho_arquivo)
                except: pass
            return sucesso, msg

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
            return False, "A biblioteca 'reportlab' não está instalada no sistema. Instale com: pip install reportlab"

        try:
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            elements = []
            styles = getSampleStyleSheet()
            
            # --- ESTILOS CUSTOMIZADOS PARA QUEBRA DE TEXTO ---
            style_title = ParagraphStyle(name='TitleStyle', parent=styles['Title'], fontSize=16, textColor=colors.HexColor("#0F8C75"), fontName='Helvetica-Bold')
            style_normal = ParagraphStyle(name='NormalStyle', parent=styles['Normal'], fontSize=10)
            
            # Estilo das células: O segredo para o texto quebrar e não vazar (Word Wrap)
            style_cell = ParagraphStyle(name='CellText', fontSize=7.5, leading=9, fontName='Helvetica', alignment=0)
            style_header = ParagraphStyle(name='CellHeader', fontSize=8.5, leading=10, fontName='Helvetica-Bold', textColor=colors.whitesmoke, alignment=0)
            
            elements.append(Paragraph(f"<b>{titulo}</b>", style_title))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>Filtros Utilizados:</b> {texto_filtros}", style_normal))
            elements.append(Paragraph(f"<b>Total de Resultados Encontrados:</b> {len(dados)}", style_normal))
            elements.append(Spacer(1, 20))
            
            # Envolve os cabeçalhos no estilo para padronizar
            headers_formatados = [Paragraph(c, style_header) for c in colunas]
            dados_tabela = [headers_formatados]
            
            for row in dados:
                linha_limpa = []
                for item in row:
                    txt = str(item) if item and str(item) != 'None' else '-'
                    txt = txt[:80] + '...' if len(txt) > 80 else txt # Evita strings absurdamente colossais
                    
                    # Ao injetar um Paragraph na tabela, ele quebra a linha automaticamente
                    linha_limpa.append(Paragraph(txt, style_cell)) 
                dados_tabela.append(linha_limpa)
            
            # --- LARGURAS PROPORCIONAIS INTELIGENTES ---
            largura_disp = landscape(A4)[0] - 60 # Largura total da página menos as margens
            
            if "Ordens de Serviço" in titulo:
                # 10 colunas da OS: "Nº", "Data", "ID(s)", "Origem", "Ação", "Item", "Endereço", "Status", "Pasta", "Criador"
                # Distribuímos 100% da largura (1.0) conforme a necessidade de cada coluna
                pesos = [0.05, 0.08, 0.08, 0.06, 0.10, 0.12, 0.23, 0.12, 0.08, 0.08]
            else:
                # 10 colunas do Parecer: "Nº", "Tipo", "Origem", "Processo", "Assunto", "ID(s)", "Solicitante", "Endereço", "Data", "Criador"
                pesos = [0.05, 0.08, 0.06, 0.09, 0.16, 0.06, 0.14, 0.18, 0.08, 0.10]
                
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