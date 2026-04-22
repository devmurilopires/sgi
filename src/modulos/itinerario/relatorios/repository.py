import psycopg2
from config.database import get_db_connection

class RelatoriosItinerarioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            query = """
                SELECT p.id, pb.numero_parecer_ano, p.processo, p.origem, p.assunto, 
                       p.tipo_parecer as decisao, p.solicitante, p.endereco, p.evento, 
                       pb.created_at as data_criacao, u.nome_completo as responsavel,
                       p.caminho_arquivo, p.linhas_afetadas, p.motivo_indeferimento, p.periodo
                FROM itinerario.pareceres p
                LEFT JOIN common.pareceres_base pb ON p.id = pb.id
                LEFT JOIN common.usuarios u ON pb.criado_por_id = u.id
                WHERE 1=1
            """
        else: # ORDEM DE SERVIÇO (Agora com Solicitante)
            query = """
                SELECT o.id, o.numero as numero_os, o.processo_adm as processo, o.solicitante,
                       o.tipo_evento as tipo, o.origem, o.empresas_text as empresa, 
                       o.linhas_text as linhas, o.responsavel, o.data_criacao, o.endereco,
                       o.caminho_arquivo, o.evento, 
                       COALESCE(o.horario_inicio, '') || ' às ' || COALESCE(o.horario_fim, '') as periodo
                FROM itinerario.ordens_servico o
                WHERE 1=1
            """

        params = []
        mapeamento = {
            "PARECER": {
                "numero": "pb.numero_parecer_ano", "processo": "p.processo", "origem": "p.origem",
                "assunto": "p.assunto", "decisao": "p.tipo_parecer", "solicitante": "p.solicitante",
                "endereco": "p.endereco", "evento": "p.evento", "responsavel": "u.nome_completo"
            },
            "OS": {
                "numero": "o.numero", "processo": "o.processo_adm", "solicitante": "o.solicitante", "tipo": "o.tipo_evento",
                "origem": "o.origem", "empresa": "o.empresas_text", "linhas": "o.linhas_text",
                "responsavel": "o.responsavel", "endereco": "o.endereco"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                query += f" AND COALESCE({doc_map[chave]}::text, '') ILIKE %s"
                params.append(f"%{valor}%")

        col_data = "pb.created_at" if tipo_doc == "PARECER" else "o.data_criacao"
        if filtros.get("data_inicio"):
            query += f" AND ({col_data} IS NULL OR {col_data}::date >= %s)"
            params.append(filtros["data_inicio"])
        if filtros.get("data_fim"):
            query += f" AND ({col_data} IS NULL OR {col_data}::date <= %s)"
            params.append(filtros["data_fim"])

        query += " ORDER BY id DESC"
        return query, params

    def buscar_dados_paginados(self, tipo_doc, filtros, limit=20, offset=0):
        query, params = self._construir_query_filtros(tipo_doc, filtros)
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    colunas = [desc[0] for desc in cur.description]
                    return [dict(zip(colunas, row)) for row in cur.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar: {e}"); return []

    def contar_total(self, tipo_doc, filtros):
        query, params = self._construir_query_filtros(tipo_doc, filtros)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM ({query}) AS total", params)
                    return cur.fetchone()[0]
        except: return 0

    def excluir_registro(self, tipo_doc, registro_id):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if tipo_doc == "PARECER":
                        cur.execute("DELETE FROM itinerario.pareceres WHERE id = %s", (registro_id,))
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                    else:
                        cur.execute("DELETE FROM itinerario.ordens_servico WHERE id = %s", (registro_id,))
                    conn.commit()
                    return True, "Registro excluído com sucesso."
        except Exception as e:
            return False, f"Erro ao excluir: {e}"

    # --- NOVAS FUNÇÕES PARA POPULAR OS FILTROS ---
    def obter_empresas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nome FROM common.empresas ORDER BY nome")
                    return [row[0] for row in cur.fetchall()]
        except: return []

    def obter_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas ORDER BY codigo")
                    return [row[0] for row in cur.fetchall()]
        except: return []