from config.database import get_db_connection

class ParecerQuadroHorarioRepository:
    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas ORDER BY codigo;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar linhas: {e}")
            return []
        

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

    def obter_proximo_numero_parecer(self, tipo):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(MAX(numero_parecer_ano), 0) + 1 
                        FROM common.pareceres_base 
                        WHERE tipo_parecer = %s AND sistema_origem = 'quadro_horario' 
                        AND ano = EXTRACT(YEAR FROM CURRENT_DATE)
                    """, (tipo,))
                    resultado = cur.fetchone()
                    return resultado[0] if resultado else 1
        except Exception as e:
            return 1

    def salvar_parecer_no_banco(self, dados_db):
        query_base = """
            INSERT INTO common.pareceres_base (numero_parecer_ano, tipo_parecer, sistema_origem, ano, criado_por_id)
            VALUES (%(numero_parecer)s, %(tipo)s, 'quadro_horario', EXTRACT(YEAR FROM CURRENT_DATE), 
            (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %(criado_por)s LIMIT 1))
            RETURNING id;
        """
        # NOVO: 'origem' adicionada ao final da query específica
        query_especifica = """
            INSERT INTO quadro_horario.pareceres (
                id, processo, assunto, evento, data_evento, 
                solicitante, linhas_afetadas, motivo_indeferimento, caminho_arquivo, origem
            ) VALUES (
                %(id_base)s, %(processo)s, %(assunto)s, %(evento)s, %(data_evento)s,
                %(solicitante)s, %(linhas)s, %(motivo)s, %(caminho_arquivo)s, %(origem)s
            );
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query_base, dados_db)
                    id_base = cur.fetchone()[0]
                    dados_db["id_base"] = id_base
                    
                    cur.execute(query_especifica, dados_db)
                    conn.commit()
                    return True
        except Exception as e:
            print(f"Erro detalhado DB: {e}")
            return False