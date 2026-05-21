import psycopg2
from config.database import get_db_connection

class ParecerQuadroHorarioRepository:
    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas WHERE is_ativo = true ORDER BY codigo;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar linhas: {e}")
            return []
        

    def obter_proximo_numero_parecer(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # ATUALIZADO: Busca focada apenas no ano e sistema de origem
                    cur.execute("""
                        SELECT COALESCE(MAX(numero_parecer_ano), 0) + 1 
                        FROM common.pareceres_base 
                        WHERE sistema_origem = 'Quadro de Horário' 
                        AND ano = EXTRACT(YEAR FROM CURRENT_DATE)
                    """)
                    resultado = cur.fetchone()
                    return resultado[0] if resultado else 1
        except Exception as e:
            return 1

    def salvar_parecer_no_banco(self, dados_db):
        # 1. MODIFICAÇÃO: Inserção na Base blindada com ILIKE
        query_base = """
            INSERT INTO common.pareceres_base (
                numero_parecer_ano, ano, tipo_id, sistema_origem, caminho_arquivo, criado_por_id
            ) VALUES (
                %(numero_parecer)s, EXTRACT(YEAR FROM CURRENT_DATE), 
                (SELECT id FROM common.tipos WHERE contexto = 'DECISAO_PARECER' AND nome ILIKE %(tipo)s LIMIT 1),
                'Quadro de Horário', %(caminho_arquivo)s,
                (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %(criado_por)s LIMIT 1)
            ) RETURNING id;
        """
        
        # 2. MODIFICAÇÃO: Inserção Específica (Origem blindada com ILIKE)
        query_especifica = """
            INSERT INTO quadro_horario.pareceres (
                id, origem_id, processo, assunto, evento, data_evento, solicitante, motivo_indeferimento
            ) VALUES (
                %(id_base)s,
                (SELECT id FROM common.origens WHERE nome ILIKE %(origem)s LIMIT 1),
                %(processo)s, %(assunto)s, %(evento)s, %(data_db)s,
                %(solicitante)s, %(motivo)s
            );
        """

        # 3. MODIFICAÇÃO: Inserção na Tabela de Associação N:M (Código da Linha blindado com ILIKE)
        query_linha = """
            INSERT INTO quadro_horario.pareceres_linhas (parecer_id, linha_id)
            SELECT %(id_base)s, id FROM common.linhas WHERE codigo ILIKE %(codigo)s LIMIT 1;
        """

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Passo 1: Salva base e herda o ID
                    cur.execute(query_base, dados_db)
                    dados_db["id_base"] = cur.fetchone()[0]
                    
                    # Passo 2: Salva os dados específicos
                    cur.execute(query_especifica, dados_db)
                    
                    # Passo 3: Relaciona as linhas afetadas usando os códigos
                    for codigo in dados_db.get("codigos_linhas", []):
                        cur.execute(query_linha, {"id_base": dados_db["id_base"], "codigo": codigo})
                        
                    conn.commit()
                    return True, "Sucesso"
                    
        except psycopg2.IntegrityError as e:
            return False, f"Erro relacional: Verifique se a Origem ({dados_db.get('origem')}) e as Linhas estão cadastradas."
        except Exception as e:
            print(f"[LOG DB] Erro crítico: {e}")
            return False, str(e)