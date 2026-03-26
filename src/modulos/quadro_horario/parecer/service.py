import os
import shutil
import zipfile
import tempfile
import re
import stat
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape
from src.core.shared.utils import resource_path
from src.modulos.quadro_horario.parecer.repository import ParecerQuadroHorarioRepository

class ParecerQuadroHorarioService:
    def __init__(self):
        self.repo = ParecerQuadroHorarioRepository()
        # Ajuste a raiz de rede conforme o mapeamento da Etufor
        self.pasta_deferido = r"\\172.20.0.57\dados\DIPLA\Quadros de Horários\PARECER TECNICO - SPR\2026\DEFERIDO"
        self.pasta_indeferido = r"\\172.20.0.57\dados\DIPLA\Quadros de Horários\PARECER TECNICO - SPR\2026\INDEFERIDO"

    def buscar_sugestoes_linhas(self):
        return self.repo.buscar_linhas()

    def _limpar_nome_arquivo(self, nome):
        return re.sub(r'[\\/:*?"<>|]', '', nome)

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
                
                # Tenta substituição direta
                if chave in xml_content:
                    xml_content = xml_content.replace(chave, safe_val)
                    continue

                # Tenta substituição com tags fragmentadas do Word
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

    def processar_parecer(self, tipo, dados, linhas, usuario):
        numero = self.repo.obter_proximo_numero_parecer(tipo)
        data_str = datetime.now().strftime("%d/%m/%Y")
        
        # Definição de Texto (Evento vs Linhas)
        evento = dados.get("evento", "").strip()
        data_evento = dados.get("data_evento", "").strip()
        
        if evento:
            evento_text = f"ao evento {evento}"
            if data_evento:
                partes = [p.strip() for p in data_evento.split(",") if p.strip()]
                if len(partes) == 1: evento_text += f" que ocorrerá no dia {partes[0]}"
                elif len(partes) >= 2: evento_text += f" que ocorrerá no dia {partes[0]} até o dia {partes[1]}"
            linhas_text = ""
        else:
            if len(linhas) == 1: linhas_text = f"a linha {linhas[0]}"
            elif len(linhas) > 1: linhas_text = f"as linhas {', '.join(linhas)}"
            else: linhas_text = ""
            evento_text = ""

        evento_ou_linha_text = evento_text or linhas_text

        # Nome do arquivo e pastas
        identificador = evento if evento else ", ".join(linhas)
        if tipo == "DEFERIDO":
            nome_arquivo = f"Parecer N°_{numero:03d}_{dados['assunto']}_{identificador}_({usuario}).docx"
            pasta_base = self.pasta_deferido
            modelo = resource_path("dados/modelo_parecer_deferido.docx")
        else:
            nome_arquivo = f"Parecer N°_{numero:03d}_{dados['assunto']}_INDEFERIDO_({usuario}).docx"
            pasta_base = self.pasta_indeferido
            modelo = resource_path("dados/modelo_parecer_indeferido.docx")

        nome_arquivo = self._limpar_nome_arquivo(nome_arquivo)
        os.makedirs(pasta_base, exist_ok=True)
        caminho_destino = os.path.join(pasta_base, nome_arquivo)

        if not os.path.exists(modelo): return False, f"Modelo {modelo} não encontrado."

        try:
            if os.path.exists(caminho_destino): os.remove(caminho_destino)
            shutil.copyfile(modelo, caminho_destino)
            os.chmod(caminho_destino, stat.S_IWRITE)
        except Exception as e: return False, f"Erro de permissão no arquivo: {e}"

        # Mapeamento de Tags
        mapeamento = {
            "{{NUM_PARECER}}": f"{numero:03d}",
            "{{NUMERO_PARECER}}": f"{numero:03d}",
            "{{DATA}}": data_str,
            "{{PROCESSO}}": dados["processo"],
            "{{ASSUNTO}}": dados["assunto"],
            "{{SOLICITANTE}}": dados["solicitante"],
            "{{SOLICITACAO}}": dados["solicitacao"],
            "{{EVENTO_OU_LINHA}}": evento_ou_linha_text,
            "{{DATA_EVENTO}}": data_evento,
            "{{MOTIVO}}": dados.get("motivo", ""),
            "{{EVENTO}}": evento_text or linhas_text,
            "{{LINHAS}}": linhas_text
        }

        self._substituir_tags_xml(caminho_destino, mapeamento)

        # Salva no Banco
        dados_db = {
            "numero_parecer": numero, "tipo": tipo, "processo": dados["processo"],
            "assunto": dados["assunto"], "solicitacao": dados["solicitacao"],
            "evento": evento, "data_evento": data_evento,
            "solicitante": dados["solicitante"], "linhas": ", ".join(linhas),
            "motivo": dados.get("motivo", ""), "caminho_arquivo": caminho_destino,
            "criado_por": f"%{usuario}%"
        }

        sucesso, msg = self.repo.salvar_parecer_no_banco(dados_db)
        if not sucesso: return False, msg

        return True, f"Parecer gerado com sucesso!\nSalvo em: {nome_arquivo}"