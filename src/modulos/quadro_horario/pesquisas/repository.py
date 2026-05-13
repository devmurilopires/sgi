import json
from config.database import get_db_connection

class PesquisaQuadroHorarioRepository:
    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Trazendo apenas linhas ativas para evitar sujeira na View
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas WHERE is_ativo = true ORDER BY codigo;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar linhas: {e}")
            return []

    def salvar_pesquisa(self, codigo_linha, nome_tipo, datas, payload_json, criado_por):
        # Desempacota a lista de datas nas 3 colunas (se houver menos de 3, envia None/NULL)
        d1 = datas[0] if len(datas) > 0 else None
        d2 = datas[1] if len(datas) > 1 else None
        d3 = datas[2] if len(datas) > 2 else None

        # 1. MODIFICAÇÃO: Uso de subqueries para resolver IDs (Linha, Tipo e Usuário)
        # 2. MODIFICAÇÃO: Inserção das 3 datas de forma atômica
        query = """
            INSERT INTO quadro_horario.pesquisas (
                linha_id, 
                tipo_pesquisa_id, 
                data_pesquisa_1, 
                data_pesquisa_2, 
                data_pesquisa_3, 
                resultado_payload, 
                criado_por_id
            ) VALUES (
                (SELECT id FROM common.linhas WHERE codigo = %s LIMIT 1),
                (SELECT id FROM common.tipos WHERE contexto = 'TIPO_PESQUISA' AND nome ILIKE %s LIMIT 1),
                %s, %s, %s,
                %s::jsonb,
                (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %s LIMIT 1)
            ) RETURNING id;
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    json_str = json.dumps(payload_json, ensure_ascii=False)
                    
                    cur.execute(query, (
                        codigo_linha,
                        nome_tipo,
                        d1, d2, d3,
                        json_str,
                        f"%{criado_por}%" # ILIKE para evitar erros por falta de sobrenome
                    ))
                    conn.commit()
                    row = cur.fetchone()
                    return True, f"Pesquisa operacional salva com sucesso (ID: {row[0]})."
        except Exception as e:
            print(f"[LOG DB] Erro crítico: {e}")
            return False, f"Erro ao salvar no banco. Verifique se a linha e o tipo existem. Detalhe: {e}"