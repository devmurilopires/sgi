from config.database import get_db_connection
import json

class PesquisaQuadroHorarioRepository:
    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # MODIFICAÇÃO: Retorna Código + Nome para o Autocomplete funcionar com ambos
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas ORDER BY codigo;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar linhas: {e}")
            return []

    def salvar_pesquisa(self, linha, tipo, dados_completos, criado_por):
        query = """
            INSERT INTO quadro_horario.pesquisas (titulo, tipo_pesquisa, resultado_json, criado_por, created_at)
            VALUES (%s, %s, %s::jsonb, %s, NOW())
            RETURNING id;
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    json_str = json.dumps(dados_completos, ensure_ascii=False)
                    cur.execute(query, (linha, tipo, json_str, criado_por))
                    conn.commit()
                    row = cur.fetchone()
                    return True, f"Pesquisa salva com sucesso (ID: {row[0]})."
        except Exception as e:
            return False, f"Erro ao salvar: {e}"