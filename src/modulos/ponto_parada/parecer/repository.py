import psycopg2
from config.database import get_db_connection

class ParecerRepository:
    def obter_proximo_numero(self, ano):
        query = "SELECT COALESCE(MAX(numero_parecer_ano), 0) + 1 FROM common.pareceres_base WHERE ano = %s AND sistema_origem = 'Ponto de Parada'"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (ano,))
                    resultado = cursor.fetchone()
                    return resultado[0] if resultado else 1
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar número do parecer: {e}")
            raise Exception("Falha ao calcular a numeração do parecer.")

    def salvar_parecer(self, dados_db):
        # 1. TABELA MÃE: tipo_id e caminho_arquivo realocados para cá
        query_mae = """
            INSERT INTO common.pareceres_base (
                sistema_origem, numero_parecer_ano, ano, tipo_id, caminho_arquivo, criado_por_id
            ) VALUES (
                'Ponto de Parada', %(numero)s, %(ano)s, 
                (SELECT id FROM common.tipos WHERE contexto = 'DECISAO_PARECER' AND nome ILIKE %(tipo_parecer)s LIMIT 1),
                %(caminho_arquivo)s,
                (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %(usuario_logado)s OR username ILIKE %(usuario_logado)s LIMIT 1)
            ) RETURNING id;
        """

        # 2. TABELA FILHA: origem_id e uso exclusivo das colunas do DDL v2.2
        query_filha = """
            INSERT INTO ponto_parada.pareceres (
                id, origem_id, processo, assunto, solicitante, 
                tipo_execucao, item, endereco_vistoria, quantidade, motivo_indeferimento
            ) VALUES (
                %(id_base)s, 
                (SELECT id FROM common.origens WHERE nome ILIKE %(origem)s LIMIT 1),
                %(processo)s, %(assunto)s, %(solicitante)s, 
                %(tipo_exec)s, %(item)s, %(endereco)s, %(quantidade)s, %(motivo)s
            );
        """

        # 3. TABELA DE RELACIONAMENTO (N:M)
        query_pontos = """
            INSERT INTO ponto_parada.pareceres_pontos (parecer_id, ponto_id)
            VALUES (%(id_base)s, %(ponto_id)s);
        """

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Inserção Base e resgate do ID
                    cursor.execute(query_mae, dados_db)
                    id_base = cursor.fetchone()[0]
                    dados_db['id_base'] = id_base
                    
                    # Inserção Filha
                    cursor.execute(query_filha, dados_db)
                    
                    # Loop de Inserção N:M para os pontos
                    for ponto in dados_db.get('ids_list', []):
                        cursor.execute(query_pontos, {"id_base": id_base, "ponto_id": ponto.strip()})
                    
                    conn.commit()
            return True
            
        except psycopg2.IntegrityError as e:
            print(f"[LOG DB] Erro de integridade: {e}")
            raise Exception("Erro relacional: Verifique se os IDs informados, a Origem e o Tipo estão cadastrados no banco.")
        except Exception as e:
            print(f"[LOG DB] Erro ao salvar parecer duplo: {e}")
            raise Exception(f"Erro ao registrar o Parecer no Banco de Dados: {e}")