from config.database import get_db_connection

class ParametrosRepository:
    def inserir_parametro(self, routing, valor):
        """Insere um novo valor dinamicamente na tabela correta."""
        tabela = routing['tabela']
        col_val = routing['col_val']
        
        if routing['col_ctx']:
            query = f"INSERT INTO {tabela} ({routing['col_ctx']}, {col_val}) VALUES (%s, %s) RETURNING id;"
            params = (routing['val_ctx'], valor)
        else:
            query = f"INSERT INTO {tabela} ({col_val}) VALUES (%s) RETURNING id;"
            params = (valor,)
            
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    conn.commit() # CORREÇÃO CRÍTICA
                    return True, "Parâmetro adicionado com sucesso."
        except Exception as e:
            return False, f"Erro de integridade (já existe ou erro no banco): {e}"

    def inativar_parametro(self, routing, parametro_id):
        """Inativa (soft delete) dinamicamente na tabela correta."""
        tabela = routing['tabela']
        query = f"UPDATE {tabela} SET is_ativo = FALSE WHERE id = %s;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (parametro_id,))
                    conn.commit() # CORREÇÃO CRÍTICA
            return True, "Parâmetro removido (inativado) com sucesso."
        except Exception as e:
            return False, f"Erro ao inativar parâmetro: {e}"

    def atualizar_valor(self, routing, parametro_id, novo_valor):
        """Atualiza o texto dinamicamente na tabela correta."""
        tabela = routing['tabela']
        col_val = routing['col_val']
        query = f"UPDATE {tabela} SET {col_val} = %s WHERE id = %s;"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (novo_valor, parametro_id))
                    conn.commit() # CORREÇÃO CRÍTICA
            return True, "Parâmetro atualizado com sucesso."
        except Exception as e:
            return False, f"Erro ao atualizar valor: {e}"

    def listar_parametros(self, routing):
        """Busca os dados e padroniza a saída para a View (id, valor, is_ativo)."""
        tabela = routing['tabela']
        col_val = routing['col_val']
        
        if routing['col_ctx']:
            query = f"SELECT id, {col_val} AS valor, is_ativo FROM {tabela} WHERE {routing['col_ctx']} = %s AND is_ativo = TRUE ORDER BY {col_val};"
            params = (routing['val_ctx'],)
        else:
            query = f"SELECT id, {col_val} AS valor, is_ativo FROM {tabela} WHERE is_ativo = TRUE ORDER BY {col_val};"
            params = ()
            
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao listar parâmetros: {e}")
            return []