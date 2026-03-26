from config.database import get_db_connection
import json

class PesquisaQuadroHorarioRepository:
    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nome FROM common.linhas ORDER BY nome;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            return []

    def salvar_pesquisa(self, titulo, tipo, dados_tabelas, criado_por):
        query = """
            INSERT INTO spr.pesquisas (titulo, tipo_pesquisa, resultado_json, criado_por, created_at)
            VALUES (%s, %s, %s::jsonb, %s, NOW())
            RETURNING id;
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Converte as tabelas para JSON string antes de mandar pro Postgres
                    json_str = json.dumps(dados_tabelas, ensure_ascii=False)
                    cur.execute(query, (titulo, tipo, json_str, criado_por))
                    conn.commit()
                    row = cur.fetchone()
                    return True, f"Pesquisa salva com sucesso (ID: {row[0]})."
        except Exception as e:
            return False, f"Erro ao salvar pesquisa no banco: {e}"