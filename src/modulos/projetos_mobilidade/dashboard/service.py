import pandas as pd
from datetime import datetime

class DashboardPMService:
    def __init__(self, repository):
        self.repo = repository

    def carregar_dados_brutos(self):
        df = self.repo.buscar_dados_pareceres()
        if not df.empty:
            df['data_dt'] = pd.to_datetime(df['data_dt'])
        return df

    def filtrar_dados(self, df, data_ini, data_fim):
        if df.empty: return df
        mask = (df['data_dt'].dt.date >= data_ini) & (df['data_dt'].dt.date <= data_fim)
        return df.loc[mask]

    def calcular_kpis(self, df):
        if df.empty: return 0, 0, 0, "Nenhum"
        total = len(df)
        def_qte = len(df[df['decisao'] == 'DEFERIDO'])
        ind_qte = len(df[df['decisao'] == 'INDEFERIDO'])
        top_solicitante = df['solicitante'].mode()[0] if not df['solicitante'].empty else "Nenhum"
        return total, def_qte, ind_qte, top_solicitante

    def preparar_tabela_mensal(self, df):
        if df.empty: return []
        meses_nomes = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
                       7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
        
        df['mes_num'] = df['data_dt'].dt.month
        resumo = df.groupby(['mes_num', 'decisao']).size().unstack(fill_value=0)
        
        for col in ['DEFERIDO', 'INDEFERIDO']:
            if col not in resumo.columns: resumo[col] = 0
            
        resumo['Total'] = resumo['DEFERIDO'] + resumo['INDEFERIDO']
        lista_final = []
        for mes_idx in range(1, 13):
            nome = meses_nomes[mes_idx]
            if mes_idx in resumo.index:
                row = resumo.loc[mes_idx]
                lista_final.append([nome, int(row['DEFERIDO']), int(row['INDEFERIDO']), int(row['Total'])])
            else:
                lista_final.append([nome, 0, 0, 0])
        return lista_final