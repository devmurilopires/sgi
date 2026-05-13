import pandas as pd
from config.database import get_db_connection

class DashboardPMRepository:
    def buscar_dados_pareceres(self):
        # MODIFICAÇÃO CHAVE: 
        # 1. Removido pb.tipo_parecer
        # 2. Adicionado LEFT JOIN com common.tipos (alias t)
        # 3. Adicionado t.nome AS decisao
        query = """
            SELECT 
                p.id,
                t.nome AS decisao,
                p.solicitante,
                p.assunto,
                pb.created_at as data_dt
            FROM projetos_mobilidade.pareceres p
            JOIN common.pareceres_base pb ON p.id = pb.id
            LEFT JOIN common.tipos t ON pb.tipo_id = t.id
            WHERE pb.created_at IS NOT NULL
        """
        try:
            with get_db_connection() as conn:
                return pd.read_sql(query, conn)
        except Exception as e:
            print(f"[LOG DB] Erro Dashboard PM: {e}")
            # Mantemos a estrutura exata das colunas no DataFrame vazio para evitar quebra no view.py
            return pd.DataFrame(columns=['id', 'decisao', 'solicitante', 'assunto', 'data_dt'])