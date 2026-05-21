import psycopg2
import json
from config.database import get_db_connection

class RelatorioQuadroHorarioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            # MODIFICAÇÃO: Ajuste de JOINs com common.tipos, common.usuarios e concatenação de Linhas (N:M)
            query = """
                SELECT p.id, 
                       b.numero_parecer_ano::text || '/' || b.ano::text AS numero_completo, 
                       p.processo, p.assunto, 
                       t.nome AS decisao, p.solicitante, p.evento, 
                       (SELECT string_agg(cl.codigo, ', ') 
                        FROM quadro_horario.pareceres_linhas pl 
                        JOIN common.linhas cl ON pl.linha_id = cl.id 
                        WHERE pl.parecer_id = p.id) AS linhas, 
                       p.data_evento, 
                       u.nome_completo AS responsavel, b.created_at AS data_criacao, 
                       b.caminho_arquivo, p.motivo_indeferimento
                FROM quadro_horario.pareceres p
                JOIN common.pareceres_base b ON p.id = b.id
                LEFT JOIN common.tipos t ON b.tipo_id = t.id
                LEFT JOIN common.usuarios u ON b.criado_por_id = u.id 
                WHERE 1=1
            """
        else: # PESQUISA
            # MODIFICAÇÃO: Ajuste de JOINs e renomeação de colunas (resultado_payload, data_pesquisa)
            query = """
                SELECT p.id, 
                       l.codigo || ' - ' || l.nome AS titulo, 
                       tp.nome AS tipo, 
                       p.data_pesquisa_1 AS data_inicio, 
                       COALESCE(p.data_pesquisa_3, p.data_pesquisa_2, p.data_pesquisa_1) AS data_fim, 
                       u.nome_completo AS responsavel, p.created_at AS data_criacao, 
                       NULL AS caminho_arquivo,
                       p.resultado_payload AS payload
                FROM quadro_horario.pesquisas p
                LEFT JOIN common.linhas l ON p.linha_id = l.id
                LEFT JOIN common.tipos tp ON p.tipo_pesquisa_id = tp.id
                LEFT JOIN common.usuarios u ON p.criado_por_id = u.id
                WHERE 1=1
            """

        params = []
        mapeamento = {
            "PARECER": {
                "processo": "p.processo", "assunto": "p.assunto", "decisao": "t.nome",
                "solicitante": "p.solicitante", "responsavel": "u.nome_completo"
            },
            "PESQUISA": {
                "titulo": "(l.codigo || ' - ' || l.nome)", "tipo": "tp.nome", "responsavel": "u.nome_completo"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                # SOLUÇÃO NATIVA: Ignorando acentos e maiúsculas/minúsculas
                query += f" AND translate(lower(COALESCE({doc_map[chave]}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                params.append(f"%{valor}%")

        # Tratamento especial para o filtro de Linhas (Relacionamento N:M)
        if tipo_doc == "PARECER" and filtros.get("linhas"):
            query += """ AND EXISTS (
                SELECT 1 FROM quadro_horario.pareceres_linhas pl 
                JOIN common.linhas cl ON pl.linha_id = cl.id 
                WHERE pl.parecer_id = p.id AND translate(lower(cl.codigo), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')
            )"""
            params.append(f"%{filtros['linhas']}%")

        if tipo_doc == "PESQUISA" and filtros.get("relatorios"):
            query += " AND translate(lower(p.resultado_payload::text), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
            params.append(f"%{filtros['relatorios']}%")

        col_data = "b.created_at" if tipo_doc == "PARECER" else "p.created_at"
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
        except Exception as e:
            return 0

    def excluir_registro(self, tipo_doc, registro_id, motivo, excluido_por):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Resolve ID do usuário pela string do nome (caso a View passe apenas o nome)
                    cur.execute("SELECT id FROM common.usuarios WHERE nome_completo = %s LIMIT 1", (excluido_por,))
                    usr = cur.fetchone()
                    excluido_por_id = usr[0] if usr else None

                    if tipo_doc == "PARECER":
                        cur.execute("SELECT numero_parecer_ano FROM common.pareceres_base WHERE id = %s", (registro_id,))
                        linha = cur.fetchone()
                        numero = linha[0] if linha else registro_id
                        cur.execute("INSERT INTO common.lixeira (modulo, numero, motivo, excluido_por_id, data_exclusao) VALUES ('PARECER_quadro_horario', %s, %s, %s, NOW())", (numero, motivo, excluido_por_id))
                        # Deletar da base aciona ON DELETE CASCADE nas filhas
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                    else:
                        cur.execute("SELECT row_to_json(p) FROM quadro_horario.pesquisas p WHERE id = %s", (registro_id,))
                        linha = cur.fetchone()
                        if linha:
                            cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por_id, data_exclusao) VALUES ('PESQUISA_quadro_horario', %s, %s, %s, %s, NOW())", (registro_id, json.dumps(linha[0]), motivo, excluido_por_id))
                        cur.execute("DELETE FROM quadro_horario.pesquisas WHERE id = %s", (registro_id,))
                    conn.commit()
                    return True, "Registro excluído com sucesso."
        except Exception as e:
            return False, f"Erro ao excluir: {e}"

    def obter_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas ORDER BY codigo")
                    return [row[0] for row in cur.fetchall()]
        except Exception as e:
            return []