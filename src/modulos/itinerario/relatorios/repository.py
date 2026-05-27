import psycopg2
from config.database import get_db_connection

class RelatoriosItinerarioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            # MODIFICAÇÃO: Wrapper Query - Criamos uma base sólida (AS base) para que os filtros encontrem todas as colunas virtuais
            query = """
                SELECT * FROM (
                    SELECT p.id, 
                           pb.numero_parecer_ano::text || '/' || pb.ano::text AS numero_completo, 
                           p.processo, o.nome AS origem, p.assunto, 
                           t.nome AS decisao, p.solicitante, p.endereco, p.evento, 
                           pb.created_at AS data_criacao, u.nome_completo AS responsavel,
                           pb.caminho_arquivo, 
                           (SELECT string_agg(cl.codigo, ', ') 
                            FROM itinerario.pareceres_linhas pl 
                            JOIN common.linhas cl ON pl.linha_id = cl.id 
                            WHERE pl.parecer_id = p.id) AS linhas, 
                           p.motivo_indeferimento, p.periodo
                    FROM itinerario.pareceres p
                    JOIN common.pareceres_base pb ON p.id = pb.id
                    LEFT JOIN common.tipos t ON pb.tipo_id = t.id
                    LEFT JOIN common.origens o ON p.origem_id = o.id
                    LEFT JOIN common.usuarios u ON pb.criado_por_id = u.id
                ) AS base
                WHERE 1=1
            """
        else: # ORDEM DE SERVIÇO
            query = """
                SELECT * FROM (
                    SELECT os.id, 
                           os.numero::text || '/' || os.ano::text AS numero_os, 
                           os.processo_adm AS processo, os.solicitante,
                           CASE 
                               WHEN os.nome_corrida IS NOT NULL AND os.nome_corrida <> '' THEN 'CORRIDA'
                               WHEN os.tipo_obra IS NOT NULL AND os.tipo_obra <> '' THEN 'OBRAS'
                               ELSE 'EVENTOS'
                           END AS tipo, 
                           o.nome AS origem, 
                           (SELECT string_agg(ce.nome, ', ') 
                            FROM itinerario.os_empresas oe 
                            JOIN common.empresas ce ON oe.empresa_id = ce.id 
                            WHERE oe.os_id = os.id) AS empresa, 
                           (SELECT string_agg(cl.codigo, ', ') 
                            FROM itinerario.os_linhas ol 
                            JOIN common.linhas cl ON ol.linha_id = cl.id 
                            WHERE ol.os_id = os.id) AS linhas, 
                           u.nome_completo AS responsavel, os.data_emissao AS data_criacao, os.endereco,
                           os.caminho_arquivo, 
                           COALESCE(NULLIF(os.nome_corrida, ''), NULLIF(os.tipo_obra, ''), NULLIF(os.evento, '')) AS evento, 
                           COALESCE(os.horario_inicio::text, '') || ' às ' || COALESCE(os.horario_fim::text, '') AS periodo
                    FROM itinerario.ordens_servico os
                    LEFT JOIN common.origens o ON os.origem_id = o.id
                    LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
                ) AS base
                WHERE 1=1
            """

        params = []
        # MODIFICAÇÃO: O Mapeamento agora enxerga 100% dos filtros dinâmicos na Wrapper Query
        mapeamento = {
            "PARECER": {
                "numero_completo": "numero_completo", "processo": "processo", 
                "origem": "origem", "assunto": "assunto", "decisao": "decisao", 
                "solicitante": "solicitante", "endereco": "endereco", 
                "evento": "evento", "responsavel": "responsavel", "linhas": "linhas"
            },
            "OS": {
                "numero_os": "numero_os", "processo": "processo", "solicitante": "solicitante",
                "tipo": "tipo", "origem": "origem", "responsavel": "responsavel", 
                "endereco": "endereco", "evento": "evento", "empresa": "empresa", "linhas": "linhas"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                coluna = doc_map[chave]
                
                # CORREÇÃO CRÍTICA: Se for "Decisão" ou "Tipo", usa "Exatamente Igual (=)" para que DEFERIDO não puxe INDEFERIDO
                if chave in ["decisao", "tipo"]:
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') = translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(valor)
                # Para o restante (Processo, Assunto, Solicitante...), continua usando LIKE para permitir pesquisa parcial
                else:
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(f"%{valor}%")

        if filtros.get("data_inicio"):
            query += f" AND data_criacao::date >= %s"
            params.append(filtros["data_inicio"])
        if filtros.get("data_fim"):
            query += f" AND data_criacao::date <= %s"
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
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                    else:
                        cur.execute("DELETE FROM itinerario.ordens_servico WHERE id = %s", (registro_id,))
                    conn.commit()
                    return True, "Registro excluído com sucesso."
        except Exception as e:
            return False, f"Erro ao excluir: {e}"

    def obter_empresas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nome FROM common.empresas WHERE is_ativo = TRUE ORDER BY nome")
                    return [row[0] for row in cur.fetchall()]
        except: return []

    def obter_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas WHERE is_ativo = TRUE ORDER BY codigo")
                    return [row[0] for row in cur.fetchall()]
        except: return []