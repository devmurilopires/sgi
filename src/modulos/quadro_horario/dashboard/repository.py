import pandas as pd
import warnings
from config.database import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning)

class DashboardQuadroHorarioRepository:
    def buscar_dados_pareceres(self):
        query = """
            SELECT b.tipo_parecer AS decisao, 
                   p.assunto, 
                   p.solicitante, 
                   u.nome_completo AS criado_por, 
                   b.created_at AS data_dt
            FROM spr.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            WHERE b.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro ao buscar Pareceres pro Dashboard SPR: {e}")
            return pd.DataFrame()

    def buscar_dados_pesquisas(self):
        query = """
            SELECT tipo_pesquisa, 
                   criado_por, 
                   created_at AS data_dt
            FROM spr.pesquisas
            WHERE created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro ao buscar Pesquisas pro Dashboard SPR: {e}")
            return pd.DataFrame()