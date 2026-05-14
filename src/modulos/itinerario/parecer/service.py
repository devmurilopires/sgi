import os
import shutil
import zipfile
import tempfile
import re
import stat
from datetime import datetime
from config.settings import RAIZ_REDE
from src.core.shared.utils import resource_path
from src.modulos.itinerario.parecer.repository import ParecerItinerarioRepository

class ParecerItinerarioService:
    def __init__(self):
        self.repo = ParecerItinerarioRepository()
        self.ano_atual = datetime.now().year
        self.pasta_deferido = rf"{RAIZ_REDE}\ITINERARIO\{self.ano_atual}\PARECERES TECNICOS\DEFERIDO"
        self.pasta_indeferido = rf"{RAIZ_REDE}\ITINERARIO\{self.ano_atual}\PARECERES TECNICOS\INDEFERIDO"

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
        temp_copy = os.path.join(temp_dir, "temp_copy.docx")
        shutil.copyfile(caminho_docx, temp_copy)
        with zipfile.ZipFile(temp_copy, 'r') as zip_in: zip_in.extractall(temp_dir)
        document_xml_path = os.path.join(temp_dir, "word", "document.xml")

        if os.path.exists(document_xml_path):
            with open(document_xml_path, "r", encoding="utf-8") as f: xml_content = f.read()
            def substituir_completo(xml, chave, valor):
                padrao = re.compile(r"(<w:t[^>]*>.*?</w:t>)", re.DOTALL)
                partes = padrao.split(xml); buffer = ""; resultado = []
                for parte in partes:
                    if parte.startswith("<w:t"):
                        texto = re.sub(r"</?w:t[^>]*>", "", parte); buffer += texto; resultado.append(parte)
                    else: buffer += parte; resultado.append(parte)
                texto_total = "".join(resultado)
                if chave in texto_total: return texto_total.replace(chave, valor)
                return xml
            for chave, valor in mapeamento.items():
                if chave in xml_content: xml_content = xml_content.replace(chave, valor)
                else: xml_content = substituir_completo(xml_content, chave, valor)
            with open(document_xml_path, "w", encoding="utf-8") as f: f.write(xml_content)

        with zipfile.ZipFile(caminho_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zip_out:
            for pasta_raiz, _, arquivos in os.walk(temp_dir):
                for arquivo in arquivos:
                    if arquivo == "temp_copy.docx": continue
                    caminho_abs = os.path.join(pasta_raiz, arquivo)
                    zip_out.write(caminho_abs, os.path.relpath(caminho_abs, temp_dir))
        shutil.rmtree(temp_dir)

    def processar_parecer(self, tipo, dados_form, linhas, usuario):
        numero_parecer = self.repo.obter_proximo_numero_parecer(tipo)
        data_str = datetime.now().strftime("%d/%m/%Y")
        
        nome_evento_arq = dados_form['evento'] if dados_form['evento'] else "SemEvento"
        nome_arquivo = f"Parecer N°_{numero_parecer:03d}_{data_str.replace('/', '-')}_{dados_form['assunto']}_{nome_evento_arq}_({usuario}).docx"
        nome_arquivo = self._limpar_nome_arquivo(nome_arquivo)

        pasta_base = self.pasta_deferido if tipo == "DEFERIDO" else self.pasta_indeferido
        os.makedirs(pasta_base, exist_ok=True)
        caminho_destino = os.path.join(pasta_base, nome_arquivo)
        
        modelo_path = resource_path(f"dados/modelo_parecer_{tipo.lower()}_it.docx")
        if not os.path.exists(modelo_path):
            return False, f"Modelo {modelo_path} não encontrado."

        try:
            if os.path.exists(caminho_destino): os.remove(caminho_destino)
            shutil.copyfile(modelo_path, caminho_destino)
            os.chmod(caminho_destino, stat.S_IWRITE)
        except Exception as e:
            return False, f"Falha ao manipular o arquivo: {e}"

        # --- TRATAMENTO INTELIGENTE DA DATA NO WORD ---
        data_text = ""
        datas_raw = dados_form.get("datas", [])
        modo_data = dados_form.get("modo_data", "PERIODO")

        if datas_raw:
            if modo_data == "ISOLADOS":
                data_text = "nos dias " + self.formatar_lista_com_e(datas_raw) if len(datas_raw) > 1 else f"no dia {datas_raw[0]}"
            else:
                data_text = f"no dia {datas_raw[0]}" if len(datas_raw) == 1 else f"no período de {datas_raw[0]} a {datas_raw[1]}"

        mapeamento = {
            "{{NUMERO_PARECER}}": f"{numero_parecer:03d}",
            "{{DATA}}": data_str,
            "{{PROCESSO}}": dados_form["processo"],
            "{{ASSUNTO}}": dados_form["assunto"],
            "{{SOLICITANTE}}": dados_form["solicitante"],
            "{{ENDERECO}}": dados_form["endereco"]
        }

        if tipo == "DEFERIDO":
            texto_desvio = f"Informamos que este evento interfere no itinerário das linhas: {', '.join(linhas)}. Do Sistema de Transporte Coletivo e, portanto, deve ser feita uma ordem de serviço autorizando o desvio das mesmas." if linhas else "Informamos que este evento interfere no itinerário de algumas linhas do sistema de transporte coletivo de Fortaleza, portanto, deve ser feita uma ordem de serviço autorizando o desvio das mesmas."
            mapeamento.update({
                "{{EVENTO}}": f",para realização do evento {dados_form['evento']}," if dados_form["evento"] else "",
                "{{DATA_EVENTO}}": f", que acontecerá {data_text}" if data_text else "",
                "{{PERIODO}}": f", das {dados_form['periodo']} horas" if dados_form["periodo"] else "",
                "{{TEXTO_DESVIO}}": texto_desvio
            })
        else:
            mapeamento.update({
                "{{EVENTO}}": f"em razão da realização do evento {dados_form['evento']}," if dados_form["evento"] else "",
                "{{DATA_EVENTO}}": f"que ocorrerá {data_text}" if data_text else "",
                "{{PERIODO}}": f", no período das {dados_form['periodo']} horas" if dados_form["periodo"] else "",
                "{{MOTIVO}}": dados_form["motivo"]
            })

        self._substituir_tags_xml(caminho_destino, mapeamento)

        # --- MODIFICAÇÃO: TRATAMENTO DE DADOS PARA O BANCO (SGI v2.2) ---
        # 1. Transformar data string em objeto datetime.date
        data_db = None
        if datas_raw:
            try:
                data_db = datetime.strptime(datas_raw[0], "%d/%m/%Y").date()
            except ValueError: pass

        # 2. Extrair apenas o código numérico das linhas
        codigos_linhas = []
        if tipo == "DEFERIDO":
            for linha in linhas:
                if " - " in linha:
                    codigos_linhas.append(linha.split(" - ")[0].strip())

        dados_db = {
            "numero_parecer": numero_parecer, 
            "tipo": tipo, 
            "processo": dados_form["processo"],
            "origem": dados_form["origem"], 
            "assunto": dados_form["assunto"], 
            "evento": dados_form["evento"],
            "data_db": data_db, # Enviando tipo Date para a coluna do BD
            "periodo": dados_form["periodo"],
            "endereco": dados_form["endereco"], 
            "solicitante": dados_form["solicitante"],
            "codigos_linhas": codigos_linhas, # Array para o relacionamento N:M
            "motivo": dados_form["motivo"] if tipo == "INDEFERIDO" else "",
            "caminho_arquivo": caminho_destino, 
            "criado_por": f"%{usuario}%"
        }

        sucesso, msg = self.repo.salvar_parecer_no_banco(dados_db)
        if not sucesso: return False, msg

        return True, f"Parecer {tipo.lower()} gerado!\nSalvo em: {nome_arquivo}"