import psycopg2
from config.database import get_db_connection

class RelatorioProjetosMobilidadeRepository:
    def _construir_query_filtros(self, filtros):
        # 1. MODIFICAÇÃO: Junção atualizada com 'common.tipos' e concatenação de número/ano.
        # 2. MODIFICAÇÃO: 'motivo_indeferimento' removido do SELECT.
        query = """
            SELECT p.id, 
                   pb.numero_parecer_ano::text || '/' || pb.ano::text AS numero_completo, 
                   p.processo, 
                   p.assunto, 
                   t.nome AS decisao, 
                   p.solicitante, 
                   pb.created_at AS data_criacao, 
                   u.nome_completo AS responsavel
            FROM projetos_mobilidade.pareceres p
            JOIN common.pareceres_base pb ON p.id = pb.id
            LEFT JOIN common.tipos t ON pb.tipo_id = t.id
            LEFT JOIN common.usuarios u ON pb.criado_por_id = u.id
            WHERE 1=1
        """
        params = []
        
        # 3. MODIFICAÇÃO: A chave 'decisao' agora aponta para 't.nome' (da tabela de tipos).
        mapeamento = {
            "processo": "p.processo", 
            "assunto": "p.assunto",
            "decisao": "t.nome", 
            "solicitante": "p.solicitante", 
            "responsavel": "u.nome_completo"
        }

        for chave, valor in filtros.items():
            if valor and chave in mapeamento:
                query += f" AND COALESCE({mapeamento[chave]}::text, '') ILIKE %s"
                params.append(f"%{valor}%")

        # Filtro de Data
        col_data = "pb.created_at"
        if filtros.get("data_inicio"):
            query += f" AND ({col_data} IS NULL OR {col_data}::date >= %s)"
            params.append(filtros["data_inicio"])
        if filtros.get("data_fim"):
            query += f" AND ({col_data} IS NULL OR {col_data}::date <= %s)"
            params.append(filtros["data_fim"])

        # 4. DETALHE: O 'ORDER BY' agora especifica a origem do 'id' para evitar ambiguidade (p.id)
        query += " ORDER BY p.id DESC"
        return query, params

    def buscar_dados_paginados(self, filtros, limit=50, offset=0):
        query, params = self._construir_query_filtros(filtros)
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    colunas = [desc[0] for desc in cur.description]
                    return [dict(zip(colunas, row)) for row in cur.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar dados paginados: {e}")
            return []

    def contar_total(self, filtros):
        query, params = self._construir_query_filtros(filtros)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM ({query}) AS total", params)
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"[LOG DB] Erro ao contar total: {e}")
            return 0

    def excluir_registro(self, registro_id):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Devido ao ON DELETE CASCADE na tabela filha, 
                    # basta excluir na tabela base e o banco de dados limpa a filha automaticamente!
                    cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                    conn.commit()
                    return True, "Parecer excluído com sucesso do banco de dados."
        except Exception as e:
            return False, f"Erro ao excluir: {e}"