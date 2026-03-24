import pandas as pd
import unicodedata
from datetime import datetime
from src.dashboard.repository import DashboardRepository

class DashboardService:
    def __init__(self):
        self.repo = DashboardRepository()

    def normalizar(self, texto: str) -> str:
        """Remove acentos e deixa caixa alta para agrupamento na tabela."""
        if not texto or not isinstance(texto, str): return ""
        nfkd = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()

    def carregar_dados_brutos(self):
        df_os = self.repo.buscar_dados_os()
        df_par = self.repo.buscar_dados_pareceres()

        # Força conversão para o tipo Data e Limpa a Origem
        if not df_os.empty:
            df_os['data_dt'] = pd.to_datetime(df_os['data_dt'], errors='coerce')
            if 'origem' in df_os.columns:
                df_os['origem'] = df_os['origem'].fillna('SPU').astype(str).str.upper().str.strip()
                
        if not df_par.empty:
            df_par['data_dt'] = pd.to_datetime(df_par['data_dt'], errors='coerce')
            if 'origem' in df_par.columns:
                df_par['origem'] = df_par['origem'].fillna('SPU').astype(str).str.upper().str.strip()

        return df_os, df_par

    def filtrar_dados(self, df_os, df_par, ano_sel, mes_sel=None):
        df_os_f = df_os.copy()
        df_par_f = df_par.copy()

        # Filtro Ano
        if not df_os_f.empty:
            df_os_f = df_os_f[df_os_f['data_dt'].dt.year == ano_sel]
        if not df_par_f.empty:
            df_par_f = df_par_f[df_par_f['data_dt'].dt.year == ano_sel]

        # Filtro Mês
        if mes_sel:
            if not df_os_f.empty:
                df_os_f = df_os_f[df_os_f['data_dt'].dt.month == mes_sel]
            if not df_par_f.empty:
                df_par_f = df_par_f[df_par_f['data_dt'].dt.month == mes_sel]

        return df_os_f, df_par_f

    def calcular_kpis(self, df_os_f, df_par_f):
        # Quantidade de OS e Pareceres no período
        count_os = len(df_os_f)
        count_par = len(df_par_f)
        
        if not df_par_f.empty:
            count_def = len(df_par_f[df_par_f['tipo'].astype(str).str.strip().str.upper() == 'DEFERIDO'])
            count_indef = len(df_par_f[df_par_f['tipo'].astype(str).str.strip().str.upper() == 'INDEFERIDO'])
        else:
            count_def = 0
            count_indef = 0
            
        return count_os, count_par, count_def, count_indef