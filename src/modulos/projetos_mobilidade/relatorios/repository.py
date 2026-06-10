import psycopg2
from config.database import get_db_connection

class RelatorioProjetosMobilidadeRepository:
    def _construir_query_filtros(self, filtros):
        # MODIFICAÇÃO: Wrapper Query para permitir pesquisa fluida em colunas virtuais
        query = """
            SELECT * FROM (
                SELECT p.id, 
                       pb.numero_parecer_ano::text || '/' || pb.ano::text AS numero_completo, 
                       p.processo, 
                       o.nome AS origem, 
                       p.assunto, t.nome AS decisao, p.solicitante, 
                       pb.created_at AS data_criacao, u.nome_completo AS responsavel,
                       pb.caminho_arquivo
                FROM projetos_mobilidade.pareceres p
                JOIN common.pareceres_base pb ON p.id = pb.id
                LEFT JOIN common.tipos t ON pb.tipo_id = t.id
                LEFT JOIN common.origens o ON p.origem_id = o.id
                LEFT JOIN common.usuarios u ON pb.criado_por_id = u.id
            ) AS base
            WHERE 1=1
        """
        params = []
        
        # MODIFICAÇÃO: O número_completo agora está mapeado corretamente!
        mapeamento = {
            "numero_completo": "numero_completo",
            "processo": "processo", 
            "origem": "origem",
            "assunto": "assunto",
            "decisao": "decisao", 
            "solicitante": "solicitante"
        }

        for chave, valor in filtros.items():
            if valor and chave in mapeamento:
                coluna = mapeamento[chave]
                
                # BLINDAGEM: Decisão usa match exato para DEFERIDO não puxar INDEFERIDO
                if chave == "decisao":
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') = translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(valor)
                else:
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(f"%{valor}%")

        if filtros.get("data_inicio"):
            query += " AND data_criacao::date >= %s"
            params.append(filtros["data_inicio"])
        if filtros.get("data_fim"):
            query += " AND data_criacao::date <= %s"
            params.append(filtros["data_fim"])

        query += " ORDER BY data_criacao DESC"
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

    def excluir_registro(self, registro_id, motivo, excluido_por_nome):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM common.usuarios WHERE nome_completo = %s LIMIT 1", (excluido_por_nome,))
                    user_row = cur.fetchone()
                    if not user_row: return False, "Usuário não encontrado para auditoria."
                    excluido_por_id = user_row[0]

                    # CONSTRUÇÃO DO JSON COMPLETO COM NOME DO GERADOR
                    cur.execute("""
                        SELECT b.numero_parecer_ano, json_build_object(
                            'id', p.id, 'processo', p.processo, 'assunto', p.assunto,
                            'solicitante', p.solicitante, 'origem', o.nome, 'decisao', t.nome,
                            'gerado_por', u.nome_completo, 'caminho_arquivo', b.caminho_arquivo,
                            'data_criacao', b.created_at
                        )
                        FROM projetos_mobilidade.pareceres p
                        JOIN common.pareceres_base b ON p.id = b.id
                        LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
                        LEFT JOIN common.origens o ON p.origem_id = o.id
                        LEFT JOIN common.tipos t ON b.tipo_id = t.id
                        WHERE p.id = %s
                    """, (registro_id,))
                    
                    resultado = cur.fetchone()
                    if not resultado: return False, "Registro não encontrado para exclusão."
                        
                    numero_do_parecer = resultado[0]
                    dados_json = resultado[1]

                    import json
                    cur.execute("""
                        INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por_id, data_exclusao)
                        VALUES ('PARECER_projetos_mobilidade', %s, %s, %s, %s, NOW())
                    """, (numero_do_parecer, json.dumps(dados_json), motivo, excluido_por_id))

                    cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                    conn.commit()
                    return True, "Registro excluído e arquivado no histórico com sucesso."
                    
        except Exception as e:
            print(f"[LOG DB] Erro ao excluir Projeto de Mobilidade: {e}")
            return False, f"Erro ao excluir: {e}"
                    
        except Exception as e:
            print(f"[LOG DB] Erro ao excluir Projeto de Mobilidade: {e}")
            return False, f"Erro ao excluir: {e}"
        

    def atualizar_registro(self, registro_id, dados):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # 1. Atualiza Tabela Base (Responsável, Data, Decisão, Número)
                    if dados.get("numero_completo"):
                        try:
                            num = int(str(dados["numero_completo"]).split('/')[0])
                            cur.execute("UPDATE common.pareceres_base SET numero_parecer_ano = %s WHERE id = %s", (num, registro_id))
                        except: pass

                    cur.execute("""
                        UPDATE common.pareceres_base pb
                        SET tipo_id = COALESCE((SELECT id FROM common.tipos WHERE contexto IN ('PARECER', 'DECISAO_PARECER') AND nome = %(decisao)s LIMIT 1), pb.tipo_id),
                            criado_por_id = COALESCE((SELECT id FROM common.usuarios WHERE nome_completo = %(responsavel)s LIMIT 1), pb.criado_por_id),
                            created_at = COALESCE(to_timestamp(%(data_criacao)s, 'DD/MM/YYYY HH24:MI:SS'), to_timestamp(%(data_criacao)s, 'DD/MM/YYYY'), pb.created_at)
                        FROM projetos_mobilidade.pareceres p
                        WHERE pb.id = p.id AND p.id = %(id)s
                    """, {
                        "id": registro_id,
                        "decisao": dados.get("decisao"),
                        "responsavel": dados.get("responsavel"),
                        "data_criacao": dados.get("data_criacao")
                    })

                    # 2. Atualiza Tabela Específica de Projetos de Mobilidade
                    cur.execute("""
                        UPDATE projetos_mobilidade.pareceres
                        SET processo = COALESCE(%(processo)s, processo),
                            assunto = COALESCE(%(assunto)s, assunto),
                            solicitante = COALESCE(%(solicitante)s, solicitante),
                            origem_id = COALESCE((SELECT id FROM common.origens WHERE nome = %(origem)s LIMIT 1), origem_id)
                        WHERE id = %(id)s
                    """, {
                        "id": registro_id,
                        "processo": dados.get("processo"),
                        "assunto": dados.get("assunto"),
                        "solicitante": dados.get("solicitante"),
                        "origem": dados.get("origem")
                    })
                    conn.commit()
            return True, "Registro atualizado com sucesso no banco de dados."
        except Exception as e:
            print(f"[LOG DB] Erro atualizar_registro Projetos Mobilidade: {e}")
            return False, "Erro ao atualizar registro. Verifique se as informações inseridas são válidas."