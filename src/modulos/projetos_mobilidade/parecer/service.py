import os
from datetime import datetime
from docx import Document
from src.modulos.projetos_mobilidade.parecer.repository import ParecerProjetosMobilidadeRepository
from config.settings import RAIZ_REDE

try:
    from src.core.shared.utils import resource_path
except ImportError:
    def resource_path(path): return path

class ParecerProjetosMobilidadeService:
    def __init__(self):
        self.repo = ParecerProjetosMobilidadeRepository()

    def processar_geracao_parecer(self, dados_form, usuario_logado):
        # 1. Extração de Dados
        tipo = dados_form.get('tipo', 'DEFERIDO').upper()
        origem = dados_form.get('origem', '').strip()
        processo = dados_form.get('processo', '').upper()
        assunto = dados_form.get('assunto', '').upper()
        solicitante = dados_form.get('solicitante', '').upper()
        motivo = dados_form.get('motivo', '') if tipo == "INDEFERIDO" else None
        
        usuario_id = usuario_logado.get('id') if isinstance(usuario_logado, dict) else None
        if not usuario_id:
            return False, "Erro de autenticação: ID do usuário não encontrado na sessão."

        # 2. Persistência no Banco de Dados (Repassando Origem)
        sucesso_db, resultado_db = self.repo.salvar_parecer(tipo, processo, origem, assunto, solicitante, motivo, usuario_id)
        if not sucesso_db:
            return False, f"Falha crítica ao registrar no banco de dados:\n{resultado_db}"
            
        id_parecer, numero_parecer_ano = resultado_db

        # 3. Definição de Caminhos na Rede
        ano_atual = datetime.now().strftime('%Y')
        data_extenso = datetime.now().strftime('%d/%m/%Y')
        
        if not os.path.exists(RAIZ_REDE):
            return False, f"Parecer {numero_parecer_ano} salvo no banco, mas a rede está inacessível para gerar o documento."

        pasta_base = rf"{RAIZ_REDE}\PROJETOS DE MOBILIDADE\{ano_atual}\PARECERES\{tipo}"
        nome_pasta = f"PARECER {numero_parecer_ano.replace('/', '-')} - PROCESSO {processo.replace('/', '-')}"
        caminho_pasta = os.path.join(pasta_base, nome_pasta)
        nome_arquivo = f"PARECER {numero_parecer_ano.replace('/', '-')} - PROJETOS DE MOBILIDADE.docx"
        destino_docx = os.path.join(caminho_pasta, nome_arquivo)

        # 4. Geração do Documento Físico
        modelo_str = "dados/modelo_parecer_deferido_pm.docx" if tipo == "DEFERIDO" else "dados/modelo_parecer_indeferido_pm.docx"
        caminho_modelo = resource_path(modelo_str)

        try:
            os.makedirs(caminho_pasta, exist_ok=True)
            self._gerar_documento(caminho_modelo, destino_docx, numero_parecer_ano, processo, assunto, solicitante, data_extenso, motivo)
            return True, f"Parecer Técnico Nº {numero_parecer_ano} gerado com sucesso!\nSalvo em:\n{destino_docx}"
        except Exception as e:
            return False, f"Parecer registrado no banco, mas falhou ao criar o Word:\n{e}"

    def _gerar_documento(self, modelo_path, destino_path, num_parecer, processo, assunto, solicitante, data_str, motivo):
        doc = Document(modelo_path)
        
        mapeamento = {
            "{{NUM_PARECER}}": num_parecer,
            "{{PROCESSO}}": processo,
            "{{ASSUNTO}}": assunto,
            "{{SOLICITANTE}}": solicitante,
            "{{DATA}}": data_str
        }
        
        if motivo: mapeamento["{{MOTIVO}}"] = motivo

        for paragrafo in doc.paragraphs:
            texto_original = "".join(run.text for run in paragrafo.runs)
            novo_texto = texto_original
            for chave, valor in mapeamento.items():
                if chave in novo_texto: novo_texto = novo_texto.replace(chave, valor)
            if novo_texto != texto_original:
                for run in paragrafo.runs: run.text = ""
                if paragrafo.runs: paragrafo.runs[0].text = novo_texto
                
        doc.save(destino_path)