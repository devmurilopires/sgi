import pandas as pd
from config.database import get_db_connection

class EnderecoRepository:
    def salvar_ou_atualizar(self, id_ponto, endereco, numero, bairro, complemento, status, criado_por):
        # Converte o status que vem da tela para o formato Booleano do novo banco
        if isinstance(status, str):
            is_ativo = status.strip().upper() == "ATIVO"
        else:
            is_ativo = bool(status)

        query = """
            INSERT INTO sigp.enderecos_cadastrados 
            (id_ponto, logradouro, numero, bairro, complemento, is_ativo, responsavel_vistoria, data_vistoria)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (id_ponto) DO UPDATE SET
                logradouro = EXCLUDED.logradouro,
                numero = EXCLUDED.numero,
                bairro = EXCLUDED.bairro,
                complemento = EXCLUDED.complemento,
                is_ativo = EXCLUDED.is_ativo,
                responsavel_vistoria = EXCLUDED.responsavel_vistoria,
                data_vistoria = CURRENT_TIMESTAMP;
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (id_ponto, endereco, numero, bairro, complemento, is_ativo, criado_por))
                conn.commit()
            return True, "Endereço salvo/atualizado com sucesso!"
        except Exception as e:
            return False, f"Erro no banco de dados: {e}"

    def listar_todos(self):
        # O AS (Alias) garante que o Pandas DataFrame continue entregando os nomes 
        # antigos para a View, sem precisar refazer a tela de Endereços!
        query = """
            SELECT 
                id_ponto, 
                logradouro AS endereco, 
                numero, 
                bairro, 
                complemento, 
                CASE WHEN is_ativo THEN 'ATIVO' ELSE 'INATIVO' END AS status, 
                responsavel_vistoria AS criado_por, 
                data_vistoria AS updated_at
            FROM sigp.enderecos_cadastrados
            ORDER BY id_ponto
        """
        try:
            with get_db_connection() as conn:
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Erro ao listar endereços: {e}")
            return pd.DataFrame()