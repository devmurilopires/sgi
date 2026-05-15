import pandas as pd
import warnings
from config.database import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning)

class DashboardGeralRepository:
    def buscar_dados_os_global(self):
        # MODIFICAÇÃO: JOIN com common.usuarios e common.origens. Ajuste para data_emissao no Itinerário.
        query = """
            SELECT 'Ponto de Parada' AS modulo, os.data_criacao AS data_dt, u.nome_completo AS criado_por, NULL AS solicitante, o.nome AS origem
            FROM ponto_parada.ordens_servico os
            LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
            LEFT JOIN common.origens o ON os.origem_id = o.id
            WHERE os.data_criacao IS NOT NULL
            
            UNION ALL
            
            SELECT 'Itinerário' AS modulo, os.data_emissao AS data_dt, u.nome_completo AS criado_por, NULL AS solicitante, o.nome AS origem
            FROM itinerario.ordens_servico os
            LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
            LEFT JOIN common.origens o ON os.origem_id = o.id
            WHERE os.data_emissao IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"[LOG DB] Erro OS Global: {e}")
            return pd.DataFrame(columns=['modulo', 'data_dt', 'criado_por', 'solicitante', 'origem'])

    def buscar_dados_pareceres_global(self):
        # MODIFICAÇÃO: JOIN com common.tipos para pegar a Decisão, e common.origens para a Origem.
        query = """
            SELECT 'Ponto de Parada' AS modulo, t.nome AS decisao, u.nome_completo AS criado_por, b.created_at AS data_dt, p.solicitante, o.nome AS origem
            FROM common.pareceres_base b 
            JOIN ponto_parada.pareceres p ON b.id = p.id 
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            LEFT JOIN common.tipos t ON b.tipo_id = t.id
            LEFT JOIN common.origens o ON p.origem_id = o.id
            
            UNION ALL
            
            SELECT 'Itinerário' AS modulo, t.nome AS decisao, u.nome_completo AS criado_por, b.created_at AS data_dt, p.solicitante, o.nome AS origem
            FROM common.pareceres_base b 
            JOIN itinerario.pareceres p ON b.id = p.id 
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            LEFT JOIN common.tipos t ON b.tipo_id = t.id
            LEFT JOIN common.origens o ON p.origem_id = o.id
            
            UNION ALL
            
            SELECT 'Quadro de Horário' AS modulo, t.nome AS decisao, u.nome_completo AS criado_por, b.created_at AS data_dt, p.solicitante, NULL AS origem
            FROM common.pareceres_base b 
            JOIN quadro_horario.pareceres p ON b.id = p.id 
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            LEFT JOIN common.tipos t ON b.tipo_id = t.id
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"[LOG DB] Erro Pareceres Global: {e}")
            return pd.DataFrame(columns=['modulo', 'decisao', 'criado_por', 'data_dt', 'solicitante', 'origem'])

    def buscar_dados_pesquisas_global(self):
        # MODIFICAÇÃO: JOIN com common.tipos e common.usuarios para resgatar os textos.
        query = """
            SELECT 'Quadro de Horário' AS modulo, t.nome AS tipo_pesquisa, u.nome_completo AS criado_por, p.created_at AS data_dt, 'Interno' AS solicitante, 'SISGEP' AS origem
            FROM quadro_horario.pesquisas p
            LEFT JOIN common.tipos t ON p.tipo_pesquisa_id = t.id
            LEFT JOIN common.usuarios u ON p.criado_por_id = u.id
            WHERE p.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"[LOG DB] Erro Pesquisas Global: {e}")
            return pd.DataFrame(columns=['modulo', 'tipo_pesquisa', 'criado_por', 'data_dt', 'solicitante', 'origem'])