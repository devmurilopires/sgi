import psycopg2
from config.database import get_db_connection

class RelatorioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            # MODIFICAÇÃO: Inserida a subquery para puxar o ID do Ponto (ponto_id)
            query = """
                SELECT * FROM (
                    SELECT p.id, pb.numero_parecer_ano::text || '/' || pb.ano::text AS numero_completo, 
                           p.processo, 
                           (SELECT string_agg(pp.ponto_id, ', ') FROM ponto_parada.pareceres_pontos pp WHERE pp.parecer_id = p.id) AS id_ponto,
                           o.nome AS origem, p.assunto, t.nome AS decisao, 
                           p.tipo_execucao AS acao, p.item AS item,
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
            query = """
                SELECT * FROM (
                    SELECT os.id, os.numero AS numero_os, os.processo, o.nome AS origem, 
                           ta.nome AS acao, ti.nome AS item, 
                           tm.nome AS empresa, 
                           os.ponto_principal_id, 
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
                    LEFT JOIN common.tipos tm ON os.modelo_id = tm.id 
                    LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
                ) AS base
                WHERE 1=1
            """

        params = []
        mapeamento = {
            "PARECER": {
                "numero_completo": "numero_completo", "processo": "processo", "origem": "origem", "id_ponto": "id_ponto",
                "assunto": "assunto", "decisao": "decisao", "solicitante": "solicitante", 
                "acao": "acao", "item": "item", "responsavel": "responsavel", "endereco": "endereco"
            },
            "OS": {
                "numero_os": "numero_os", "processo": "processo", "origem": "origem", "acao": "acao", "item": "item",
                "status": "status", "bairro": "bairro", "responsavel": "responsavel",
                "id_ponto": "ponto_principal_id", "empresa": "empresa", "endereco": "endereco"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                coluna = doc_map[chave]
                if chave == "decisao" or chave == "empresa":
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') = translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(valor)
                elif chave == "id_ponto" and tipo_doc == "OS":
                    query += f""" AND (
                        translate(lower(COALESCE(ponto_principal_id::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') OR 
                        translate(lower(COALESCE(pontos_adicionais::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')
                    )"""
                    params.extend([f"%{valor}%", f"%{valor}%"])
                elif chave == "id_ponto" and tipo_doc == "PARECER":
                    query += f" AND translate(lower(COALESCE(id_ponto::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(f"%{valor}%")
                else:
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(f"%{valor}%")

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

    def excluir_registro(self, tipo_doc, registro_id, motivo, excluido_por_nome):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM common.usuarios WHERE nome_completo = %s LIMIT 1", (excluido_por_nome,))
                    user_row = cur.fetchone()
                    excluido_por_id = user_row[0] if user_row else None

                    import json
                    if tipo_doc == "PARECER":
                        cur.execute("""
                            SELECT pb.numero_parecer_ano, json_build_object(
                                'id', p.id, 'processo', p.processo, 'assunto', p.assunto,
                                'solicitante', p.solicitante, 'origem', o.nome, 'decisao', t.nome,
                                'acao', p.tipo_execucao, 'item', p.item,
                                'endereco', p.endereco_vistoria, 'motivo_indeferimento', p.motivo_indeferimento,
                                'gerado_por', u.nome_completo, 'caminho_arquivo', pb.caminho_arquivo,
                                'data_criacao', pb.created_at
                            )
                            FROM ponto_parada.pareceres p
                            JOIN common.pareceres_base pb ON p.id = pb.id
                            LEFT JOIN common.tipos t ON pb.tipo_id = t.id
                            LEFT JOIN common.origens o ON p.origem_id = o.id
                            LEFT JOIN common.usuarios u ON pb.criado_por_id = u.id
                            WHERE p.id = %s
                        """, (registro_id,))
                        
                        res = cur.fetchone()
                        if res:
                            numero, dados_json = res
                            cur.execute("""
                                INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por_id, data_exclusao)
                                VALUES ('PARECER_ponto_parada', %s, %s, %s, %s, NOW())
                            """, (numero, json.dumps(dados_json), motivo, excluido_por_id))

                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                        
                    else:
                        cur.execute("""
                            SELECT os.numero, json_build_object(
                                'id', os.id, 'numero_os', os.numero, 'origem', o.nome,
                                'acao', ta.nome, 'item', ti.nome, 'ponto_principal_id', os.ponto_principal_id,
                                'bairro', e.bairro, 'endereco', (e.logradouro || COALESCE(', ' || e.numero, '') || COALESCE(' - ' || e.complemento, '')),
                                'status', os.status_conclusao, 'gerado_por', u.nome_completo, 
                                'caminho_arquivo', os.caminho_arquivo, 'data_criacao', os.data_criacao
                            )
                            FROM ponto_parada.ordens_servico os
                            LEFT JOIN ponto_parada.enderecos_cadastrados e ON os.ponto_principal_id = e.id
                            LEFT JOIN common.origens o ON os.origem_id = o.id
                            LEFT JOIN common.tipos ta ON os.tipo_acao_id = ta.id
                            LEFT JOIN common.tipos ti ON os.tipo_item_id = ti.id
                            LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
                            WHERE os.id = %s
                        """, (registro_id,))
                        
                        res = cur.fetchone()
                        if res:
                            numero, dados_json = res
                            cur.execute("""
                                INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por_id, data_exclusao)
                                VALUES ('OS_ponto_parada', %s, %s, %s, %s, NOW())
                            """, (numero, json.dumps(dados_json), motivo, excluido_por_id))
                            
                        cur.execute("DELETE FROM ponto_parada.ordens_servico WHERE id = %s", (registro_id,))
                        
                    conn.commit()
                    return True, "Registro excluído e arquivado no histórico com sucesso."
        except Exception as e:
            return False, f"Erro ao excluir: {e}"
        
    def atualizar_registro(self, tipo_doc, registro_id, dados):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if tipo_doc == "PARECER":
                        if dados.get("numero_completo"):
                            try:
                                num = int(str(dados["numero_completo"]).split('/')[0])
                                cur.execute("UPDATE common.pareceres_base SET numero_parecer_ano = %s WHERE id = %s", (num, registro_id))
                            except: pass

                        # MODIFICAÇÃO: COALESCE agora suporta a atualização do 'caminho_arquivo'
                        cur.execute("""
                            UPDATE common.pareceres_base pb
                            SET tipo_id = COALESCE((SELECT id FROM common.tipos WHERE contexto IN ('PARECER', 'DECISAO_PARECER') AND nome = %(decisao)s LIMIT 1), pb.tipo_id),
                                criado_por_id = COALESCE((SELECT id FROM common.usuarios WHERE nome_completo = %(responsavel)s LIMIT 1), pb.criado_por_id),
                                created_at = COALESCE(to_timestamp(%(data_criacao)s, 'DD/MM/YYYY HH24:MI:SS'), to_timestamp(%(data_criacao)s, 'DD/MM/YYYY'), pb.created_at),
                                caminho_arquivo = COALESCE(%(caminho)s, caminho_arquivo)
                            FROM ponto_parada.pareceres p
                            WHERE pb.id = p.id AND p.id = %(id)s
                        """, {
                            "id": registro_id, "decisao": dados.get("decisao"),
                            "responsavel": dados.get("responsavel"), "data_criacao": dados.get("data_criacao"), "caminho": dados.get("caminho")
                        })

                        cur.execute("""
                            UPDATE ponto_parada.pareceres
                            SET processo = COALESCE(%(processo)s, processo),
                                assunto = COALESCE(%(assunto)s, assunto),
                                solicitante = COALESCE(%(solicitante)s, solicitante),
                                endereco_vistoria = COALESCE(%(endereco)s, endereco_vistoria),
                                motivo_indeferimento = COALESCE(%(motivo)s, motivo_indeferimento),
                                origem_id = COALESCE((SELECT id FROM common.origens WHERE nome = %(origem)s LIMIT 1), origem_id),
                                tipo_execucao = COALESCE(%(acao)s, tipo_execucao),
                                item = COALESCE(%(item)s, item)
                            WHERE id = %(id)s
                        """, {
                            "id": registro_id, "processo": dados.get("processo"),
                            "assunto": dados.get("assunto"), "solicitante": dados.get("solicitante"),
                            "endereco": dados.get("endereco"), "motivo": dados.get("motivo_indeferimento"),
                            "origem": dados.get("origem"), "acao": dados.get("acao"), "item": dados.get("item")
                        })
                        
                    else: # ORDEM DE SERVIÇO
                        if "id_ponto" in dados and dados["id_ponto"] and str(dados["id_ponto"]).strip() != "-":
                            ponto_str = str(dados["id_ponto"]).split('(')[0].strip()
                            dados["ponto_id_clean"] = ponto_str if ponto_str else None
                        else:
                            dados["ponto_id_clean"] = None

                        dt_criacao = dados.get("data_criacao")
                        if not dt_criacao or str(dt_criacao).strip() in ["", "-"]:
                            dados["data_criacao_clean"] = None
                        else:
                            dados["data_criacao_clean"] = str(dt_criacao).strip()

                        # MODIFICAÇÃO: Atualiza também o 'caminho_arquivo'
                        cur.execute("""
                            UPDATE ponto_parada.ordens_servico
                            SET numero = COALESCE(%(numero_os)s, numero),
                                processo = COALESCE(%(processo)s, processo),
                                ponto_principal_id = COALESCE(%(ponto_id_clean)s, ponto_principal_id),
                                origem_id = COALESCE((SELECT id FROM common.origens WHERE nome = %(origem)s LIMIT 1), origem_id),
                                tipo_acao_id = COALESCE((SELECT id FROM common.tipos WHERE contexto = 'ACAO_OS' AND nome = %(acao)s LIMIT 1), tipo_acao_id),
                                tipo_item_id = COALESCE((SELECT id FROM common.tipos WHERE contexto IN ('ITEM_URBMIDIA', 'ITEM_MCMENSAGEM') AND nome = %(item)s LIMIT 1), tipo_item_id),
                                modelo_id = COALESCE((SELECT id FROM common.tipos WHERE contexto = 'MODELO_OS' AND nome = %(empresa)s LIMIT 1), modelo_id),
                                status_conclusao = COALESCE(%(status)s, status_conclusao),
                                responsavel_id = COALESCE((SELECT id FROM common.usuarios WHERE nome_completo = %(responsavel)s LIMIT 1), responsavel_id),
                                data_criacao = COALESCE(to_timestamp(%(data_criacao_clean)s, 'DD/MM/YYYY HH24:MI:SS'), to_timestamp(%(data_criacao_clean)s, 'DD/MM/YYYY'), data_criacao),
                                caminho_arquivo = COALESCE(%(caminho)s, caminho_arquivo)
                            WHERE id = %(id)s
                            RETURNING ponto_principal_id
                        """, {
                            "id": registro_id, 
                            "numero_os": dados.get("numero_os"), 
                            "processo": dados.get("processo"),
                            "ponto_id_clean": dados["ponto_id_clean"],
                            "origem": dados.get("origem"), 
                            "acao": dados.get("acao"), 
                            "item": dados.get("item"),
                            "empresa": dados.get("empresa"),
                            "status": dados.get("status"), 
                            "responsavel": dados.get("responsavel"), 
                            "data_criacao_clean": dados["data_criacao_clean"],
                            "caminho": dados.get("caminho")
                        })
                        
                        res = cur.fetchone()
                        if res and res[0] and (dados.get("bairro") or dados.get("endereco")):
                            cur.execute("""
                                UPDATE ponto_parada.enderecos_cadastrados
                                SET bairro = COALESCE(%(bairro)s, bairro), logradouro = COALESCE(%(endereco)s, logradouro)
                                WHERE id = %(p_id)s
                            """, {"bairro": dados.get("bairro"), "endereco": dados.get("endereco"), "p_id": res[0]})
                    conn.commit()
            return True, "Registro atualizado com sucesso."
        except Exception as e:
            print(f"[LOG DB] Erro atualizar_registro: {e}")
            return False, "Erro ao atualizar registro. Verifique os dados e tente novamente."

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