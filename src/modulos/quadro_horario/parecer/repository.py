from config.database import get_db_connection

class ParecerQuadroHorarioRepository:
    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nome FROM common.linhas ORDER BY nome;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar linhas: {e}")
            return []

    def obter_proximo_numero_parecer(self, tipo):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(MAX(numero_parecer_ano), 0) + 1 
                        FROM common.pareceres_base 
                        WHERE tipo_parecer = %s AND sistema_origem = 'spr' 
                        AND ano = EXTRACT(YEAR FROM CURRENT_DATE)
                    """, (tipo,))
                    resultado = cur.fetchone()
                    return resultado[0] if resultado else 1
        except Exception as e:
            return 1

    def salvar_parecer_no_banco(self, dados_db):
        query_base = """
            INSERT INTO common.pareceres_base (numero_parecer_ano, tipo_parecer, sistema_origem, ano, criado_por_id)
            VALUES (%(numero_parecer)s, %(tipo)s, 'spr', EXTRACT(YEAR FROM CURRENT_DATE), 
            (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %(criado_por)s LIMIT 1))
            RETURNING id;
        """
        query_especifica = """
            INSERT INTO spr.pareceres (
                id, processo, assunto, solicitacao, evento, data_evento, 
                solicitante, linhas_afetadas, motivo_indeferimento, caminho_arquivo
            ) VALUES (
                %(id_base)s, %(processo)s, %(assunto)s, %(solicitacao)s, %(evento)s, %(data_evento)s,
                %(solicitante)s, %(linhas)s, %(motivo)s, %(caminho_arquivo)s
            );
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query_base, dados_db)
                    id_base = cur.fetchone()[0]
                    dados_db["id_base"] = id_base
                    
                    cur.execute(query_especifica, dados_db)
                    conn.commit()
            return True, "Registro salvo no banco com sucesso."
        except Exception as e:
            return False, f"Erro ao salvar no banco: {e}"