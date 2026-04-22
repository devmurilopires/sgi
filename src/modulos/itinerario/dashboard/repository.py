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
            FROM itinerario.ordens_servico
            WHERE data_criacao IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro OS Itinerário: {e}")
            return pd.DataFrame()

    def buscar_dados_pareceres(self):
        query = """
            SELECT p.tipo_parecer AS tipo, 
                   u.nome_completo AS criado_por, 
                   b.created_at AS data_dt, 
                   p.solicitante
            FROM itinerario.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            WHERE b.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro Parecer Itinerário: {e}")
            return pd.DataFrame()