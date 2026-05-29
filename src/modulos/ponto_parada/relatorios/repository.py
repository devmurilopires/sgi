import psycopg2
from config.database import get_db_connection

class RelatorioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            # MODIFICAÇÃO: Wrapper Query para destravar busca por Nº Parecer
            query = """
                SELECT * FROM (
                    SELECT p.id, pb.numero_parecer_ano::text || '/' || pb.ano::text AS numero_completo, 
                           p.processo, o.nome AS origem, p.assunto, t.nome AS decisao, 
                           p.solicitante, p.endereco_vistoria AS endereco, 
                           pb.created_at AS data_criacao, u.nome_completo AS responsavel,
                           pb.caminho_arquivo, p.motivo_indeferimento
                    FROM ponto_parada.pareceres p
                    JOIN common.pareceres_base pb ON p.id = pb.id
                    LEFT JOIN common.tipos t ON pb.tipo_id = t.id
                    LEFT JOIN common.origens o ON p.origem_id = o.id
                    LEFT JOIN common.usuarios u ON pb.criado_por_id = u.id
                ) AS base
                WHERE 1=1
            """
        else: # ORDEM DE SERVIÇO
            # MODIFICAÇÃO: Wrapper Query para destravar busca por Nº OS
            query = """
                SELECT * FROM (
                    SELECT os.id, os.numero AS numero_os, o.nome AS origem, 
                           ta.nome AS acao, ti.nome AS item, os.ponto_principal_id, 
                           (SELECT string_agg(pa.ponto_id, ', ') 
                            FROM ponto_parada.os_pontos_adicionais pa 
                            WHERE pa.os_id = os.id) AS pontos_adicionais, 
                           (e.logradouro || COALESCE(', ' || e.numero, '') || COALESCE(' - ' || e.complemento, '')) AS endereco, 
                           e.bairro, os.status_conclusao AS status,
                           os.data_criacao, u.nome_completo AS responsavel, os.caminho_arquivo
                    FROM ponto_parada.ordens_servico os
                    LEFT JOIN ponto_parada.enderecos_cadastrados e ON os.ponto_principal_id = e.id
                    LEFT JOIN common.origens o ON os.origem_id = o.id
                    LEFT JOIN common.tipos ta ON os.tipo_acao_id = ta.id
                    LEFT JOIN common.tipos ti ON os.tipo_item_id = ti.id
                    LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
                ) AS base
                WHERE 1=1
            """

        params = []
        mapeamento = {
            "PARECER": {
                "numero_completo": "numero_completo", "processo": "processo", "origem": "origem", 
                "assunto": "assunto", "decisao": "decisao", "solicitante": "solicitante", "responsavel": "responsavel"
            },
            "OS": {
                "numero_os": "numero_os", "origem": "origem", "acao": "acao", "item": "item",
                "status": "status", "bairro": "bairro", "responsavel": "responsavel",
                "id_ponto": "ponto_principal_id"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                coluna = doc_map[chave]
                
                # BLINDAGEM: Decisão usa = para que "Deferido" não puxe "Indeferido"
                if chave == "decisao":
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') = translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(valor)
                # BLINDAGEM: Busca por ID do Ponto de Parada (Principal ou Adicionais)
                elif chave == "id_ponto" and tipo_doc == "OS":
                    query += f""" AND (
                        translate(lower(COALESCE(ponto_principal_id::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') OR 
                        translate(lower(COALESCE(pontos_adicionais::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')
                    )"""
                    params.extend([f"%{valor}%", f"%{valor}%"])
                # BLINDAGEM: Qualquer outro campo livre (LIKE Ignorando maiúsculas e acentos)
                else:
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(f"%{valor}%")

        # Filtro de Data
        col_data = "data_criacao"
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
            print(f"[LOG DB] Erro ao buscar dados: {e}")
            return []

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
                    cur.execute("SELECT DISTINCT bairro FROM ponto_parada.enderecos_cadastrados WHERE bairro IS NOT NULL AND bairro != '' ORDER BY bairro")
                    return [row[0] for row in cur.fetchall()]
        except: return []

    def obter_todos_itens(self):
        query = "SELECT nome FROM common.tipos WHERE contexto IN ('ITEM_URBMIDIA', 'ITEM_MCMENSAGEM') ORDER BY nome"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return [row[0] for row in cur.fetchall()]
        except: return []