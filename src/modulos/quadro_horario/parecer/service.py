import os
import shutil
import zipfile
import tempfile
import re
import stat
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape
from config.settings import RAIZ_REDE
from src.core.shared.utils import resource_path
from src.modulos.quadro_horario.parecer.repository import ParecerQuadroHorarioRepository

class ParecerQuadroHorarioService:
    def __init__(self):
        self.repo = ParecerQuadroHorarioRepository()
        self.ano_atual = datetime.now().year
        self.pasta_deferido = rf"{RAIZ_REDE}\QUADRO DE HORARIO\{self.ano_atual}\PARECERES TECNICOS\DEFERIDO"
        self.pasta_indeferido = rf"{RAIZ_REDE}\QUADRO DE HORARIO\{self.ano_atual}\PARECERES TECNICOS\INDEFERIDO"

    def buscar_sugestoes_linhas(self):
        return self.repo.buscar_linhas()

    def _limpar_nome_arquivo(self, nome):
        return re.sub(r'[\\/:*?"<>|]', '', nome)

    def formatar_lista_com_e(self, lista):
        lst = [s for s in lista if s]
        if not lst: return ""
        if len(lst) == 1: return lst[0]
        if len(lst) == 2: return f"{lst[0]} e {lst[1]}"
        return ", ".join(lst[:-1]) + f" e {lst[-1]}"

    def _substituir_tags_xml(self, caminho_docx, mapeamento):
        temp_dir = tempfile.mkdtemp()
        temp_docx = os.path.join(temp_dir, "temp.docx")
        shutil.copyfile(caminho_docx, temp_docx)

        with zipfile.ZipFile(temp_docx, 'r') as zip_in:
            zip_in.extractall(temp_dir)

        document_xml_path = os.path.join(temp_dir, "word", "document.xml")
        if os.path.exists(document_xml_path):
            with open(document_xml_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

            for chave, valor in mapeamento.items():
                safe_val = xml_escape(str(valor or ""))
                
                if chave in xml_content:
                    xml_content = xml_content.replace(chave, safe_val)
                    continue

                pattern = "".join(re.escape(ch) + r"(?:<[^>]+>)*" for ch in chave)
                try:
                    new_xml, n = re.subn(pattern, safe_val, xml_content, flags=re.IGNORECASE)
                    if n > 0: xml_content = new_xml
                except: pass

            with open(document_xml_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

        with zipfile.ZipFile(caminho_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zip_out:
            for pasta_raiz, _, arquivos in os.walk(temp_dir):
                for arquivo in arquivos:
                    if arquivo == "temp.docx": continue
                    caminho_abs = os.path.join(pasta_raiz, arquivo)
                    zip_out.write(caminho_abs, os.path.relpath(caminho_abs, temp_dir))
        shutil.rmtree(temp_dir)

    def processar_parecer(self, tipo, dados_form, linhas, usuario):
        # ATUALIZADO: Remoção do parâmetro 'tipo' na contagem, agora unificada.
        numero = self.repo.obter_proximo_numero_parecer()
        data_str = datetime.now().strftime("%d/%m/%Y")
        
        evento = dados_form.get("evento", "").strip()
        
        # --- PREPARAÇÃO DE TEXTO PARA O WORD ---
        data_text = ""
        datas_raw = dados_form.get("datas", [])
        modo_data = dados_form.get("modo_data", "PERIODO")

        if evento and datas_raw:
            if modo_data == "ISOLADOS":
                data_text = "nos dias " + self.formatar_lista_com_e(datas_raw) if len(datas_raw) > 1 else f"no dia {datas_raw[0]}"
            else:
                data_text = f"no dia {datas_raw[0]}" if len(datas_raw) == 1 else f"do dia {datas_raw[0]} até o dia {datas_raw[1]}"

        # --- PREPARAÇÃO DE DADOS PARA O BANCO DE DADOS ---
        # 1. Converter primeira data string para objeto Date (Coluna data_evento)
        data_db = None
        if datas_raw:
            try:
                # O banco aceita 1 única data. Pegamos o primeiro dia do evento.
                data_db = datetime.strptime(datas_raw[0], "%d/%m/%Y").date()
            except ValueError:
                pass
        
        # 2. Extrair apenas os Códigos das Linhas (para a tabela pareceres_linhas)
        codigos_linhas = []
        for linha in linhas:
            if " - " in linha:
                codigos_linhas.append(linha.split(" - ")[0].strip())

        # Configuração de Arquivos
        if evento:
            evento_text = f"ao evento {evento}"
            if data_text: evento_text += f" que ocorrerá {data_text}"
            linhas_text = ""
        else:
            if len(linhas) == 1: linhas_text = f"a linha {linhas[0]}"
            elif len(linhas) > 1: linhas_text = f"as linhas {self.formatar_lista_com_e(linhas)}"
            else: linhas_text = ""
            evento_text = ""

        evento_ou_linha_text = evento_text or linhas_text
        identificador = evento if evento else ", ".join(codigos_linhas)

        if tipo == "DEFERIDO":
            nome_arquivo = f"Parecer N°_{numero:03d}_{dados_form['assunto']}_{identificador}_({usuario}).docx"
            pasta_base = self.pasta_deferido
            modelo = resource_path("dados/modelo_parecer_deferido_qh.docx")
        else:
            nome_arquivo = f"Parecer N°_{numero:03d}_{dados_form['assunto']}_INDEFERIDO_({usuario}).docx"
            pasta_base = self.pasta_indeferido
            modelo = resource_path("dados/modelo_parecer_indeferido_qh.docx")

        nome_arquivo = self._limpar_nome_arquivo(nome_arquivo)
        os.makedirs(pasta_base, exist_ok=True)
        caminho_destino = os.path.join(pasta_base, nome_arquivo)

        if not os.path.exists(modelo): return False, f"Modelo {modelo} não encontrado."

        try:
            if os.path.exists(caminho_destino): os.remove(caminho_destino)
            shutil.copyfile(modelo, caminho_destino)
            os.chmod(caminho_destino, stat.S_IWRITE)
        except Exception as e: return False, f"Erro de permissão no arquivo: {e}"

        mapeamento = {
            "{{NUM_PARECER}}": f"{numero:03d}",
            "{{NUMERO_PARECER}}": f"{numero:03d}",
            "{{DATA}}": data_str,
            "{{PROCESSO}}": dados_form["processo"],
            "{{ASSUNTO}}": dados_form["assunto"],
            "{{SOLICITANTE}}": dados_form["solicitante"],
            "{{EVENTO_OU_LINHA}}": evento_ou_linha_text,
            "{{DATA_EVENTO}}": data_text,
            "{{MOTIVO}}": dados_form.get("motivo", ""),
            "{{EVENTO}}": evento_text or linhas_text,
            "{{LINHAS}}": linhas_text
        }

        self._substituir_tags_xml(caminho_destino, mapeamento)

        # ATUALIZADO: Payload enviado ao repositório alinhado com a nova estrutura DB
        dados_db = {
            "numero_parecer": numero, 
            "tipo": tipo, 
            "processo": dados_form["processo"],
            "origem": dados_form.get("origem", ""),
            "assunto": dados_form["assunto"],
            "evento": evento, 
            "data_db": data_db,  # Enviado como datetime.date para postgres
            "solicitante": dados_form["solicitante"], 
            "codigos_linhas": codigos_linhas, # Array de Códigos
            "motivo": dados_form.get("motivo", ""), 
            "caminho_arquivo": caminho_destino, # Encaminhado para a base
            "criado_por": f"%{usuario}%"
        }

        sucesso, msg = self.repo.salvar_parecer_no_banco(dados_db)
        if not sucesso: 
            return False, msg

        return True, f"Parecer Técnico gerado e salvo no banco com sucesso!\nSalvo em: {nome_arquivo}"