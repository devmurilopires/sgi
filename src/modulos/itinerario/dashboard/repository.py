import pandas as pd
import warnings
from config.database import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning)

class DashboardItinerarioRepository:
    def buscar_dados_os(self):
        # MODIFICAÇÃO: 
        # 1. data_criacao -> os.data_emissao
        # 2. JOIN com common.tipos para pegar o tipo_evento
        # 3. JOIN com common.usuarios para pegar o responsavel
        query = """
            SELECT t.nome AS tipo_os, 
                   os.data_emissao AS data_dt, 
                   u.nome_completo AS criado_por
            FROM itinerario.ordens_servico os
            LEFT JOIN common.tipos t ON os.tipo_evento_id = t.id
            LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
            WHERE os.data_emissao IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro OS Itinerário: {e}")
            return pd.DataFrame(columns=['tipo_os', 'data_dt', 'criado_por'])

    def buscar_dados_pareceres(self):
        # MODIFICAÇÃO: 
        # 1. 'tipo' agora vem do JOIN com common.tipos através da tabela base (b.tipo_id)
        query = """
            SELECT t.nome AS tipo, 
                   u.nome_completo AS criado_por, 
                   b.created_at AS data_dt, 
                   p.solicitante
            FROM itinerario.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.tipos t ON b.tipo_id = t.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            WHERE b.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro Parecer Itinerário: {e}")
            return pd.DataFrame(columns=['tipo', 'criado_por', 'data_dt', 'solicitante'])