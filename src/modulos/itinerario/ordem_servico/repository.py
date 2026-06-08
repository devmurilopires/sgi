import psycopg2
from config.database import get_db_connection

class OSItinerarioRepository:
    def buscar_empresas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nome FROM common.empresas WHERE is_ativo = TRUE ORDER BY nome;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar empresas: {e}")
            return []

    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas WHERE is_ativo = TRUE ORDER BY codigo;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar linhas: {e}")
            return []

    def obter_proximo_numero_os(self, pasta_destino):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM itinerario.ordens_servico WHERE ano = EXTRACT(YEAR FROM CURRENT_DATE)")
                    resultado = cur.fetchone()
                    return resultado[0] if resultado else 1
        except Exception as e:
            print(f"Erro ao buscar próximo número da OS: {e}")
            return 1

    def salvar_os_itinerario(self, dados_db):
        # MODIFICAÇÃO: A coluna KM agora recebe o valor cru sem forçar a conversão (::NUMERIC), permitindo texto livre!
        query_os = """
            INSERT INTO itinerario.ordens_servico (
                numero, ano, origem_id, tipo_evento_id, processo_adm, endereco,
                horario_inicio, horario_fim, evento, nome_corrida, tipo_obra,
                km, caminho_arquivo, responsavel_id, data_emissao
            ) VALUES (
                %(num_os)s, %(ano)s, 
                (SELECT id FROM common.origens WHERE nome ILIKE %(origem)s LIMIT 1),
                (SELECT id FROM common.tipos WHERE contexto = 'TIPO_EVENTO_OS' AND nome ILIKE %(tipo)s LIMIT 1),
                %(processo)s, %(endereco)s,
                NULLIF(%(horario_inicio)s, '')::TIME, NULLIF(%(horario_final)s, '')::TIME, 
                %(evento)s, %(nome_corrida)s, %(tipo_obra)s,
                NULLIF(%(km)s, ''), %(docx_path)s, 
                (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %(criado_por)s LIMIT 1),
                NOW()
            ) RETURNING id;
        """

        query_empresas = """
            INSERT INTO itinerario.os_empresas (os_id, empresa_id)
            SELECT %(os_id)s, id FROM common.empresas WHERE nome ILIKE %(empresa_nome)s LIMIT 1;
        """

        # A query vai juntar o código e o nome com o traço no meio apenas para visualização
        query_linhas = """
            SELECT 
                codigo || ' - ' || nome AS linha_formatada
            FROM common.linhas 
            WHERE is_ativo = TRUE 
            ORDER BY codigo;
        """

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query_os, dados_db)
                    os_id = cur.fetchone()[0]

                    for emp in dados_db.get("empresas_lista", []):
                        cur.execute(query_empresas, {"os_id": os_id, "empresa_nome": emp})

                    for cod in dados_db.get("codigos_linhas", []):
                        cur.execute(query_linhas, {"os_id": os_id, "codigo_linha": cod})

                    conn.commit()
            return True, "Ordem de Serviço salva no banco com sucesso."
        except psycopg2.IntegrityError as e:
            return False, f"Erro de Integridade: Verifique se a Origem ou Tipo estão cadastrados. {e}"
        except Exception as e:
            return False, f"Erro crítico ao salvar no banco: {e}"