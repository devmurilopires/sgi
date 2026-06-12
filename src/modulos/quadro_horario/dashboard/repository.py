import pandas as pd
import warnings
from config.database import get_db_connection

warnings.filterwarnings('ignore', category=UserWarning)

class DashboardQuadroHorarioRepository:
    def buscar_dados_pareceres(self):
        # MODIFICAÇÃO: Adicionada a junção com common.origens para buscar a coluna 'origem'
        query = """
            SELECT 
                t.nome AS tipo,
                p.solicitante,
                p.assunto,
                p.evento,
                (SELECT string_agg(cl.codigo, ', ') 
                 FROM quadro_horario.pareceres_linhas pl 
                 JOIN common.linhas cl ON pl.linha_id = cl.id 
                 WHERE pl.parecer_id = p.id) AS linhas_afetadas,
                u.nome_completo AS criado_por,
                o.nome AS origem,
                b.created_at AS data_dt
            FROM quadro_horario.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.tipos t ON b.tipo_id = t.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            LEFT JOIN common.origens o ON p.origem_id = o.id
            WHERE b.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"[LOG DB] Erro Pareceres Quadro de Horário: {e}")
            # Atualizado o fallback para incluir a coluna 'origem'
            return pd.DataFrame(columns=['tipo', 'solicitante', 'assunto', 'evento', 'linhas_afetadas', 'criado_por', 'origem', 'data_dt'])

    def buscar_dados_pesquisas(self):
        query = """
            SELECT 
                l.codigo || ' - ' || l.nome AS linha,
                tp.nome AS tipo,
                u.nome_completo AS criado_por,
                p.created_at AS data_dt
            FROM quadro_horario.pesquisas p
            LEFT JOIN common.linhas l ON p.linha_id = l.id
            LEFT JOIN common.tipos tp ON p.tipo_pesquisa_id = tp.id
            LEFT JOIN common.usuarios u ON p.criado_por_id = u.id
            WHERE p.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"[LOG DB] Erro Pesquisas Quadro de Horário: {e}")
            return pd.DataFrame(columns=['linha', 'tipo', 'criado_por', 'data_dt'])