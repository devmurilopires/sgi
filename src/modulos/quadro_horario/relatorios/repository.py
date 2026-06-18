import psycopg2
import json
from config.database import get_db_connection

class RelatorioQuadroHorarioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            # MODIFICAÇÃO: Inserido 'tm.nome AS manifestacao' e o JOIN correspondente
            query = """
                SELECT * FROM (
                    SELECT p.id, 
                           b.numero_parecer_ano::text || '/' || b.ano::text AS numero_completo, 
                           p.processo, o.nome AS origem, p.assunto, 
                           t.nome AS decisao, tm.nome AS manifestacao, p.solicitante, p.evento, 
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
                    LEFT JOIN common.tipos tm ON p.tipo_manifestacao_id = tm.id
                    LEFT JOIN common.origens o ON p.origem_id = o.id
                    LEFT JOIN common.usuarios u ON b.criado_por_id = u.id 
                ) AS base
                WHERE 1=1
            """
        else: # PESQUISA
            query = """
                SELECT * FROM (
                    SELECT p.id, 
                           l.codigo || ' - ' || l.nome AS titulo, 
                           tp.nome AS tipo, 
                           p.data_pesquisa_1 AS data_inicio, 
                           COALESCE(p.data_pesquisa_3, p.data_pesquisa_2, p.data_pesquisa_1) AS data_fim, 
                           u.nome_completo AS responsavel, p.created_at AS data_criacao, 
                           NULL AS caminho_arquivo,
                           p.resultado_payload AS payload,
                           p.data_pesquisa_1, p.data_pesquisa_2, p.data_pesquisa_3
                    FROM quadro_horario.pesquisas p
                    LEFT JOIN common.linhas l ON p.linha_id = l.id
                    LEFT JOIN common.tipos tp ON p.tipo_pesquisa_id = tp.id
                    LEFT JOIN common.usuarios u ON p.criado_por_id = u.id
                ) AS base
                WHERE 1=1
            """

        params = []
        mapeamento = {
            "PARECER": {
                "numero_completo": "numero_completo", "processo": "processo", "origem": "origem", 
                "decisao": "decisao", "manifestacao": "manifestacao", "assunto": "assunto", 
                "solicitante": "solicitante", "responsavel": "responsavel"
            },
            "PESQUISA": {
                "titulo": "titulo", "tipo": "tipo", "responsavel": "responsavel"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                coluna = doc_map[chave]
                
                if chave == "decisao" or chave == "manifestacao":
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') = translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(valor)
                else:
                    query += f" AND translate(lower(COALESCE({coluna}::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
                    params.append(f"%{valor}%")

        if tipo_doc == "PESQUISA" and filtros.get("relatorios"):
            query += " AND translate(lower(COALESCE(payload::text, '')), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') LIKE translate(lower(%s), 'áàãâäéèêëíìîïóòõôöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')"
            params.append(f"%{filtros['relatorios']}%")

        col_data = "data_criacao"
        if filtros.get("data_inicio"):
            query += f" AND {col_data}::date >= %s"
            params.append(filtros["data_inicio"])
        if filtros.get("data_fim"):
            query += f" AND {col_data}::date <= %s"
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
                    cur.execute("SELECT id FROM common.usuarios WHERE nome_completo = %s LIMIT 1", (excluido_por,))
                    usr = cur.fetchone()
                    excluido_por_id = usr[0] if usr else None

                    import json
                    if tipo_doc == "PARECER":
                        # CONSTRUÇÃO DO JSON COMPLETO COM NOME DO GERADOR
                        cur.execute("""
                            SELECT b.numero_parecer_ano, json_build_object(
                                'id', p.id, 'processo', p.processo, 'assunto', p.assunto, 
                                'solicitante', p.solicitante, 'evento', p.evento, 
                                'origem', o.nome, 'decisao', t.nome,
                                'gerado_por', u.nome_completo, 'caminho_arquivo', b.caminho_arquivo
                            )
                            FROM quadro_horario.pareceres p
                            JOIN common.pareceres_base b ON p.id = b.id
                            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
                            LEFT JOIN common.origens o ON p.origem_id = o.id
                            LEFT JOIN common.tipos t ON b.tipo_id = t.id
                            WHERE p.id = %s
                        """, (registro_id,))
                        res = cur.fetchone()
                        if res:
                            numero, dados_json = res
                            cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por_id, data_exclusao) VALUES ('PARECER_quadro_horario', %s, %s, %s, %s, NOW())", (numero, json.dumps(dados_json), motivo, excluido_por_id))
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                    else:
                        # CONSTRUÇÃO DO JSON PARA PESQUISAS
                        cur.execute("""
                            SELECT json_build_object(
                                'id', p.id, 'titulo', l.codigo || ' - ' || l.nome,
                                'data_inicio', p.data_pesquisa_1, 
                                'data_fim', COALESCE(p.data_pesquisa_3, p.data_pesquisa_2, p.data_pesquisa_1),
                                'gerado_por', u.nome_completo
                            )
                            FROM quadro_horario.pesquisas p
                            LEFT JOIN common.linhas l ON p.linha_id = l.id
                            LEFT JOIN common.usuarios u ON p.criado_por_id = u.id
                            WHERE p.id = %s
                        """, (registro_id,))
                        res = cur.fetchone()
                        if res:
                            dados_json = res[0]
                            cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por_id, data_exclusao) VALUES ('PESQUISA_quadro_horario', %s, %s, %s, %s, NOW())", (registro_id, json.dumps(dados_json), motivo, excluido_por_id))
                        cur.execute("DELETE FROM quadro_horario.pesquisas WHERE id = %s", (registro_id,))
                    conn.commit()
                    return True, "Registro excluído com sucesso."
        except Exception as e:
            return False, f"Erro ao excluir: {e}"
        
    def atualizar_registro(self, tipo_doc, registro_id, dados):
        # =====================================================================
        # BLINDAGEM SÊNIOR: Sanitização de Dados
        # Removemos os marcadores de vazio da interface e limpamos as datas!
        # =====================================================================
        for k, v in dados.items():
            if isinstance(v, str):
                v_clean = v.strip()
                if v_clean in ["-", ""]:
                    dados[k] = None

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if tipo_doc == "PARECER":
                        # (O bloco do PARECER mantém-se igual ao que você já tinha)
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
                            FROM quadro_horario.pareceres p
                            WHERE pb.id = p.id AND p.id = %(id)s
                        """, {"id": registro_id, "decisao": dados.get("decisao"), "responsavel": dados.get("responsavel"), "data_criacao": dados.get("data_criacao")})

                        cur.execute("""
                            UPDATE quadro_horario.pareceres
                            SET processo = COALESCE(%(processo)s, processo), assunto = COALESCE(%(assunto)s, assunto),
                                solicitante = COALESCE(%(solicitante)s, solicitante), evento = COALESCE(%(evento)s, evento),
                                data_evento = COALESCE(%(data_evento)s, data_evento), motivo_indeferimento = COALESCE(%(motivo)s, motivo_indeferimento),
                                origem_id = COALESCE((SELECT id FROM common.origens WHERE nome = %(origem)s LIMIT 1), origem_id)
                            WHERE id = %(id)s
                        """, {"id": registro_id, "processo": dados.get("processo"), "assunto": dados.get("assunto"), "solicitante": dados.get("solicitante"), "evento": dados.get("evento"), "data_evento": dados.get("data_evento"), "motivo": dados.get("motivo_indeferimento"), "origem": dados.get("origem")})
                        
                        str_linhas = dados.get("linhas")
                        if str_linhas:
                            cur.execute("DELETE FROM quadro_horario.pareceres_linhas WHERE parecer_id = %s", (registro_id,))
                            for cod in [c.strip() for c in str_linhas.split(',') if c.strip()]:
                                cur.execute("INSERT INTO quadro_horario.pareceres_linhas (parecer_id, linha_id) SELECT %s, id FROM common.linhas WHERE codigo = %s LIMIT 1", (registro_id, cod))
                                
                    else: # EDIÇÃO DE PESQUISA
                        # 1. Atualiza a Linha
                        if dados.get("titulo"):
                            linha_codigo = str(dados["titulo"]).split(" - ")[0].strip()
                            cur.execute("""
                                UPDATE quadro_horario.pesquisas 
                                SET linha_id = COALESCE((SELECT id FROM common.linhas WHERE codigo = %(codigo)s LIMIT 1), linha_id)
                                WHERE id = %(id)s
                            """, {"codigo": linha_codigo, "id": registro_id})

                        # 2. Atualiza os metadados e as 3 DATAS NO BANCO DE DADOS
                        cur.execute("""
                            UPDATE quadro_horario.pesquisas
                            SET tipo_pesquisa_id = COALESCE((SELECT id FROM common.tipos WHERE contexto = 'PESQUISA' AND nome = %(tipo)s LIMIT 1), tipo_pesquisa_id),
                                criado_por_id = COALESCE((SELECT id FROM common.usuarios WHERE nome_completo = %(responsavel)s LIMIT 1), criado_por_id),
                                data_pesquisa_1 = to_date(%(dp1)s, 'DD/MM/YYYY'),
                                data_pesquisa_2 = to_date(%(dp2)s, 'DD/MM/YYYY'),
                                data_pesquisa_3 = to_date(%(dp3)s, 'DD/MM/YYYY')
                            WHERE id = %(id)s
                        """, {
                            "id": registro_id,
                            "tipo": dados.get("tipo"),
                            "responsavel": dados.get("responsavel"),
                            "dp1": dados.get("dp1"), "dp2": dados.get("dp2"), "dp3": dados.get("dp3")
                        })
                        
                        # 3. Atualiza o JSON Payload para a interface não quebrar as tabelas
                        cur.execute("SELECT resultado_payload FROM quadro_horario.pesquisas WHERE id = %s", (registro_id,))
                        res_payload = cur.fetchone()
                        if res_payload and res_payload[0]:
                            payload_obj = res_payload[0]
                            if isinstance(payload_obj, str):
                                import json
                                try: payload_obj = json.loads(payload_obj)
                                except: pass
                            
                            if isinstance(payload_obj, dict):
                                novas_datas = [d for d in [dados.get("dp1"), dados.get("dp2"), dados.get("dp3")] if d]
                                payload_obj["datas"] = novas_datas
                                import json
                                cur.execute("UPDATE quadro_horario.pesquisas SET resultado_payload = %s::jsonb WHERE id = %s", (json.dumps(payload_obj, ensure_ascii=False), registro_id))
                                
                    conn.commit()
            return True, "Registro atualizado com sucesso no banco de dados."
        except Exception as e:
            print(f"[LOG DB] Erro atualizar_registro: {e}")
            return False, "Erro ao atualizar registro. Verifique se as informações são válidas."

    def obter_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas ORDER BY codigo")
                    return [row[0] for row in cur.fetchall()]
        except Exception as e:
            return []