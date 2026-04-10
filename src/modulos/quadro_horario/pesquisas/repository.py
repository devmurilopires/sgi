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

    def salvar_pesquisa(self, linha, tipo, dados_completos, criado_por):
        # A coluna 'titulo' no banco vai guardar a 'linha' selecionada
        query = """
            INSERT INTO spr.pesquisas (titulo, tipo_pesquisa, resultado_json, criado_por, created_at)
            VALUES (%s, %s, %s::jsonb, %s, NOW())
            RETURNING id;
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Converte o dicionário completo (datas + tabelas) para JSON
                    json_str = json.dumps(dados_completos, ensure_ascii=False)
                    cur.execute(query, (linha, tipo, json_str, criado_por))
                    conn.commit()
                    row = cur.fetchone()
                    return True, f"Pesquisa salva com sucesso (ID: {row[0]})."
        except Exception as e:
            return False, f"Erro ao salvar pesquisa no banco: {e}"