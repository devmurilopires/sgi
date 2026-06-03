from config.database import get_db_connection

class ParametrosRepository:
    def inserir_parametro(self, routing, valor):
        """Insere um novo valor ou reativa (ressuscita) um valor inativado."""
        tabela = routing['tabela']
        col_val = routing['col_val']
        col_ctx = routing['col_ctx']
        val_ctx = routing['val_ctx']
            
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # 1. Verifica se a palavra exata já existe (seja ativa ou inativa)
                    if col_ctx:
                        check_query = f"SELECT id, is_ativo FROM {tabela} WHERE {col_ctx} = %s AND UPPER({col_val}) = UPPER(%s);"
                        cur.execute(check_query, (val_ctx, valor))
                    else:
                        check_query = f"SELECT id, is_ativo FROM {tabela} WHERE UPPER({col_val}) = UPPER(%s);"
                        cur.execute(check_query, (valor,))

                    registro = cur.fetchone()

                    # Se encontrou o registro
                    if registro:
                        registro_id, is_ativo = registro
                        if is_ativo:
                            return False, f"O valor '{valor}' já existe e já está ativo na lista."
                        else:
                            # 2. O registro estava excluído (Soft Delete). Vamos ressuscitá-lo!
                            update_query = f"UPDATE {tabela} SET is_ativo = TRUE, {col_val} = %s WHERE id = %s;"
                            cur.execute(update_query, (valor, registro_id))
                            conn.commit()
                            return True, f"O item '{valor}' havia sido excluído anteriormente e foi restaurado com sucesso."

                    # 3. Se não encontrou nada no banco, faz a inserção (INSERT) normal
                    if col_ctx:
                        insert_query = f"INSERT INTO {tabela} ({col_ctx}, {col_val}) VALUES (%s, %s) RETURNING id;"
                        cur.execute(insert_query, (val_ctx, valor))
                    else:
                        insert_query = f"INSERT INTO {tabela} ({col_val}) VALUES (%s) RETURNING id;"
                        cur.execute(insert_query, (valor,))
                        
                    conn.commit()
                    return True, "Parâmetro adicionado com sucesso."
                    
        except Exception as e:
            return False, f"Erro inesperado no banco de dados: {e}"

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
        
    
    def listar_parametros(self, routing):
            """Busca os dados ordenados primeiro pela Ordem e depois alfabeticamente."""
            tabela = routing['tabela']
            col_val = routing['col_val']
            
            if routing['col_ctx']:
                query = f"SELECT id, {col_val} AS valor, is_ativo FROM {tabela} WHERE {routing['col_ctx']} = %s AND is_ativo = TRUE ORDER BY ordem ASC, {col_val} ASC;"
                params = (routing['val_ctx'],)
            else:
                query = f"SELECT id, {col_val} AS valor, is_ativo FROM {tabela} WHERE is_ativo = TRUE ORDER BY ordem ASC, {col_val} ASC;"
                params = ()
                
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, params)
                        columns = [desc[0] for desc in cur.description]
                        return [dict(zip(columns, row)) for row in cur.fetchall()]
            except Exception as e:
                print(f"Erro ao listar: {e}")
                return []

    def atualizar_ordem_lote(self, routing, lista_ids):
        """Atualiza a coluna 'ordem' baseada na posição do ID na lista."""
        tabela = routing['tabela']
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    for index, item_id in enumerate(lista_ids):
                        # O index será 0, 1, 2, 3... gravando a ordem exata no banco
                        cur.execute(f"UPDATE {tabela} SET ordem = %s WHERE id = %s;", (index, item_id))
                    conn.commit()
            return True, "Ordenação guardada com sucesso."
        except Exception as e:
            return False, f"Erro ao reordenar: {e}"