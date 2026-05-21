import psycopg2
from config.database import get_db_connection

class ParecerItinerarioRepository:
    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT codigo || ' - ' || nome FROM common.linhas WHERE is_ativo = TRUE ORDER BY codigo;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e: 
            print(f"Erro ao buscar linhas formatadas: {e}")
            return []

    def obter_proximo_numero_parecer(self, tipo):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COALESCE(MAX(numero_parecer_ano), 0) + 1 
                        FROM common.pareceres_base 
                        WHERE sistema_origem = 'Itinerário' 
                        AND ano = EXTRACT(YEAR FROM CURRENT_DATE)
                    """)
                    resultado = cur.fetchone()
                    return resultado[0] if resultado else 1
        except Exception as e: 
            print(f"Erro ao gerar numeração: {e}")
            return 1

    def salvar_parecer_no_banco(self, dados_db):
        query_base = """
            INSERT INTO common.pareceres_base (
                numero_parecer_ano, ano, tipo_id, sistema_origem, caminho_arquivo, criado_por_id
            ) VALUES (
                %(numero_parecer)s, EXTRACT(YEAR FROM CURRENT_DATE), 
                (SELECT id FROM common.tipos WHERE contexto = 'DECISAO_PARECER' AND nome ILIKE %(tipo)s LIMIT 1),
                'Itinerário', %(caminho_arquivo)s,
                (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %(criado_por)s LIMIT 1)
            ) RETURNING id;
        """
        
        query_especifica = """
            INSERT INTO itinerario.pareceres (
                id, origem_id, processo, assunto, evento, data_evento, periodo, 
                endereco, solicitante, motivo_indeferimento
            ) VALUES (
                %(id_base)s, 
                (SELECT id FROM common.origens WHERE nome ILIKE %(origem)s LIMIT 1),
                %(processo)s, %(assunto)s, %(evento)s, %(data_db)s, %(periodo)s,
                %(endereco)s, %(solicitante)s, %(motivo)s
            );
        """

        # 3. MODIFICAÇÃO: Relacionamento N:M para as linhas afetadas
        query_linha = """
            INSERT INTO itinerario.pareceres_linhas (parecer_id, linha_id)
            SELECT %(id_base)s, id FROM common.linhas WHERE codigo = %(codigo)s LIMIT 1;
        """

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query_base, dados_db)
                    id_base = cur.fetchone()[0]
                    dados_db["id_base"] = id_base
                    
                    cur.execute(query_especifica, dados_db)

                    # Inserir as linhas afetadas na tabela de relacionamento
                    for codigo in dados_db.get("codigos_linhas", []):
                        cur.execute(query_linha, {"id_base": id_base, "codigo": codigo})

                    conn.commit()
            return True, "Registro salvo no banco com sucesso."
        except psycopg2.IntegrityError as e:
            return False, f"Erro de integridade relacional. Verifique os cadastros base: {e}"
        except Exception as e:
            return False, f"Erro ao salvar no banco: {e}"