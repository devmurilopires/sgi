import psycopg2
import json
from config.database import get_db_connection

class RelatorioQuadroHorarioRepository:
    def _construir_query_filtros(self, tipo_doc, filtros):
        if tipo_doc == "PARECER":
            query = """
                SELECT p.id, b.numero_parecer_ano, p.processo, p.assunto, 
                       b.tipo_parecer as decisao, p.solicitante, p.evento, 
                       p.linhas_afetadas as linhas, p.data_evento, 
                       u.nome_completo as responsavel, b.created_at as data_criacao, 
                       p.caminho_arquivo, p.motivo_indeferimento
                FROM quadro_horario.pareceres p
                LEFT JOIN common.pareceres_base b ON p.id = b.id
                LEFT JOIN common.usuarios u ON b.criado_por_id = u.id 
                WHERE 1=1
            """
        else: # PESQUISA
            query = """
                SELECT id, titulo, tipo_pesquisa as tipo, data_inicio, data_fim, 
                       criado_por as responsavel, created_at as data_criacao, caminho_arquivo,
                       resultado_json as payload
                FROM quadro_horario.pesquisas
                WHERE 1=1
            """

        params = []
        mapeamento = {
            "PARECER": {
                "processo": "p.processo", "assunto": "p.assunto", "decisao": "b.tipo_parecer",
                "solicitante": "p.solicitante", "linhas": "p.linhas_afetadas", "responsavel": "u.nome_completo"
            },
            "PESQUISA": {
                "titulo": "titulo", "tipo": "tipo_pesquisa", "responsavel": "criado_por"
            }
        }

        doc_map = mapeamento[tipo_doc]
        for chave, valor in filtros.items():
            if valor and chave in doc_map:
                query += f" AND COALESCE({doc_map[chave]}::text, '') ILIKE %s"
                params.append(f"%{valor}%")

        # Filtro para buscar por data específica dentro da lista de relatórios utilizados
        if tipo_doc == "PESQUISA" and filtros.get("relatorios"):
            query += " AND resultado_json::text ILIKE %s"
            params.append(f"%{filtros['relatorios']}%")

        col_data = "b.created_at" if tipo_doc == "PARECER" else "created_at"
        if filtros.get("data_inicio"):
            query += f" AND ({col_data} IS NULL OR {col_data}::date >= %s)"
            params.append(filtros["data_inicio"])
        if filtros.get("data_fim"):
            query += f" AND ({col_data} IS NULL OR {col_data}::date <= %s)"
            params.append(filtros["data_fim"])

        query += " ORDER BY id DESC"
        return query, params
    
    def buscar_opcoes_dropdown(self, tipo_opcao):
        """
        Busca no banco de dados as opções ativas para preencher os dropdowns e filtros.
        
        :param tipo_opcao: String identificando a categoria (ex: 'qh_evento', 'qh_assunto')
        :return: Lista de strings com os valores ordenados alfabeticamente.
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # A query agora aponta para o schema 'common' e a tabela 'parametros_sistema'
                    # Filtramos pela 'categoria' e verificamos se 'is_ativo' é verdadeiro
                    query = """
                        SELECT valor 
                        FROM common.parametros_sistema 
                        WHERE categoria = %s AND is_ativo = true 
                        ORDER BY valor;
                    """
                    # Executamos a query substituindo o '%s' pela categoria desejada
                    cur.execute(query, (tipo_opcao,))
                    
                    # Retornamos uma lista simples (array) contendo apenas os valores textuais
                    return [r[0] for r in cur.fetchall()]
                    
        except Exception as e:
            print(f"Erro ao buscar opções de filtro para a categoria '{tipo_opcao}': {e}")
            return []

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
            print(f"Erro ao buscar dados: {e}")
            return []

    def contar_total(self, tipo_doc, filtros):
        query, params = self._construir_query_filtros(tipo_doc, filtros)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM ({query}) AS total", params)
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Erro ao contar total: {e}")
            return 0

    def excluir_registro(self, tipo_doc, registro_id, motivo, excluido_por):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if tipo_doc == "PARECER":
                        cur.execute("SELECT numero_parecer_ano FROM common.pareceres_base WHERE id = %s", (registro_id,))
                        linha = cur.fetchone()
                        numero = linha[0] if linha else registro_id
                        cur.execute("INSERT INTO common.lixeira (modulo, numero, motivo, excluido_por, data_exclusao) VALUES ('PARECER_quadro_horario', %s, %s, %s, NOW())", (numero, motivo, excluido_por))
                        cur.execute("DELETE FROM quadro_horario.pareceres WHERE id = %s", (registro_id,))
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (registro_id,))
                    else:
                        cur.execute("SELECT row_to_json(p) FROM quadro_horario.pesquisas p WHERE id = %s", (registro_id,))
                        linha = cur.fetchone()
                        if linha:
                            dados_json = linha[0]
                            cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, motivo, excluido_por, data_exclusao) VALUES ('PESQUISA_quadro_horario', %s, %s, %s, %s, NOW())", (registro_id, json.dumps(dados_json), motivo, excluido_por))
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