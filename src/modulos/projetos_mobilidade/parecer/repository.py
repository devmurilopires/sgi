import psycopg2
from config.database import get_db_connection
from datetime import datetime

class ParecerProjetosMobilidadeRepository:
    
    def salvar_parecer(self, tipo_parecer, processo, origem, assunto, solicitante, motivo_indeferimento, usuario_id):
        ano_atual = datetime.now().year
        contexto_tipo = 'DECISAO_PARECER' 
        
        # Inserção Base (Sem alterações lógicas, apenas formatação)
        query_base = """
            WITH seq AS (
                SELECT COALESCE(MAX(numero_parecer_ano), 0) + 1 AS proximo_numero
                FROM common.pareceres_base
                WHERE ano = %s AND sistema_origem = 'Projetos de Mobilidade'
            )
            INSERT INTO common.pareceres_base (
                numero_parecer_ano, ano, tipo_id, sistema_origem, criado_por_id
            )
            VALUES (
                (SELECT proximo_numero FROM seq), %s,
                (SELECT id FROM common.tipos WHERE contexto = %s AND nome ILIKE %s LIMIT 1),
                'Projetos de Mobilidade', %s
            )
            RETURNING id, numero_parecer_ano
        """
        
        # MODIFICAÇÃO: Inserindo a Origem via Subquery (Evitando necessidade de saber ID)
        query_filha = """
            INSERT INTO projetos_mobilidade.pareceres (id, processo, assunto, solicitante, origem_id)
            VALUES (%s, %s, %s, %s, (SELECT id FROM common.origens WHERE nome ILIKE %s LIMIT 1))
        """
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    
                    cursor.execute(query_base, (ano_atual, ano_atual, contexto_tipo, tipo_parecer, usuario_id))
                    resultado_base = cursor.fetchone()
                    
                    if not resultado_base:
                        raise Exception("Falha de integridade: Tipo de Parecer não cadastrado em common.tipos ou erro ao gerar numeração.")
                        
                    id_gerado, numero_parecer_ano = resultado_base
                    
                    # Passo 2: Executando Query Filha enviando a Origem Textual
                    cursor.execute(query_filha, (id_gerado, processo, assunto, solicitante, origem))
                    conn.commit()
                    
                    numero_formatado = f"{numero_parecer_ano}/{ano_atual}"
                    return True, (id_gerado, numero_formatado)
                    
        except psycopg2.IntegrityError as e:
            print(f"[LOG DB] Erro de Integridade Relacional: {e}")
            return False, "Erro de integridade no banco. Verifique se os dados relacionados (como Origem) existem no Admin."
        except Exception as e:
            print(f"[LOG DB] Erro crítico ao salvar Parecer: {e}")
            return False, str(e)