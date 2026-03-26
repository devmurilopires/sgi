import psycopg2
from config.database import get_db_connection
import os
import re

class OSItinerarioRepository:
    def buscar_empresas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nome FROM public.empresas ORDER BY nome;")
                    return [r[0] for r in cur.fetchall()]
        except: return []

    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nome FROM common.linhas ORDER BY nome;")
                    return [r[0] for r in cur.fetchall()]
        except: return []

    def obter_proximo_numero_os(self, pasta_destino):
        try:
            padrao = re.compile(r"OS Nº(\d+)\s+de", re.IGNORECASE)
            max_num = 0
            if os.path.isdir(pasta_destino):
                for nome in os.listdir(pasta_destino):
                    m = padrao.search(nome)
                    if m:
                        try:
                            n = int(m.group(1))
                            if n > max_num: max_num = n
                        except: pass
            return max_num + 1
        except: return 1

    def salvar_os_itinerario(self, dados_db):
        query = """
            INSERT INTO siga.ordens_servico (
                numero, ano, tipo_evento, processo_adm, empresas_text, endereco,
                horario_inicio, horario_fim, linhas_text, ruas_ida, ruas_volta, evento,
                caminho_arquivo, responsavel, nome_corrida, km_impactado, tipo_obra, data_criacao
            ) VALUES (
                %(num_os)s, %(ano)s, %(tipo)s, %(processo)s, %(empresas_text)s, %(endereco)s,
                %(horario_inicio)s, %(horario_final)s, %(linhas_text)s, %(ruas_ida)s, %(ruas_volta)s, %(evento)s,
                %(docx_path)s, %(criado_por)s, %(nome_corrida)s, NULLIF(%(km)s, '')::NUMERIC, %(tipo_obra)s, NOW()
            ) RETURNING id;
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, dados_db)
                    conn.commit()
            return True, "Registro salvo no banco com sucesso."
        except Exception as e:
            return False, f"Erro ao salvar no banco: {e}"