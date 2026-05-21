import psycopg2
from config.database import get_db_connection

class RelatoriosItinerarioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            # MODIFICAÇÃO: JOINs de FK (Tipos, Origens) e Subquery N:M para as Linhas
            query = """
                SELECT p.id, 
                       pb.numero_parecer_ano::text || '/' || pb.ano::text AS numero_completo, 
                       p.processo, o.nome AS origem, p.assunto, 
                       t.nome AS decisao, p.solicitante, p.endereco, p.evento, 
                       pb.created_at AS data_criacao, u.nome_completo AS responsavel,
                       pb.caminho_arquivo, 
                       (SELECT string_agg(cl.codigo, ', ') 
                        FROM itinerario.pareceres_linhas pl 
                        JOIN common.linhas cl ON pl.linha_id = cl.id 
                        WHERE pl.parecer_id = p.id) AS linhas_afetadas, 
                       p.motivo_indeferimento, p.periodo
                FROM itinerario.pareceres p
                JOIN common.pareceres_base pb ON p.id = pb.id
                LEFT JOIN common.tipos t ON pb.tipo_id = t.id
                LEFT JOIN common.origens o ON p.origem_id = o.id
                LEFT JOIN common.usuarios u ON pb.criado_por_id = u.id
                WHERE 1=1
            """
        else: # ORDEM DE SERVIÇO
            # MODIFICAÇÃO: Subqueries N:M para Empresas e Linhas. Ajuste data_emissao.
            # NOTA: Solicitante não existe na OS no DDL, fixado como '' para não quebrar a View.
            query = """
                SELECT os.id, 
                       os.numero::text || '/' || os.ano::text AS numero_os, 
                       os.processo_adm AS processo, '' AS solicitante,
                       t.nome AS tipo, o.nome AS origem, 
                       (SELECT string_agg(ce.nome, ', ') 
                        FROM itinerario.os_empresas oe 
                        JOIN common.empresas ce ON oe.empresa_id = ce.id 
                        WHERE oe.os_id = os.id) AS empresa, 
                       (SELECT string_agg(cl.codigo, ', ') 
                        FROM itinerario.os_linhas ol 
                        JOIN common.linhas cl ON ol.linha_id = cl.id 
                        WHERE ol.os_id = os.id) AS linhas, 
                       u.nome_completo AS responsavel, os.data_emissao AS data_criacao, os.endereco,
                       os.caminho_arquivo, os.evento, 
                       COALESCE(os.horario_inicio::text, '') || ' às ' || COALESCE(os.horario_fim::text, '') AS periodo
                FROM itinerario.ordens_servico os
                LEFT JOIN common.tipos t ON os.tipo_evento_id = t.id
                LEFT JOIN common.origens o ON os.origem_id = o.id
                LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
                WHERE 1=1
            """

        params = []
        mapeamento = {
            "PARECER": {
                "processo": "p.processo", "origem": "o.nome",
                "assunto": "p.assunto", "decisao": "t.nome", "solicitante": "p.solicitante",
                "endereco": "p.endereco", "evento": "p.evento", "responsavel": "u.nome_completo"
            },
            "OS": {
                "processo": "os.processo_adm", "tipo": "t.nome",
                "origem": "o.nome", "responsavel": "u.nome_completo", "endereco": "os.endereco"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                # SOLUÇÃO NATIVA: Busca inteligente ignorando acentos!
                query += f" AND translate(lower(COALESCE({doc_map[chave]}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                params.append(f"%{valor}%")

        # Filtros Especiais de N:M que exigem Subqueries no WHERE (Também ignorando acentos)
        if filtros.get("linhas"):
            term = f"%{filtros['linhas']}%"
            if tipo_doc == "PARECER":
                query += " AND EXISTS (SELECT 1 FROM itinerario.pareceres_linhas pl JOIN common.linhas cl ON pl.linha_id = cl.id WHERE pl.parecer_id = p.id AND translate(lower(cl.codigo), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc'))"
                params.append(term)
            else:
                query += " AND EXISTS (SELECT 1 FROM itinerario.os_linhas ol JOIN common.linhas cl ON ol.linha_id = cl.id WHERE ol.os_id = os.id AND translate(lower(cl.codigo), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc'))"
                params.append(term)
                
        if tipo_doc == "OS" and filtros.get("empresa"):
            query += " AND EXISTS (SELECT 1 FROM itinerario.os_empresas oe JOIN common.empresas ce ON oe.empresa_id = ce.id WHERE oe.os_id = os.id AND translate(lower(ce.nome), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc'))"
            params.append(f"%{filtros['empresa']}%")

        col_data = "pb.created_at" if tipo_doc == "PARECER" else "os.data_emissao"
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
                        # Deletando a base, o banco apaga a filha via CASCADE
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
                    # Garantindo apenas ativos
                    cur.execute("SELECT nome FROM common.empresas WHERE is_ativo = TRUE ORDER BY nome")
                    return [row[0] for row in cur.fetchall()]
        except: return []

    def obter_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Garantindo apenas ativos
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas WHERE is_ativo = TRUE ORDER BY codigo")
                    return [row[0] for row in cur.fetchall()]
        except: return []