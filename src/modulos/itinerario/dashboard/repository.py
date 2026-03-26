import pandas as pd
import warnings
from config.database import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning)

class DashboardItinerarioRepository:
    def buscar_dados_os(self):
        query = """
            SELECT tipo_evento AS tipo_os, 
                   data_criacao AS data_dt, 
                   responsavel AS criado_por
            FROM siga.ordens_servico
            WHERE data_criacao IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro OS Dash: {e}")
            return pd.DataFrame()

    def buscar_dados_pareceres(self):
        query = """
            SELECT p.tipo_parecer AS tipo, 
                   u.nome_completo AS criado_por, 
                   b.created_at AS data_dt, 
                   p.solicitante
            FROM siga.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            WHERE b.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro Parecer Dash: {e}")
            return pd.DataFrame()