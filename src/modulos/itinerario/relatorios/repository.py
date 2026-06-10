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

    def excluir_registro(self, tipo_doc, registro_id, motivo, excluido_por_nome):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # 1. Pega o ID do usuário que está excluindo
                    cur.execute("SELECT id FROM common.usuarios WHERE nome_completo = %s LIMIT 1", (excluido_por_nome,))
                    user_row = cur.fetchone()
                    excluido_por_id = user_row[0] if user_row else None

                    import json
                    if tipo_doc == "PARECER":
                        # CONSTRUÇÃO DO JSON COMPLETO COM NOME DO GERADOR (PARECER)
                        cur.execute("""
                            SELECT b.numero_parecer_ano, json_build_object(
                                'id', p.id, 'processo', p.processo, 'assunto', p.assunto,
                                'solicitante', p.solicitante, 'origem', o.nome, 'decisao', t.nome,
                                'gerado_por', u.nome_completo, 'caminho_arquivo', b.caminho_arquivo,
                                'data_criacao', b.created_at, 'endereco', p.endereco, 'evento', p.evento,
                                'motivo_indeferimento', p.motivo_indeferimento, 'periodo', p.periodo
                            )
                            FROM itinerario.pareceres p
                            JOIN common.pareceres_base b ON p.id = b.id
                            LEFT JOIN common.tipos t ON b.tipo_id = t.id
                            LEFT JOIN common.origens o ON p.origem_id = o.id
                            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
                            WHERE p.id = %s
                        """, (registro_id,))
                        
                        res = cur.fetchone()
                        if res:
                            numero, dados_json = res
                            cur.execute("""
                                INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por_id, data_exclusao)
                                VALUES ('PARECER_itinerario', %s, %s, %s, %s, NOW())
                            """, (numero, json.dumps(dados_json), motivo, excluido_por_id))
                        
                        # Deleta em cascata através da base
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                        
                    else:
                        # CONSTRUÇÃO DO JSON COMPLETO COM NOME DO GERADOR (ORDEM DE SERVIÇO)
                        cur.execute("""
                            SELECT os.numero, json_build_object(
                                'id', os.id, 'processo', os.processo_adm, 'solicitante', os.solicitante,
                                'origem', o.nome, 'gerado_por', u.nome_completo, 'caminho_arquivo', os.caminho_arquivo,
                                'data_criacao', os.data_emissao, 'endereco', os.endereco,
                                'horario_inicio', os.horario_inicio, 'horario_fim', os.horario_fim,
                                'evento', os.evento, 'nome_corrida', os.nome_corrida, 'tipo_obra', os.tipo_obra,
                                'km', os.km
                            )
                            FROM itinerario.ordens_servico os
                            LEFT JOIN common.origens o ON os.origem_id = o.id
                            LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
                            WHERE os.id = %s
                        """, (registro_id,))
                        
                        res = cur.fetchone()
                        if res:
                            numero, dados_json = res
                            cur.execute("""
                                INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por_id, data_exclusao)
                                VALUES ('OS_itinerario', %s, %s, %s, %s, NOW())
                            """, (numero, json.dumps(dados_json), motivo, excluido_por_id))
                            
                        # Deleta da tabela principal
                        cur.execute("DELETE FROM itinerario.ordens_servico WHERE id = %s", (registro_id,))
                        
                    conn.commit()
                    return True, "Registro excluído e arquivado no histórico com sucesso."
        except Exception as e:
            print(f"[LOG DB] Erro ao excluir no Itinerário: {e}")
            return False, f"Erro ao excluir: {e}"
        
    def atualizar_registro(self, tipo_doc, registro_id, dados):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if tipo_doc == "PARECER":
                        # Atualiza Número da Base
                        if dados.get("numero_completo"):
                            try:
                                num = int(str(dados["numero_completo"]).split('/')[0])
                                cur.execute("UPDATE common.pareceres_base SET numero_parecer_ano = %s WHERE id = %s", (num, registro_id))
                            except: pass

                        # Atualiza dados da Tabela Base (Decisão, Responsável, Data)
                        cur.execute("""
                            UPDATE common.pareceres_base pb
                            SET tipo_id = COALESCE((SELECT id FROM common.tipos WHERE contexto IN ('PARECER', 'DECISAO_PARECER') AND nome = %(decisao)s LIMIT 1), pb.tipo_id),
                                criado_por_id = COALESCE((SELECT id FROM common.usuarios WHERE nome_completo = %(responsavel)s LIMIT 1), pb.criado_por_id),
                                created_at = COALESCE(to_timestamp(%(data_criacao)s, 'DD/MM/YYYY HH24:MI:SS'), to_timestamp(%(data_criacao)s, 'DD/MM/YYYY'), pb.created_at)
                            FROM itinerario.pareceres p
                            WHERE pb.id = p.id AND p.id = %(id)s
                        """, {
                            "id": registro_id,
                            "decisao": dados.get("decisao"),
                            "responsavel": dados.get("responsavel"),
                            "data_criacao": dados.get("data_criacao")
                        })
                        
                        # Atualiza a Tabela de Pareceres Específica
                        cur.execute("""
                            UPDATE itinerario.pareceres
                            SET processo = COALESCE(%(processo)s, processo),
                                assunto = COALESCE(%(assunto)s, assunto),
                                solicitante = COALESCE(%(solicitante)s, solicitante),
                                endereco = COALESCE(%(endereco)s, endereco),
                                evento = COALESCE(%(evento)s, evento),
                                origem_id = COALESCE((SELECT id FROM common.origens WHERE nome = %(origem)s LIMIT 1), origem_id)
                            WHERE id = %(id)s
                        """, {
                            "id": registro_id, 
                            "processo": dados.get("processo"),
                            "assunto": dados.get("assunto"),
                            "solicitante": dados.get("solicitante"),
                            "endereco": dados.get("endereco"),
                            "evento": dados.get("evento"),
                            "origem": dados.get("origem")
                        })

                        # Atualiza Linhas Relacionadas (N:M)
                        if "linhas" in dados:
                            cur.execute("DELETE FROM itinerario.pareceres_linhas WHERE parecer_id = %s", (registro_id,))
                            codigos = [c.strip() for c in dados["linhas"].split(',') if c.strip()]
                            for cod in codigos:
                                cur.execute("INSERT INTO itinerario.pareceres_linhas (parecer_id, linha_id) SELECT %s, id FROM common.linhas WHERE codigo = %s LIMIT 1", (registro_id, cod))

                    else: # OS (ORDEM DE SERVIÇO)
                        # Atualiza Número da OS
                        if dados.get("numero_os"):
                            try:
                                num = int(str(dados["numero_os"]).split('/')[0])
                                cur.execute("UPDATE itinerario.ordens_servico SET numero = %s WHERE id = %s", (num, registro_id))
                            except: pass

                        # Atualiza Tabela Principal da OS
                        cur.execute("""
                            UPDATE itinerario.ordens_servico
                            SET processo_adm = COALESCE(%(processo)s, processo_adm),
                                solicitante = COALESCE(%(solicitante)s, solicitante),
                                endereco = COALESCE(%(endereco)s, endereco),
                                evento = CASE WHEN %(tipo)s = 'EVENTOS' THEN %(evento)s ELSE NULL END,
                                nome_corrida = CASE WHEN %(tipo)s = 'CORRIDA' THEN %(evento)s ELSE NULL END,
                                tipo_obra = CASE WHEN %(tipo)s = 'OBRAS' THEN %(evento)s ELSE NULL END,
                                tipo_evento_id = COALESCE((SELECT id FROM common.tipos WHERE contexto = 'TIPO_EVENTO_OS' AND nome = %(tipo)s LIMIT 1), tipo_evento_id),
                                origem_id = COALESCE((SELECT id FROM common.origens WHERE nome = %(origem)s LIMIT 1), origem_id),
                                responsavel_id = COALESCE((SELECT id FROM common.usuarios WHERE nome_completo = %(responsavel)s LIMIT 1), responsavel_id),
                                data_emissao = COALESCE(to_timestamp(%(data_criacao)s, 'DD/MM/YYYY HH24:MI:SS'), to_timestamp(%(data_criacao)s, 'DD/MM/YYYY'), data_emissao)
                            WHERE id = %(id)s
                        """, {
                            "id": registro_id,
                            "processo": dados.get("processo"),
                            "solicitante": dados.get("solicitante"),
                            "endereco": dados.get("endereco"),
                            "evento": dados.get("evento"),
                            "tipo": dados.get("tipo"),
                            "origem": dados.get("origem"),
                            "responsavel": dados.get("responsavel"),
                            "data_criacao": dados.get("data_criacao")
                        })

                        # Atualiza Linhas e Empresas Relacionadas (N:M)
                        if "linhas" in dados:
                            cur.execute("DELETE FROM itinerario.os_linhas WHERE os_id = %s", (registro_id,))
                            codigos = [c.strip() for c in dados["linhas"].split(',') if c.strip()]
                            for cod in codigos:
                                cur.execute("INSERT INTO itinerario.os_linhas (os_id, linha_id) SELECT %s, id FROM common.linhas WHERE codigo = %s LIMIT 1", (registro_id, cod))
                                
                        if "empresa" in dados:
                            cur.execute("DELETE FROM itinerario.os_empresas WHERE os_id = %s", (registro_id,))
                            empresas = [e.strip() for e in dados["empresa"].split(',') if e.strip()]
                            for emp in empresas:
                                cur.execute("INSERT INTO itinerario.os_empresas (os_id, empresa_id) SELECT %s, id FROM common.empresas WHERE nome ILIKE %s LIMIT 1", (registro_id, emp))

                    conn.commit()
            return True, "Registro atualizado com sucesso no banco de dados."
        except Exception as e:
            print(f"[LOG DB] Erro atualizar_registro: {e}")
            return False, f"Erro ao atualizar registro: Verifique se os dados são válidos e se as linhas/empresas existem." 

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