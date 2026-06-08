import psycopg2
from config.database import get_db_connection

class ParecerProjetosMobilidadeRepository:
    def obter_proximo_numero_parecer(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(MAX(numero_parecer_ano), 0) + 1 
                        FROM common.pareceres_base 
                        WHERE ano = EXTRACT(YEAR FROM CURRENT_DATE)
                    """)
                    resultado = cur.fetchone()
                    return resultado[0] if resultado else 1
        except Exception as e:
            return 1

    def salvar_parecer_no_banco(self, dados_db):
        query_base = """
            INSERT INTO common.pareceres_base (
                numero_parecer_ano, ano, tipo_id, sistema_origem, caminho_arquivo, criado_por_id
            ) VALUES (
                %(numero_parecer)s, EXTRACT(YEAR FROM CURRENT_DATE), 
                (SELECT id FROM common.tipos WHERE contexto IN ('PARECER', 'DECISAO_PARECER') AND nome ILIKE %(tipo)s LIMIT 1),
                'Projetos de Mobilidade', %(caminho_arquivo)s,
                (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %(criado_por)s OR username ILIKE %(criado_por)s LIMIT 1)
            ) RETURNING id;
        """
        
        query_especifica = """
            INSERT INTO projetos_mobilidade.pareceres (
                id, origem_id, processo, assunto, solicitante
            ) VALUES (
                %(id_base)s,
                (SELECT id FROM common.origens WHERE nome ILIKE %(origem)s LIMIT 1),
                %(processo)s, %(assunto)s, %(solicitante)s
            );
        """

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query_base, dados_db)
                    dados_db["id_base"] = cur.fetchone()[0]
                    cur.execute(query_especifica, dados_db)
                    conn.commit()
                    return True, "Sucesso"
        except psycopg2.IntegrityError as e:
            return False, "Erro relacional: O banco rejeitou a inserção. Verifique se a Origem e a Decisão estão corretamente cadastradas."
        except Exception as e:
            return False, str(e)