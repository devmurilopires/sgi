import psycopg2
from config.database import get_db_connection
from datetime import datetime

class OSRepository:
    
    def buscar_endereco_por_id(self, id_procurado):
        query = """
            SELECT logradouro, bairro, numero, complemento, is_ativo
            FROM ponto_parada.enderecos_cadastrados 
            WHERE id = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_procurado,))
                    resultado = cursor.fetchone()
                    if resultado:
                        return {
                            "endereco": resultado[0],
                            "bairro": resultado[1],
                            "numero": resultado[2],
                            "complemento": resultado[3] or "",
                            "status": "ATIVO" if resultado[4] else "INATIVO"
                        }
            return None
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar endereço: {e}")
            raise Exception("Erro ao buscar endereço no banco de dados.")

    def cadastrar_endereco(self, id_texto, endereco, numero, bairro, complemento, usuario):
        query = """
            INSERT INTO ponto_parada.enderecos_cadastrados 
            (id, logradouro, numero, bairro, complemento, is_ativo, responsavel_vistoria_id, data_vistoria)
            VALUES (%s, %s, %s, %s, %s, TRUE, (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %s LIMIT 1), %s)
        """
        data_atual = datetime.now() 
        params = (id_texto, endereco, numero, bairro, complemento, f"%{usuario}%", data_atual)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"[LOG DB] Erro ao cadastrar endereço: {e}")
            raise Exception("Falha ao salvar o novo endereço no banco.")

    def atualizar_endereco(self, id_texto, endereco, numero, bairro, complemento, usuario, reativar=False):
        set_ativo = "is_ativo = TRUE," if reativar else ""
        query = f"""
            UPDATE ponto_parada.enderecos_cadastrados
            SET logradouro=%s, numero=%s, bairro=%s, complemento=%s, {set_ativo}
                responsavel_vistoria_id=(SELECT id FROM common.usuarios WHERE nome_completo ILIKE %s LIMIT 1), 
                data_vistoria=%s
            WHERE id=%s
        """
        data_atual = datetime.now()
        params = (endereco, numero, bairro, complemento, f"%{usuario}%", data_atual, id_texto)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"[LOG DB] Erro ao atualizar endereço: {e}")
            raise Exception("Falha ao atualizar o endereço no banco.")

    def buscar_historico_os(self, id_procurado, limite=5):
        query = """
            SELECT os.numero, TO_CHAR(os.data_criacao, 'DD/MM/YYYY'), 
                   ta.nome AS acao_realizada, ti.nome AS tipo_item, 
                   e.logradouro, e.bairro, u.nome_completo
            FROM ponto_parada.ordens_servico os
            JOIN ponto_parada.enderecos_cadastrados e ON os.ponto_principal_id = e.id
            LEFT JOIN common.tipos ta ON os.tipo_acao_id = ta.id
            LEFT JOIN common.tipos ti ON os.tipo_item_id = ti.id
            LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
            WHERE os.ponto_principal_id = %s
            ORDER BY os.data_criacao DESC
            LIMIT %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_procurado, limite))
                    return cursor.fetchall()
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar histórico: {e}")
            return []

    def obter_proximo_numero_os(self, ano_atual):
        query = """
            SELECT COALESCE(MAX(numero), 0) + 1
            FROM ponto_parada.ordens_servico
            WHERE EXTRACT(YEAR FROM data_criacao) = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (int(ano_atual),))
                    return cursor.fetchone()[0]
        except Exception as e:
            print(f"[LOG DB] Erro ao gerar numeração da OS: {e}")
            return 1

    # NOVA FUNÇÃO: Busca dinâmica para o Cascading Dropdown
    def buscar_tipos_por_contexto(self, contexto):
        query = "SELECT nome FROM common.tipos WHERE contexto = %s ORDER BY nome"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (contexto,))
                    return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[LOG DB] Erro ao buscar tipos do contexto {contexto}: {e}")
            return []

    def salvar_os(self, dados_db):
        # MODIFICAÇÃO: A subquery do tipo_item_id agora cruza com o contexto para evitar duplicações
        query_os = """
            INSERT INTO ponto_parada.ordens_servico (
                numero, data_criacao, ponto_principal_id, origem_id,
                tipo_acao_id, tipo_item_id, descricao_tecnica, responsavel_id, caminho_arquivo
            ) VALUES (
                %(numero_os)s, %(data_criacao)s, %(id_principal)s,
                (SELECT id FROM common.origens WHERE nome ILIKE %(origem)s LIMIT 1),
                (SELECT id FROM common.tipos WHERE nome ILIKE %(acao)s AND contexto = 'ACAO_OS' LIMIT 1),
                (SELECT id FROM common.tipos WHERE nome ILIKE %(item)s AND contexto = %(item_contexto)s LIMIT 1),
                %(descricao)s,
                (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %(usuario)s LIMIT 1),
                %(caminho)s
            ) RETURNING id;
        """
        
        query_pontos = """
            INSERT INTO ponto_parada.os_pontos_adicionais (os_id, ponto_id)
            VALUES (%(os_id)s, %(ponto_id)s)
        """

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query_os, dados_db)
                    os_id = cursor.fetchone()[0]
                    
                    for pt_id in dados_db.get("pontos_adicionais", []):
                        cursor.execute(query_pontos, {"os_id": os_id, "ponto_id": pt_id})
                        
                    conn.commit()
            return True
        except psycopg2.IntegrityError as e:
            print(f"[LOG DB] Erro de Integridade OS: {e}")
            raise Exception("Verifique se o ID principal, Origem e Tipos estão cadastrados corretamente no sistema.")
        except Exception as e:
            print(f"[LOG DB] Erro Crítico: {e}")
            raise Exception(f"Falha ao registrar a OS no banco: {e}")