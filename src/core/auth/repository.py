import psycopg2
from config.database import get_db_connection

class AuthRepository:
    def buscar_usuario(self, login):
        query = """
            SELECT password_hash, tipo_perfil, nome_completo, username, is_admin, is_ativo
            FROM common.usuarios 
            WHERE email = %s OR username = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (login, login))
                    return True, cur.fetchone()
        except Exception as e:
            print(f"[LOG DB] Erro no Auth: {e}")
            return False, None

    def verificar_existencia(self, username, email):
        query = "SELECT id FROM common.usuarios WHERE username = %s OR email = %s"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (username, email))
                    return True, cur.fetchone()
        except Exception as e:
            return False, None

    def buscar_email(self, email):
        query = "SELECT id FROM common.usuarios WHERE email = %s"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (email,))
                    return True, cur.fetchone()
        except Exception as e:
            return False, None

    def criar_usuario(self, nome, username, email, senha_hash, perfil):
        query = """
            INSERT INTO common.usuarios (nome_completo, username, email, password_hash, tipo_perfil, is_admin) 
            VALUES (%s, %s, %s, %s, %s, False)
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (nome, username, email, senha_hash, perfil))
                    conn.commit()
                    return True, None
        except Exception as e:
            return False, str(e)

    def atualizar_senha(self, email, senha_hash):
        query = "UPDATE common.usuarios SET password_hash = %s WHERE email = %s"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (senha_hash, email))
                    conn.commit()
                    return True, None
        except Exception as e:
            return False, str(e)