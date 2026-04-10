import pandas as pd
import warnings
from config.database import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning)

class DashboardQuadroHorarioRepository:
    def buscar_dados_pareceres(self):
        query = """
            SELECT b.tipo_parecer AS tipo,
                   p.solicitante,
                   p.assunto,
                   p.evento,
                   p.linhas_afetadas,
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
            print(f"Erro Pareceres SPR: {e}")
            return pd.DataFrame()

    def buscar_dados_pesquisas(self):
        query = """
            SELECT titulo AS linha,
                   tipo_pesquisa AS tipo,
                   criado_por,
                   created_at AS data_dt
            FROM spr.pesquisas
            WHERE created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro Pesquisas SPR: {e}")
            return pd.DataFrame()