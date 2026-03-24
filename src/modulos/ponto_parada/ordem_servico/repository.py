import psycopg2
from config.database import get_db_connection
from datetime import datetime

class OSRepository:
    
    def buscar_endereco_por_id(self, id_procurado):
        # BUSCA DE ENDEREÇO CADASTRADO PELO ID DO PONTO
        query = """
            SELECT logradouro, bairro, numero, complemento, is_ativo
            FROM sigp.enderecos_cadastrados 
            WHERE id_ponto = %s
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
        # CADASTRO DE NOVO ENDEREÇO PARA UM PONTO (COM RESPONSÁVEL E DATA DE VISTORIA)
        query = """
            INSERT INTO sigp.enderecos_cadastrados 
            (id_ponto, logradouro, numero, bairro, complemento, is_ativo, responsavel_vistoria, data_vistoria)
            VALUES (%s, %s, %s, %s, %s, TRUE, %s, %s)
        """
        data_atual = datetime.now() 
        params = (id_texto, endereco, numero, bairro, complemento, usuario, data_atual)
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
        
        # ATUALIZAÇÃO DE ENDEREÇO EXISTENTE (COM OPÇÃO DE REATIVAÇÃO)
        query = f"""
            UPDATE sigp.enderecos_cadastrados
            SET logradouro=%s, numero=%s, bairro=%s, complemento=%s, {set_ativo}
                responsavel_vistoria=%s, data_vistoria=%s
            WHERE id_ponto=%s
        """
        
        data_atual = datetime.now()
        params = (endereco, numero, bairro, complemento, usuario, data_atual, id_texto)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"[LOG DB] Erro ao atualizar endereço: {e}")
            raise Exception("Falha ao atualizar o endereço no banco.")

    def buscar_historico_os(self, id_procurado, limite=5):
        # BUSCA DO HISTÓRICO DE ORDEM DE SERVIÇO PARA UM PONTO (COM LIMITAÇÃO DE REGISTROS)
        query = """
            SELECT numero, TO_CHAR(data_criacao, 'DD/MM/YYYY'), acao_realizada, tipo_item, logradouro_completo, bairro, responsavel
            FROM sigp.ordens_servico
            WHERE ponto_principal_id = %s
            ORDER BY data_criacao DESC
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

    def obter_proximo_numero_os(self, pasta_final, ano_atual):
        # GERAÇÃO DO PRÓXIMO NÚMERO DE ORDEM DE SERVIÇO PARA O MODELO SELECIONADO NO ANO ATUAL
        query = """
            SELECT MAX(numero)
            FROM sigp.ordens_servico
            WHERE modelo_documento = %s AND EXTRACT(YEAR FROM data_criacao) = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (pasta_final, int(ano_atual)))
                    resultado = cursor.fetchone()
                    if resultado and resultado[0] is not None:
                        return resultado[0] + 1
                    return 1
        except Exception as e:
            print(f"[LOG DB] Erro ao gerar numeração da OS: {e}")
            return 1

    def salvar_os(self, dados_os):
        # SALVA A ORDEM DE SERVIÇO NO BANCO DE DADOS (COM A ORIGEM DA DEMANDA)
        (numero_os, data_str, id_principal, ids_formatado,
         tipo_os, _lixo1, tipo_item, _lixo2,
         endereco_completo, bairro_str, _lixo3,
         complemento_str, descricoes, usuario_logado, pasta_escolhida, origem_demanda) = dados_os

        data_criacao = datetime.strptime(data_str, "%d/%m/%Y").date()
        query = """
            INSERT INTO sigp.ordens_servico (
                numero, data_criacao, ponto_principal_id, pontos_adicionais,
                acao_realizada, tipo_item, logradouro_completo, bairro,
                complemento, descricao_tecnica, responsavel, modelo_documento, origem_demanda
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            numero_os, data_criacao, id_principal, ids_formatado,
            tipo_os, tipo_item, endereco_completo, bairro_str,
            complemento_str, descricoes, usuario_logado, pasta_escolhida, origem_demanda
        )

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"[LOG DB] Erro ao salvar OS final: {e}")
            raise Exception("Falha ao registrar a Ordem de Serviço no banco de dados.")