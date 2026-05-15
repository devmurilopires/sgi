import pandas as pd
import warnings
from config.database import get_db_connection

# Ignora avisos internos do Pandas
warnings.filterwarnings('ignore', category=UserWarning)

class DashboardRepository:
    def buscar_dados_os(self):
        # MODIFICAÇÃO: 
        # 1. Múltiplos JOINs para resolver as chaves estrangeiras (Tipos, Origens, Usuários)
        # 2. JOIN com enderecos_cadastrados para resgatar o Bairro
        query = """
            SELECT ta.nome AS tipo_os, 
                   ti.nome AS tipo_item, 
                   os.status_conclusao, 
                   e.bairro, 
                   os.data_criacao AS data_dt, 
                   u.nome_completo AS criado_por,
                   o.nome AS origem
            FROM ponto_parada.ordens_servico os
            LEFT JOIN common.tipos ta ON os.tipo_acao_id = ta.id
            LEFT JOIN common.tipos ti ON os.tipo_item_id = ti.id
            LEFT JOIN ponto_parada.enderecos_cadastrados e ON os.ponto_principal_id = e.id
            LEFT JOIN common.usuarios u ON os.responsavel_id = u.id
            LEFT JOIN common.origens o ON os.origem_id = o.id
            WHERE os.data_criacao IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Erro ao buscar OS pro Dashboard: {e}")
            # Retorna um DataFrame vazio com a estrutura correta para evitar crash na View
            return pd.DataFrame(columns=['tipo_os', 'tipo_item', 'status_conclusao', 'bairro', 'data_dt', 'criado_por', 'origem'])

    def buscar_dados_pareceres(self):
        # MODIFICAÇÃO: 
        # 1. 'tipo' resolvido via JOIN com common.tipos através da tabela base
        # 2. 'origem' resolvida via JOIN com common.origens
        query = """
            SELECT t.nome AS tipo, 
                   u.nome_completo AS criado_por, 
                   b.created_at AS data_dt, 
                   p.solicitante,
                   o.nome AS origem
            FROM ponto_parada.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.tipos t ON b.tipo_id = t.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            LEFT JOIN common.origens o ON p.origem_id = o.id
            WHERE b.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            print(f"Erro ao buscar Pareceres pro Dashboard: {e}")
            return pd.DataFrame(columns=['tipo', 'criado_por', 'data_dt', 'solicitante', 'origem'])