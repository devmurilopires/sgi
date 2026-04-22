import psycopg2
from config.database import get_db_connection
import os
import re

class OSItinerarioRepository:
    def buscar_empresas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Aponta para o novo schema 'common' e filtra as ativas
                    cur.execute("SELECT nome FROM common.empresas WHERE ativo = TRUE ORDER BY nome;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e: 
            print(f"Erro ao buscar empresas: {e}")
            return []

    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Concatena o código e o nome da linha diretamente na query
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas WHERE ativo = TRUE ORDER BY codigo;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar linhas: {e}")
            return []

    def obter_proximo_numero_os(self, pasta_destino):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM siga.ordens_servico WHERE ano = EXTRACT(YEAR FROM CURRENT_DATE)")
                    resultado = cur.fetchone()
                    return resultado[0] if resultado else 1
        except Exception as e:
            print(f"Erro ao buscar próximo número da OS Itinerário no banco: {e}")
            return 1

    def salvar_os_itinerario(self, dados_db):
        query = """
            INSERT INTO itinerario.ordens_servico (
                numero, ano, tipo_evento, processo_adm, origem, empresas_text, endereco,
                horario_inicio, horario_fim, linhas_text, ruas_ida, ruas_volta, evento,
                caminho_arquivo, responsavel, nome_corrida, km_impactado, tipo_obra, data_criacao
            ) VALUES (
                %(num_os)s, %(ano)s, %(tipo)s, %(processo)s, %(origem)s, %(empresas_text)s, %(endereco)s,
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