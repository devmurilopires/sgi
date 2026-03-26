import pandas as pd
import math
import unicodedata
from datetime import datetime
from numbers import Number
from src.modulos.quadro_horario.pesquisas.repository import PesquisaQuadroHorarioRepository

class PesquisaQuadroHorarioService:
    def __init__(self):
        self.repo = PesquisaQuadroHorarioRepository()

    def buscar_sugestoes_linhas(self):
        return self.repo.buscar_linhas()

    def salvar_dados(self, titulo, tipo, dados, usuario):
        return self.repo.salvar_pesquisa(titulo, tipo, dados, usuario)

    # --- Utilitários Internos ---
    def _normalizar_nome(self, s):
        if not isinstance(s, str): return ""
        s = s.lower().strip()
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
        return s.replace(" ", "")

    def _extrair_nome_sentido(self, trajeto):
        if not isinstance(trajeto, str): return ""
        trajeto = trajeto.upper()
        return trajeto.split("SENTIDO", 1)[1].strip() if "SENTIDO" in trajeto else trajeto.strip()

    def _extrair_hora(self, v):
        if pd.isna(v): return None
        if isinstance(v, (datetime.time, datetime)): return v.hour
        try:
            ts = pd.to_datetime(v, errors='coerce')
            if pd.isna(ts): return int(str(v).strip().split(":")[0]) if ":" in str(v) else None
            return int(ts.hour)
        except: return None

    def _normalizar_tempo(self, v):
        if pd.isna(v): return ""
        if isinstance(v, (datetime.time, datetime)): return v.strftime("%H:%M:%S")
        if isinstance(v, Number):
            fv = float(v)
            sec = int(round(fv * 86400.0)) if abs(fv) <= 1.0 else int(round(fv))
            return f"{sec//3600:02d}:{(sec%3600)//60:02d}:{sec%60:02d}"
        return str(v).strip()

    def _separar_blocos(self, df, col_trajeto):
        blank_mask = df[col_trajeto].isna() | (df[col_trajeto].astype(str).str.strip() == "")
        blank_idxs = df[blank_mask].index.tolist()
        blocks, start = [], 0
        for bi in blank_idxs:
            if not df.iloc[start:bi].empty: blocks.append(df.iloc[start:bi].copy())
            start = bi + 1
        if not df.iloc[start:].empty: blocks.append(df.iloc[start:].copy())
        return blocks

    # --- PROCESSAMENTO: TEMPO DE VIAGEM ---
    def processar_excel_tempo(self, caminho, nomes_sentidos):
        df = pd.read_excel(caminho)
        req = ["Trajeto", "Partida Real", "Tempo Viagem"]
        if not all(c in df.columns for c in req): return False, "Colunas Trajeto, Partida Real, Tempo Viagem não encontradas."
        
        blocos = self._separar_blocos(df[req].copy(), "Trajeto")
        if not blocos: return False, "Nenhum dado válido."

        sentidos = {}
        for i, bloco in enumerate(blocos[:4], start=1):
            bloco["Hora"] = bloco["Partida Real"].apply(self._extrair_hora)
            bloco["TempoStr"] = bloco["Tempo Viagem"].apply(self._normalizar_tempo)
            bloco["TempoMin"] = pd.to_timedelta(bloco["TempoStr"], errors='coerce').dt.total_seconds() / 60.0
            
            bloco = bloco[bloco["Hora"].notna() & bloco["TempoMin"].notna()]
            if bloco.empty: continue

            medias = bloco.groupby("Hora")["TempoMin"].mean()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco["Trajeto"].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"sentido{i}")

            sentidos[col_alvo] = {int(h): math.ceil(float(m)) for h, m in medias.items()}
        return True, sentidos

    def processar_excel_verde(self, caminho, nomes_sentidos):
        df = pd.read_excel(caminho)
        req = ["Trajeto", "Partida Planejada", "TV"]
        if not all(c in df.columns for c in req): return False, "Colunas Trajeto, Partida Planejada, TV ausentes."
        
        blocos = self._separar_blocos(df[req].copy(), "Trajeto")
        sentidos = {}
        for i, bloco in enumerate(blocos[:4], start=1):
            bloco["Hora"] = bloco["Partida Planejada"].apply(self._extrair_hora)
            bloco = bloco[bloco["Hora"].notna() & bloco["TV"].notna()]
            if bloco.empty: continue

            medias = bloco.groupby("Hora")["TV"].mean()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco["Trajeto"].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")

            sentidos[col_alvo] = {int(h): math.ceil(float(m)) for h, m in medias.items()}
        return True, sentidos

    # --- PROCESSAMENTO: DEMANDA ---
    def processar_excel_demanda(self, caminho, nomes_sentidos):
        df = pd.read_excel(caminho)
        col_map = {self._normalizar_nome(c): c for c in df.columns}
        t_col, p_col, pass_col = col_map.get("trajeto"), col_map.get("partida"), col_map.get("passageiro")
        if not (t_col and p_col and pass_col): return False, "Colunas Trajeto, Partida e Passageiro ausentes."
        
        blocos = self._separar_blocos(df, t_col)
        sentidos = {}
        for i, bloco in enumerate(blocos[:4], start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco[pass_col] = pd.to_numeric(bloco[pass_col], errors='coerce')
            bloco = bloco[bloco["Hora"].notna() & bloco[pass_col].notna()]
            if bloco.empty: continue

            somas = bloco.groupby("Hora")[pass_col].sum()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"sentido{i}")
            
            sentidos[col_alvo] = {int(h): int(round(float(s))) for h, s in somas.items()}
        return True, sentidos

    def processar_excel_viagens(self, caminho, nomes_sentidos):
        df = pd.read_excel(caminho)
        col_map = {self._normalizar_nome(c): c for c in df.columns}
        t_col, p_col = col_map.get("trajeto"), col_map.get("partidaplanejada") or col_map.get("partida")
        if not (t_col and p_col): return False, "Colunas Trajeto e Partida ausentes."

        blocos = self._separar_blocos(df, t_col)
        viagens = {}
        for i, bloco in enumerate(blocos[:4], start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco = bloco[bloco["Hora"].notna()]
            if bloco.empty: continue

            contagens = bloco.groupby("Hora").size()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")
            
            viagens[col_alvo] = {int(h): int(c) for h, c in contagens.items()}
        return True, viagens