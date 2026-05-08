import psycopg2
from config.database import get_db_connection

class RelatorioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            # Usando as colunas reais: p.solicitante e p.endereco_vistoria
            query = """
                SELECT p.id, pb.numero_parecer_ano, p.processo, p.origem_demanda as origem, 
                       p.assunto, pb.tipo_parecer as decisao, p.solicitante, p.endereco_vistoria as endereco, 
                       pb.created_at as data_criacao, u.nome_completo as responsavel,
                       p.caminho_arquivo_docx as caminho_arquivo, p.motivo_indeferimento
                FROM ponto_parada.pareceres p
                LEFT JOIN common.pareceres_base pb ON p.id = pb.id
                LEFT JOIN common.usuarios u ON pb.criado_por_id = u.id
                WHERE 1=1
            """
        else: # ORDEM DE SERVIÇO (ponto_parada)
            # CORREÇÃO: Removido o bloqueio " '' as caminho_arquivo ".
            # Agora o sistema puxa a coluna 'o.caminho_arquivo' real do banco de dados!
            query = """
                SELECT o.id, o.numero as numero_os, o.origem_demanda as origem, o.acao_realizada as acao,
                       o.tipo_item as item, o.ponto_principal_id, o.pontos_adicionais, 
                       o.logradouro_completo as endereco, o.bairro, o.status_conclusao as status,
                       o.data_criacao, o.responsavel, o.caminho_arquivo
                FROM ponto_parada.ordens_servico o
                WHERE 1=1
            """

        params = []
        mapeamento = {
            "PARECER": {
                "processo": "p.processo", "origem": "p.origem_demanda", "assunto": "p.assunto",
                "decisao": "pb.tipo_parecer", "solicitante": "p.solicitante", "responsavel": "u.nome_completo"
            },
            "OS": {
                "id_ponto": "MULTI_ID", # Busca tanto no principal quanto nos adicionais
                "origem": "o.origem_demanda", "acao": "o.acao_realizada", "item": "o.tipo_item",
                "status": "o.status_conclusao", "bairro": "o.bairro", "responsavel": "o.responsavel"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                if chave == "id_ponto" and tipo_doc == "OS":
                    query += f" AND (o.ponto_principal_id ILIKE %s OR o.pontos_adicionais ILIKE %s)"
                    params.extend([f"%{valor}%", f"%{valor}%"])
                else:
                    query += f" AND COALESCE({doc_map[chave]}::text, '') ILIKE %s"
                    params.append(f"%{valor}%")

        # Filtro de Data
        col_data = "pb.created_at" if tipo_doc == "PARECER" else "o.data_criacao"
        if filtros.get("data_inicio"):
            query += f" AND ({col_data} IS NULL OR {col_data}::date >= %s)"
            params.append(filtros["data_inicio"])
        if filtros.get("data_fim"):
            query += f" AND ({col_data} IS NULL OR {col_data}::date <= %s)"
            params.append(filtros["data_fim"])

        query += " ORDER BY id DESC"
        return query, params

    def buscar_dados_paginados(self, tipo_doc, filtros, limit=50, offset=0):
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
            print(f"Erro ao buscar dados: {e}"); return []

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
                        cur.execute("DELETE FROM ponto_parada.pareceres WHERE id = %s", (registro_id,))
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                    else:
                        cur.execute("DELETE FROM ponto_parada.ordens_servico WHERE id = %s", (registro_id,))
                    conn.commit()
                    return True, "Registro excluído com sucesso."
        except Exception as e:
            return False, f"Erro ao excluir: {e}"

    def obter_bairros(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT DISTINCT bairro FROM ponto_parada.ordens_servico WHERE bairro IS NOT NULL AND bairro != '' ORDER BY bairro")
                    return [row[0] for row in cur.fetchall()]
        except: return []