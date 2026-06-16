import pandas as pd
from config.database import get_db_connection

class EnderecoRepository:
    def salvar_ou_atualizar(self, id_ponto, endereco, numero, bairro, complemento, status, criado_por):
        if isinstance(status, str):
            is_ativo = status.strip().upper() == "ATIVO"
        else:
            is_ativo = bool(status)

        query = """
            INSERT INTO ponto_parada.enderecos_cadastrados 
            (id, logradouro, numero, bairro, complemento, is_ativo, responsavel_vistoria_id, data_vistoria)
            VALUES (%s, %s, %s, %s, %s, %s, (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %s LIMIT 1), CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                logradouro = EXCLUDED.logradouro,
                numero = EXCLUDED.numero,
                bairro = EXCLUDED.bairro,
                complemento = EXCLUDED.complemento,
                is_ativo = EXCLUDED.is_ativo,
                responsavel_vistoria_id = EXCLUDED.responsavel_vistoria_id,
                data_vistoria = CURRENT_TIMESTAMP;
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (id_ponto, endereco, numero, bairro, complemento, is_ativo, f"%{criado_por}%"))
                conn.commit()
            return True, "Endereço salvo/atualizado com sucesso!"
        except Exception as e:
            return False, f"Erro no banco de dados: {e}"

    def excluir(self, id_ponto):
        query = "DELETE FROM ponto_parada.enderecos_cadastrados WHERE id = %s"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (id_ponto,))
                conn.commit()
            return True, "Endereço excluído com sucesso!"
        except Exception as e:
            return False, f"Erro ao excluir o endereço do banco de dados: {e}"

    # ==========================================
    # NOVAS FUNÇÕES: PAGINAÇÃO E BUSCA OTIMIZADA
    # ==========================================
    def contar_enderecos(self, termo=""):
        query = "SELECT COUNT(*) FROM ponto_parada.enderecos_cadastrados"
        params = []
        if termo:
            query += " WHERE id::text ILIKE %s OR logradouro ILIKE %s OR bairro ILIKE %s"
            termo_like = f"%{termo}%"
            params.extend([termo_like, termo_like, termo_like])
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"[LOG DB] Erro ao contar endereços: {e}")
            return 0

    def listar_enderecos_paginados(self, termo="", limit=50, offset=0):
        query = """
            SELECT 
                e.id AS id_ponto, 
                e.logradouro AS endereco, 
                e.numero, 
                e.bairro, 
                e.complemento, 
                CASE WHEN e.is_ativo THEN 'ATIVO' ELSE 'INATIVO' END AS status
            FROM ponto_parada.enderecos_cadastrados e
        """
        params = []
        if termo:
            query += " WHERE e.id::text ILIKE %s OR e.logradouro ILIKE %s OR e.bairro ILIKE %s"
            termo_like = f"%{termo}%"
            params.extend([termo_like, termo_like, termo_like])
            
        query += " ORDER BY e.id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    cols = [desc[0] for desc in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao paginar endereços: {e}")
            return []

    def listar_todos(self):
        query = """
            SELECT 
                e.id AS id_ponto, e.logradouro AS endereco, e.numero, e.bairro, e.complemento, 
                CASE WHEN e.is_ativo THEN 'ATIVO' ELSE 'INATIVO' END AS status, 
                u.nome_completo AS criado_por, e.data_vistoria AS updated_at
            FROM ponto_parada.enderecos_cadastrados e
            LEFT JOIN common.usuarios u ON e.responsavel_vistoria_id = u.id
            ORDER BY e.id DESC
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            return pd.DataFrame()

    def obter_valores_unicos(self, campo):
        coluna = "bairro" if campo == "Bairro" else "logradouro"
        query = f"SELECT DISTINCT {coluna} FROM ponto_parada.enderecos_cadastrados WHERE {coluna} IS NOT NULL AND {coluna} != '' ORDER BY {coluna}"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return [row[0] for row in cur.fetchall()]
        except: return []

    def padronizar_valores(self, campo, valores_antigos, novo_valor):
        coluna = "bairro" if campo == "Bairro" else "logradouro"
        query = f"UPDATE ponto_parada.enderecos_cadastrados SET {coluna} = %s WHERE {coluna} = ANY(%s)"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (novo_valor, valores_antigos))
                    linhas_afetadas = cur.rowcount
                conn.commit()
            nome_amigavel = "bairros" if campo == "Bairro" else "endereços"
            return True, f"Sucesso! {linhas_afetadas} ponto(s) atualizado(s) para o {nome_amigavel[:-1]} '{novo_valor}'."
        except Exception as e:
            return False, f"Erro ao padronizar no banco: {e}"
        
    # ==========================================
    # PAGINAÇÃO PARA A MODAL DE PADRONIZAÇÃO
    # ==========================================
    def contar_valores_unicos(self, campo, termo=""):
        coluna = "bairro" if campo == "Bairro" else "logradouro"
        query = f"SELECT COUNT(DISTINCT {coluna}) FROM ponto_parada.enderecos_cadastrados WHERE {coluna} IS NOT NULL AND {coluna} != ''"
        params = []
        if termo:
            query += f" AND {coluna} ILIKE %s"
            params.append(f"%{termo}%")
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"[LOG DB] Erro ao contar valores únicos: {e}")
            return 0

    def listar_valores_unicos_paginados(self, campo, termo="", limit=50, offset=0):
        coluna = "bairro" if campo == "Bairro" else "logradouro"
        query = f"SELECT DISTINCT {coluna} FROM ponto_parada.enderecos_cadastrados WHERE {coluna} IS NOT NULL AND {coluna} != ''"
        params = []
        if termo:
            query += f" AND {coluna} ILIKE %s"
            params.append(f"%{termo}%")
            
        query += f" ORDER BY {coluna} LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao listar valores únicos: {e}")
            return []