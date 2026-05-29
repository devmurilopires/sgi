from config.database import get_db_connection

class LinhasRepository:
    def get_all_linhas(self):
        query = "SELECT id, codigo, nome, is_ativo FROM common.linhas ORDER BY codigo;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    cols = [desc[0] for desc in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar linhas: {e}")
            return []

    def adicionar_linha(self, codigo, nome):
        query = "INSERT INTO common.linhas (codigo, nome, is_ativo) VALUES (%s, %s, TRUE);"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (codigo, nome))
                    conn.commit()
            return True, "Linha adicionada com sucesso."
        except Exception as e:
            return False, f"Erro ao adicionar linha: {e}"

    def atualizar_linha(self, linha_id, codigo, nome):
        query = "UPDATE common.linhas SET codigo = %s, nome = %s WHERE id = %s;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (codigo, nome, linha_id))
                    conn.commit()
            return True, "Linha atualizada com sucesso."
        except Exception as e:
            return False, f"Erro ao atualizar linha: {e}"

    def toggle_ativo(self, linha_id, status_ativo):
        query = "UPDATE common.linhas SET is_ativo = %s WHERE id = %s;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (status_ativo, linha_id))
                    conn.commit()
            return True, "Status da linha atualizado com sucesso."
        except Exception as e:
            return False, f"Erro ao atualizar status: {e}"