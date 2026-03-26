import pandas as pd
import unicodedata
from src.modulos.itinerario.dashboard.repository import DashboardItinerarioRepository

class DashboardItinerarioService:
    def __init__(self):
        self.repo = DashboardItinerarioRepository()

    def normalizar(self, texto: str) -> str:
        if not texto or not isinstance(texto, str): return ""
        nfkd = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()

    def carregar_dados_brutos(self):
        df_os = self.repo.buscar_dados_os()
        df_par = self.repo.buscar_dados_pareceres()

        if not df_os.empty:
            df_os['data_dt'] = pd.to_datetime(df_os['data_dt'], errors='coerce')
                
        if not df_par.empty:
            df_par['data_dt'] = pd.to_datetime(df_par['data_dt'], errors='coerce')

        return df_os, df_par

    def filtrar_dados(self, df_os, df_par, ano_sel, mes_sel=None):
        df_os_f = df_os.copy()
        df_par_f = df_par.copy()

        if not df_os_f.empty:
            df_os_f = df_os_f[df_os_f['data_dt'].dt.year == ano_sel]
        if not df_par_f.empty:
            df_par_f = df_par_f[df_par_f['data_dt'].dt.year == ano_sel]

        if mes_sel:
            if not df_os_f.empty:
                df_os_f = df_os_f[df_os_f['data_dt'].dt.month == mes_sel]
            if not df_par_f.empty:
                df_par_f = df_par_f[df_par_f['data_dt'].dt.month == mes_sel]

        return df_os_f, df_par_f

    def calcular_kpis(self, df_os_f, df_par_f):
        count_os = len(df_os_f)
        count_par = len(df_par_f)
        
        count_def = len(df_par_f[df_par_f['tipo'].astype(str).str.strip().str.upper() == 'DEFERIDO']) if not df_par_f.empty else 0
        count_indef = len(df_par_f[df_par_f['tipo'].astype(str).str.strip().str.upper() == 'INDEFERIDO']) if not df_par_f.empty else 0
            
        return count_os, count_par, count_def, count_indef