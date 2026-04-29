import psycopg2
from config.database import get_db_connection

class ParametrosRepository:
    def inserir_parametro(self, categoria, valor):
        """Insere um novo parâmetro no sistema."""
        query = """
            INSERT INTO common.parametros_sistema (categoria, valor)
            VALUES (%s, %s) RETURNING id;
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (categoria, valor))
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Erro ao inserir parâmetro: {e}")
            raise e

    def inativar_parametro(self, parametro_id):
        """Realiza o soft delete de um parâmetro alterando is_ativo para false."""
        query = "UPDATE common.parametros_sistema SET is_ativo = FALSE WHERE id = %s;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (parametro_id,))
        except Exception as e:
            print(f"Erro ao inativar parâmetro {parametro_id}: {e}")
            raise e

    def get_parametros_by_categoria(self, categoria):
        """Busca todos os parâmetros ativos de uma determinada categoria."""
        query = """
            SELECT id, categoria, valor, is_ativo 
            FROM common.parametros_sistema 
            WHERE categoria = %s AND is_ativo = TRUE;
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (categoria,))
                    # Retorna como uma lista de dicionários para facilitar o uso no service/view
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar parâmetros da categoria {categoria}: {e}")
            return []
