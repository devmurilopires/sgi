import pandas as pd

from src.modulos.quadro_horario.dashboard.repository import DashboardQuadroHorarioRepository

class DashboardQuadroHorarioService:
    def __init__(self):
        self.repo = DashboardQuadroHorarioRepository()

    def carregar_dados_brutos(self):
        df_par = self.repo.buscar_dados_pareceres()
        df_pesq = self.repo.buscar_dados_pesquisas()

        if not df_par.empty:
            df_par['data_dt'] = pd.to_datetime(df_par['data_dt'], errors='coerce')
        if not df_pesq.empty:
            df_pesq['data_dt'] = pd.to_datetime(df_pesq['data_dt'], errors='coerce')

        return df_par, df_pesq

    def filtrar_dados(self, df_par, df_pesq, ano_sel, mes_sel=None):
        df_par_f = df_par.copy()
        df_pesq_f = df_pesq.copy()

        if not df_par_f.empty:
            df_par_f = df_par_f[df_par_f['data_dt'].dt.year == ano_sel]
        if not df_pesq_f.empty:
            df_pesq_f = df_pesq_f[df_pesq_f['data_dt'].dt.year == ano_sel]

        if mes_sel:
            if not df_par_f.empty:
                df_par_f = df_par_f[df_par_f['data_dt'].dt.month == mes_sel]
            if not df_pesq_f.empty:
                df_pesq_f = df_pesq_f[df_pesq_f['data_dt'].dt.month == mes_sel]

        return df_par_f, df_pesq_f

    def calcular_kpis(self, df_par_f, df_pesq_f):
        count_par = len(df_par_f)
        count_pesq = len(df_pesq_f)
        
        count_def = len(df_par_f[df_par_f['decisao'].astype(str).str.strip().str.upper() == 'DEFERIDO']) if not df_par_f.empty else 0
        count_indef = len(df_par_f[df_par_f['decisao'].astype(str).str.strip().str.upper() == 'INDEFERIDO']) if not df_par_f.empty else 0
            
        return count_par, count_pesq, count_def, count_indef