import psycopg2
from config.database import get_db_connection

class ParecerRepository:
    
    def obter_proximo_numero(self, ano):
        """Calcula o próximo número do parecer para o SIGP no ano atual consultando a Tabela Mãe."""
        query = "SELECT MAX(numero_parecer_ano) FROM common.pareceres_base WHERE ano = %s AND sistema_origem = 'SIGP'"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (ano,))
                    resultado = cursor.fetchone()
                    if resultado and resultado[0] is not None:
                        return resultado[0] + 1
                    return 1
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar número do parecer: {e}")
            raise Exception("Falha ao calcular a numeração do parecer.")

    def salvar_parecer(self, dados_banco):
        """
        Salva na Tabela Mãe (common.pareceres_base) e na Tabela Filha (sigp.pareceres) 
        em uma única transação segura (Duplo Insert).
        """
        
        # Desempacota os dados exatos que o seu Service manda
        (numero, ano, data_criacao, tipo_parecer, processo, 
         assunto, ids_joined, tipo_exec, item, endereco, 
         solicitante, motivo, quantidade, caminho_arquivo, usuario_logado, origem_demanda) = dados_banco

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Pega o ID numérico do usuário baseado no nome
                    cursor.execute("SELECT id FROM common.usuarios WHERE nome_completo = %s OR username = %s LIMIT 1", (usuario_logado, usuario_logado))
                    user_row = cursor.fetchone()
                    usuario_id = user_row[0] if user_row else None

                    # INSERE NA TABELA MÃE e pega o ID gerado usando 'RETURNING id'
                    query_mae = """
                        INSERT INTO common.pareceres_base 
                        (sistema_origem, numero_parecer_ano, ano, criado_por_id) 
                        VALUES ('SIGP', %s, %s, %s)
                        RETURNING id;
                    """
                    cursor.execute(query_mae, (numero, ano, usuario_id))
                    id_mae = cursor.fetchone()[0]

                    # INSERE NA TABELA FILHA usando o ID DA MÃE (AGORA COM A ORIGEM)
                    query_filha = """
                        INSERT INTO sigp.pareceres (
                            id, tipo_parecer, processo, assunto, solicitante, ids_pontos,
                            tipo_execucao, item, endereco_vistoria, motivo_indeferimento,
                            quantidade, caminho_arquivo_docx, origem_demanda
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    params_filha = (
                        id_mae, tipo_parecer, processo, assunto, solicitante, ids_joined,
                        tipo_exec, item, endereco, motivo, quantidade, caminho_arquivo, origem_demanda
                    )
                    
                    cursor.execute(query_filha, params_filha)
                    
                    # Confirma a transação
                    conn.commit()
                    
            return True
            
        except Exception as e:
            print(f"[LOG DB] Erro ao salvar parecer duplo: {e}")
            raise Exception(f"Erro ao registrar o Parecer no Banco de Dados: {e}")