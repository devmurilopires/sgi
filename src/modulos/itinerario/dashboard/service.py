import pandas as pd
import math

class DashboardItinerarioService:
    def __init__(self, repository):
        self.repo = repository

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

        if not df_os_f.empty and 'data_dt' in df_os_f.columns:
            df_os_f = df_os_f[df_os_f['data_dt'].dt.year == ano_sel]
        if not df_par_f.empty and 'data_dt' in df_par_f.columns:
            df_par_f = df_par_f[df_par_f['data_dt'].dt.year == ano_sel]

        if mes_sel:
            if not df_os_f.empty: df_os_f = df_os_f[df_os_f['data_dt'].dt.month == mes_sel]
            if not df_par_f.empty: df_par_f = df_par_f[df_par_f['data_dt'].dt.month == mes_sel]

        return df_os_f, df_par_f

    def calcular_kpis(self, df_os_f, df_par_f):
        c_os = len(df_os_f)
        c_par = len(df_par_f)
        c_def = len(df_par_f[df_par_f['tipo'].astype(str).str.upper() == 'DEFERIDO']) if not df_par_f.empty and 'tipo' in df_par_f.columns else 0
        c_indef = len(df_par_f[df_par_f['tipo'].astype(str).str.upper() == 'INDEFERIDO']) if not df_par_f.empty and 'tipo' in df_par_f.columns else 0
        
        return c_os, c_par, c_def, c_indef

    def preparar_tabela_mensal_pareceres(self, df_par_f):
        meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        tabela = []
        for m_num, m_nome in meses.items():
            if df_par_f.empty or 'data_dt' not in df_par_f.columns:
                tabela.append([m_nome, 0, 0, 0])
                continue
                
            mes_data = df_par_f[df_par_f['data_dt'].dt.month == m_num]
            if not mes_data.empty and 'tipo' in mes_data.columns:
                tipos = mes_data['tipo'].fillna('').astype(str).str.upper()
                deferidos = len(tipos[tipos == 'DEFERIDO'])
                indeferidos = len(tipos[tipos == 'INDEFERIDO'])
            else:
                deferidos, indeferidos = 0, 0
                
            tabela.append([m_nome, deferidos, indeferidos, deferidos + indeferidos])
        return tabela

    def preparar_tabela_mensal_os(self, df_os_f):
        meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        tabela = []
        for m_num, m_nome in meses.items():
            if df_os_f.empty or 'data_dt' not in df_os_f.columns:
                tabela.append([m_nome, 0, 0, 0, 0, 0])
                continue
                
            mes_data = df_os_f[df_os_f['data_dt'].dt.month == m_num]
            if not mes_data.empty and 'tipo_os' in mes_data.columns:
                tipos = mes_data['tipo_os'].fillna('').astype(str).str.upper()
                eventos = len(tipos[tipos.str.contains('EVENTO')])
                corrida = len(tipos[tipos.str.contains('CORRIDA')])
                obras = len(tipos[tipos.str.contains('OBRA')])
                outros = len(mes_data) - (eventos + corrida + obras)
            else:
                eventos, corrida, obras, outros = 0, 0, 0, len(mes_data)
                
            tabela.append([m_nome, eventos, corrida, obras, outros, len(mes_data)])
        return tabela