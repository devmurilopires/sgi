from config.database import get_db_connection

class UsuariosRepository:
    def get_all_usuarios(self):
        """Busca todos os usuários cadastrados."""
        query = """
            SELECT id, nome_completo, username, email, tipo_perfil, is_admin, is_ativo
            FROM common.usuarios
            ORDER BY nome_completo;
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar usuários: {e}")
            return []

    def atualizar_perfil(self, usuario_id, novo_perfil):
        """Atualiza o perfil de acesso do usuário."""
        query = "UPDATE common.usuarios SET tipo_perfil = %s WHERE id = %s;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (novo_perfil, usuario_id))
                    conn.commit() # CORREÇÃO CRÍTICA: Sem isso o banco não salva a alteração!
            return True, "Perfil atualizado com sucesso."
        except Exception as e:
            return False, f"Erro ao atualizar perfil: {e}"

    def toggle_admin(self, usuario_id, status_admin):
        """Promove ou remove status de administrador de um usuário."""
        query = "UPDATE common.usuarios SET is_admin = %s WHERE id = %s;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (status_admin, usuario_id))
                    conn.commit() # CORREÇÃO CRÍTICA
            return True, "Status de administrador atualizado com sucesso."
        except Exception as e:
            return False, f"Erro ao alterar status admin: {e}"

    def toggle_ativo(self, usuario_id, status_ativo):
        """Ativa ou inativa um usuário (Soft Delete)."""
        query = "UPDATE common.usuarios SET is_ativo = %s WHERE id = %s;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (status_ativo, usuario_id))
                    conn.commit() # CORREÇÃO CRÍTICA
            return True, "Status de acesso atualizado com sucesso."
        except Exception as e:
            return False, f"Erro ao alterar status ativo: {e}"