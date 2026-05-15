import pandas as pd
from config.database import get_db_connection

class EnderecoRepository:
    def salvar_ou_atualizar(self, id_ponto, endereco, numero, bairro, complemento, status, criado_por):
        # Converte o status que vem da tela para o formato Booleano do novo banco
        if isinstance(status, str):
            is_ativo = status.strip().upper() == "ATIVO"
        else:
            is_ativo = bool(status)

        # MODIFICAÇÃO: 
        # 1. 'id_ponto' virou 'id'
        # 2. 'responsavel_vistoria' virou FK (resolvida via subquery com o ILIKE)
        query = """
            INSERT INTO ponto_parada.enderecos_cadastrados 
            (id, logradouro, numero, bairro, complemento, is_ativo, responsavel_vistoria_id, data_vistoria)
            VALUES (%s, %s, %s, %s, %s, %s, (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %s LIMIT 1), CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                logradouro = EXCLUDED.logradouro,
                numero = EXCLUDED.numero,
                bairro = EXCLUDED.bairro,
                complemento = EXCLUDED.complemento,
                is_ativo = EXCLUDED.is_ativo,
                responsavel_vistoria_id = EXCLUDED.responsavel_vistoria_id,
                data_vistoria = CURRENT_TIMESTAMP;
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # Adicionamos % % ao redor do nome do criador para o ILIKE funcionar bem
                cursor.execute(query, (id_ponto, endereco, numero, bairro, complemento, is_ativo, f"%{criado_por}%"))
                conn.commit()
            return True, "Endereço salvo/atualizado com sucesso!"
        except Exception as e:
            return False, f"Erro no banco de dados: {e}"

    def listar_todos(self):
        # MODIFICAÇÃO: 
        # 1. Aliases mantidos (id AS id_ponto, etc.) para NÃO quebrar a View
        # 2. LEFT JOIN com common.usuarios para buscar o nome do responsável
        query = """
            SELECT 
                e.id AS id_ponto, 
                e.logradouro AS endereco, 
                e.numero, 
                e.bairro, 
                e.complemento, 
                CASE WHEN e.is_ativo THEN 'ATIVO' ELSE 'INATIVO' END AS status, 
                u.nome_completo AS criado_por, 
                e.data_vistoria AS updated_at
            FROM ponto_parada.enderecos_cadastrados e
            LEFT JOIN common.usuarios u ON e.responsavel_vistoria_id = u.id
            ORDER BY e.id
        """
        try:
            with get_db_connection() as conn:
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Erro ao listar endereços: {e}")
            return pd.DataFrame()