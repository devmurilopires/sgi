import pandas as pd
import warnings
from config.database import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning)

class DashboardGeralRepository:
    def buscar_dados_os_global(self):
        # Correção: O Ponto de Parada usa 'origem_demanda', mas o Itinerário usa apenas 'origem'
        query = """
            SELECT 'Ponto de Parada' AS modulo, data_criacao AS data_dt, responsavel AS criado_por, NULL AS solicitante, origem_demanda AS origem
            FROM ponto_parada.ordens_servico WHERE data_criacao IS NOT NULL
            UNION ALL
            SELECT 'Itinerário' AS modulo, data_criacao AS data_dt, responsavel AS criado_por, NULL AS solicitante, origem AS origem
            FROM itinerario.ordens_servico WHERE data_criacao IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro OS Global: {e}")
            return pd.DataFrame(columns=['modulo', 'data_dt', 'criado_por', 'solicitante', 'origem'])

    def buscar_dados_pareceres_global(self):
        # Correção: Respeitando o nome exato da coluna (origem_demanda vs origem) em cada JOIN
        query = """
            SELECT 'Ponto de Parada' AS modulo, b.tipo_parecer AS decisao, u.nome_completo AS criado_por, b.created_at AS data_dt, p.solicitante, p.origem_demanda AS origem
            FROM common.pareceres_base b JOIN ponto_parada.pareceres p ON b.id = p.id LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            UNION ALL
            SELECT 'Itinerário' AS modulo, b.tipo_parecer AS decisao, u.nome_completo AS criado_por, b.created_at AS data_dt, p.solicitante, p.origem AS origem
            FROM common.pareceres_base b JOIN itinerario.pareceres p ON b.id = p.id LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            UNION ALL
            SELECT 'Quadro de Horário' AS modulo, b.tipo_parecer AS decisao, u.nome_completo AS criado_por, b.created_at AS data_dt, p.solicitante, p.origem AS origem
            FROM common.pareceres_base b JOIN quadro_horario.pareceres p ON b.id = p.id LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro Pareceres Global: {e}")
            return pd.DataFrame(columns=['modulo', 'decisao', 'criado_por', 'data_dt', 'solicitante', 'origem'])

    def buscar_dados_pesquisas_global(self):
        query = """
            SELECT 'Quadro de Horário' AS modulo, tipo_pesquisa, criado_por, created_at AS data_dt, 'Interno' AS solicitante, 'SISGEP' AS origem
            FROM quadro_horario.pesquisas
            WHERE created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"Erro Pesquisas Global: {e}")
            return pd.DataFrame(columns=['modulo', 'tipo_pesquisa', 'criado_por', 'data_dt', 'solicitante', 'origem'])