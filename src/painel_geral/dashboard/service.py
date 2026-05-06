import pandas as pd
from src.painel_geral.dashboard.repository import DashboardGeralRepository

class DashboardGeralService:
    def __init__(self):
        self.repo = DashboardGeralRepository()

    def carregar_dados_brutos(self):
        df_os = self.repo.buscar_dados_os_global()
        df_par = self.repo.buscar_dados_pareceres_global()
        df_pesq = self.repo.buscar_dados_pesquisas_global()

        if not df_os.empty: df_os['data_dt'] = pd.to_datetime(df_os['data_dt'], errors='coerce')
        if not df_par.empty: df_par['data_dt'] = pd.to_datetime(df_par['data_dt'], errors='coerce')
        if not df_pesq.empty: df_pesq['data_dt'] = pd.to_datetime(df_pesq['data_dt'], errors='coerce')

        return df_os, df_par, df_pesq

    def filtrar_dados(self, df_os, df_par, df_pesq, data_inicio, data_fim):
        # Converte as strings/dates do Tkinter para o tipo datetime do Pandas (incluindo até o último segundo do dia)
        dt_ini = pd.to_datetime(data_inicio)
        dt_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        df_os_f = df_os[(df_os['data_dt'] >= dt_ini) & (df_os['data_dt'] <= dt_fim)] if not df_os.empty else df_os
        df_par_f = df_par[(df_par['data_dt'] >= dt_ini) & (df_par['data_dt'] <= dt_fim)] if not df_par.empty else df_par
        df_pesq_f = df_pesq[(df_pesq['data_dt'] >= dt_ini) & (df_pesq['data_dt'] <= dt_fim)] if not df_pesq.empty else df_pesq

        return df_os_f, df_par_f, df_pesq_f

    def calcular_kpis(self, df_os_f, df_par_f, df_pesq_f):
        c_os = len(df_os_f)
        c_par = len(df_par_f)
        c_pesq = len(df_pesq_f)
        c_total = c_os + c_par + c_pesq

        s_os = df_os_f['criado_por'].value_counts() if not df_os_f.empty else pd.Series(dtype=int)
        s_par = df_par_f['criado_por'].value_counts() if not df_par_f.empty else pd.Series(dtype=int)
        s_pesq = df_pesq_f['criado_por'].value_counts() if not df_pesq_f.empty else pd.Series(dtype=int)
        
        prod_total = s_os.add(s_par, fill_value=0).add(s_pesq, fill_value=0).sort_values(ascending=False)
        campeao = prod_total.index[0] if not prod_total.empty else "Nenhum"

        return c_total, c_os, c_par, c_pesq, campeao