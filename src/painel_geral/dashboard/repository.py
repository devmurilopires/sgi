import pandas as pd
import warnings
from config.database import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning)

class DashboardGeralRepository:
    def buscar_dados_os_global(self):
        query = """
            SELECT 'Ponto de Parada' AS modulo, data_criacao AS data_dt, responsavel AS criado_por
            FROM sigp.ordens_servico WHERE data_criacao IS NOT NULL
            UNION ALL
            SELECT 'Itinerário' AS modulo, data_criacao AS data_dt, responsavel AS criado_por
            FROM siga.ordens_servico WHERE data_criacao IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro OS Global: {e}")
            return pd.DataFrame()

    def buscar_dados_pareceres_global(self):
        query = """
            SELECT b.sistema_origem AS modulo,
                   b.tipo_parecer AS decisao,
                   u.nome_completo AS criado_por,
                   b.created_at AS data_dt
            FROM common.pareceres_base b
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            WHERE b.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro Pareceres Global: {e}")
            return pd.DataFrame()

    def buscar_dados_pesquisas_global(self):
        query = """
            SELECT 'Quadro de Horário' AS modulo,
                   tipo_pesquisa,
                   criado_por,
                   created_at AS data_dt
            FROM spr.pesquisas
            WHERE created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro Pesquisas Global: {e}")
            return pd.DataFrame()