import pandas as pd
import math
import unicodedata
from datetime import datetime, time
from numbers import Number
from src.modulos.quadro_horario.pesquisas.repository import PesquisaQuadroHorarioRepository

class PesquisaQuadroHorarioService:
    def __init__(self):
        self.repo = PesquisaQuadroHorarioRepository()

    def buscar_sugestoes_linhas(self):
        return self.repo.buscar_linhas()

    def salvar_dados(self, linha, tipo, dados_completos, usuario):
        codigo_linha = linha.split(" - ")[0].strip() if " - " in linha else linha.strip()
        
        nome_tipo = "%TEMPO%" if tipo == "tempo" else "%DEMANDA%"

        datas_raw = dados_completos.get("datas", [])
        datas_formatadas = []
        for d in datas_raw:
            try:
                dt_obj = datetime.strptime(d, "%d/%m/%Y").date()
                datas_formatadas.append(dt_obj)
            except Exception:
                pass

        return self.repo.salvar_pesquisa(codigo_linha, nome_tipo, datas_formatadas, dados_completos, usuario)
    
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
        if isinstance(v, (time, datetime)): return v.hour
        try:
            ts = pd.to_datetime(v, errors='coerce')
            if pd.isna(ts): return int(str(v).strip().split(":")[0]) if ":" in str(v) else None
            return int(ts.hour)
        except: return None

    def _normalizar_tempo(self, v):
        if pd.isna(v): return ""
        if isinstance(v, (time, datetime)): return v.strftime("%H:%M:%S")
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

    # --- NOVO: Caçador de Colunas Flexível ---
    def _encontrar_coluna(self, colunas, chaves):
        """Procura o nome real da coluna no Excel a partir de palavras-chave, ignorando maiúsculas e acentos."""
        col_map = {self._normalizar_nome(str(c)): c for c in colunas}
        
        # 1. Tenta encontrar a palavra exata
        for chave in chaves:
            if chave in col_map: return col_map[chave]
            
        # 2. Se não encontrou exato, tenta encontrar parte da palavra (ex: "Partida Real" encontra "partida")
        for chave in chaves:
            for norm_col, orig_col in col_map.items():
                if chave in norm_col:
                    return orig_col
        return None

    # --- PROCESSAMENTO: TEMPO DE VIAGEM ---
    def processar_excel_tempo(self, caminho, nomes_sentidos):
        df = pd.read_excel(caminho)
        
        # Busca inteligente das colunas
        t_col = self._encontrar_coluna(df.columns, ["trajeto", "rota", "sentido"])
        p_col = self._encontrar_coluna(df.columns, ["partidareal", "partida", "hora"])
        tv_col = self._encontrar_coluna(df.columns, ["tempoviagem", "tempo", "tv"])
        
        if not (t_col and p_col and tv_col): 
            return False, f"Colunas necessárias não encontradas.\nColunas identificadas no Excel: {', '.join(str(c) for c in df.columns)}"
        
        blocos = self._separar_blocos(df[[t_col, p_col, tv_col]].copy(), t_col)
        if not blocos: return False, "Nenhum dado válido encontrado para separação."

        sentidos = {}
        for i, bloco in enumerate(blocos, start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco["TempoStr"] = bloco[tv_col].apply(self._normalizar_tempo)
            bloco["TempoMin"] = pd.to_timedelta(bloco["TempoStr"], errors='coerce').dt.total_seconds() / 60.0
            
            bloco = bloco[bloco["Hora"].notna() & bloco["TempoMin"].notna()]
            if bloco.empty: continue

            medias = bloco.groupby("Hora")["TempoMin"].mean()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")

            sentidos[col_alvo] = {int(h): math.ceil(float(m)) for h, m in medias.items()}
        return True, sentidos

    def processar_excel_verde(self, caminho, nomes_sentidos):
        df = pd.read_excel(caminho)
        
        t_col = self._encontrar_coluna(df.columns, ["trajeto", "rota", "sentido"])
        p_col = self._encontrar_coluna(df.columns, ["partidaplanejada", "planejada", "partida"])
        tv_col = self._encontrar_coluna(df.columns, ["tv", "tempoviagem", "tempo"])
        
        if not (t_col and p_col and tv_col): 
            return False, f"Colunas necessárias não encontradas.\nColunas identificadas no Excel: {', '.join(str(c) for c in df.columns)}"
        
        blocos = self._separar_blocos(df[[t_col, p_col, tv_col]].copy(), t_col)
        sentidos = {}
        for i, bloco in enumerate(blocos, start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco = bloco[bloco["Hora"].notna() & bloco[tv_col].notna()]
            if bloco.empty: continue

            medias = bloco.groupby("Hora")[tv_col].mean()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")

            sentidos[col_alvo] = {int(h): math.ceil(float(m)) for h, m in medias.items()}
        return True, sentidos

    # --- PROCESSAMENTO: DEMANDA ---
    def processar_excel_demanda(self, caminho, nomes_sentidos):
        df = pd.read_excel(caminho)
        
        t_col = self._encontrar_coluna(df.columns, ["trajeto", "rota", "sentido"])
        p_col = self._encontrar_coluna(df.columns, ["partidareal", "partida", "hora"])
        pass_col = self._encontrar_coluna(df.columns, ["passageiro", "passag", "pax", "total"])
        
        if not (t_col and p_col and pass_col): 
            return False, f"Colunas necessárias não encontradas.\nColunas identificadas no Excel: {', '.join(str(c) for c in df.columns)}"
        
        blocos = self._separar_blocos(df[[t_col, p_col, pass_col]].copy(), t_col)
        sentidos = {}
        for i, bloco in enumerate(blocos, start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco[pass_col] = pd.to_numeric(bloco[pass_col], errors='coerce')
            bloco = bloco[bloco["Hora"].notna() & bloco[pass_col].notna()]
            if bloco.empty: continue

            somas = bloco.groupby("Hora")[pass_col].sum()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")
            
            sentidos[col_alvo] = {int(h): int(round(float(s))) for h, s in somas.items()}
        return True, sentidos

    def processar_excel_viagens(self, caminho, nomes_sentidos):
        df = pd.read_excel(caminho)
        
        t_col = self._encontrar_coluna(df.columns, ["trajeto", "rota", "sentido"])
        p_col = self._encontrar_coluna(df.columns, ["partidaplanejada", "planejada", "partida"])
        
        if not (t_col and p_col): 
            return False, f"Colunas necessárias não encontradas.\nColunas identificadas no Excel: {', '.join(str(c) for c in df.columns)}"

        blocos = self._separar_blocos(df[[t_col, p_col]].copy(), t_col)
        viagens = {}
        for i, bloco in enumerate(blocos, start=1):
            bloco["Hora"] = bloco[p_col].apply(self._extrair_hora)
            bloco = bloco[bloco["Hora"].notna()]
            if bloco.empty: continue

            contagens = bloco.groupby("Hora").size()
            nome_norm = self._normalizar_nome(self._extrair_nome_sentido(bloco[t_col].iloc[0]))
            col_alvo = nomes_sentidos.get(nome_norm, f"s{i}")
            
            viagens[col_alvo] = {int(h): int(c) for h, c in contagens.items()}
        return True, viagens