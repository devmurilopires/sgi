import psycopg2
from config.database import get_db_connection
from datetime import datetime

class ParecerProjetosMobilidadeRepository:
    
    def salvar_parecer(self, tipo_parecer, processo, assunto, solicitante, motivo_indeferimento, usuario_id):
        # Captura o ano atual para compor a numeração
        ano_atual = datetime.now().year
        
        # Define o contexto que você cadastrou na sua tabela common.tipos
        # Ex: Se você cadastrou "DEFERIDO" com o contexto "DECISAO_PARECER"
        contexto_tipo = 'DECISAO_PARECER' 
        
        # 1. Inserção na Tabela Base (Usando CTE - Common Table Expressions)
        # O 'WITH seq' busca o último número daquele ano e módulo, e soma 1.
        # O sub-select do 'tipo_id' converte a string (ex: 'DEFERIDO') no ID correto.
        query_base = """
            WITH seq AS (
                SELECT COALESCE(MAX(numero_parecer_ano), 0) + 1 AS proximo_numero
                FROM common.pareceres_base
                WHERE ano = %s AND sistema_origem = 'Projetos de Mobilidade'
            )
            INSERT INTO common.pareceres_base (
                numero_parecer_ano, 
                ano, 
                tipo_id, 
                sistema_origem, 
                criado_por_id
            )
            VALUES (
                (SELECT proximo_numero FROM seq),
                %s,
                (SELECT id FROM common.tipos WHERE contexto = %s AND nome = %s LIMIT 1),
                'Projetos de Mobilidade',
                %s
            )
            RETURNING id, numero_parecer_ano
        """
        
        # 2. Inserção na Tabela Específica do Módulo
        # NOTA: Removido o 'motivo_indeferimento' pois a coluna não existe no novo DDL
        query_filha = """
            INSERT INTO projetos_mobilidade.pareceres (id, processo, assunto, solicitante)
            VALUES (%s, %s, %s, %s)
        """
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Passo 1: Executar query base
                    # Passamos os parâmetros na ordem que os %s aparecem no SQL
                    cursor.execute(query_base, (
                        ano_atual,        # Para a subquery de sequência
                        ano_atual,        # Para o campo 'ano'
                        contexto_tipo,    # Para buscar o ID do tipo (contexto)
                        tipo_parecer,     # Para buscar o ID do tipo (nome: 'DEFERIDO'/'INDEFERIDO')
                        usuario_id        # Para o criador
                    ))
                    
                    resultado_base = cursor.fetchone()
                    
                    # Se o tipo_parecer não estiver cadastrado na tabela common.tipos, o INSERT falha
                    if not resultado_base:
                        raise Exception("Falha de integridade: Tipo de Parecer não cadastrado em common.tipos ou erro ao gerar numeração.")
                        
                    id_gerado, numero_parecer_ano = resultado_base
                    
                    # Passo 2: Inserir na tabela filha usando o ID herdado
                    cursor.execute(query_filha, (id_gerado, processo, assunto, solicitante))
                    
                    # Passo 3: Confirma a transação
                    conn.commit()
                    
                    # Retornamos o número formatado com o ano para o Service usar no Word
                    numero_formatado = f"{numero_parecer_ano}/{ano_atual}"
                    return True, (id_gerado, numero_formatado)
                    
        except psycopg2.IntegrityError as e:
            print(f"[LOG DB] Erro de Integridade Relacional: {e}")
            return False, "Erro de integridade no banco. Verifique se os dados relacionados existem."
        except Exception as e:
            print(f"[LOG DB] Erro crítico ao salvar Parecer: {e}")
            return False, str(e)