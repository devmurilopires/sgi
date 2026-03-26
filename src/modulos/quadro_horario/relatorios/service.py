import os
import subprocess
import sys
from src.modulos.quadro_horario.relatorios.repository import RelatorioQuadroHorarioRepository

class RelatorioQuadroHorarioService:
    def __init__(self):
        self.repo = RelatorioQuadroHorarioRepository()

    def buscar_dados(self, tipo_relatorio, filtros):
        if tipo_relatorio == "PARECER":
            return self.repo.buscar_pareceres(filtros)
        elif tipo_relatorio == "PESQUISA":
            return self.repo.buscar_pesquisas(filtros)
        return []

    def buscar_detalhes(self, tipo_relatorio, id_banco):
        if tipo_relatorio == "PARECER":
            return self.repo.buscar_detalhes_parecer(id_banco)
        return None

    def excluir_registro(self, tipo_relatorio, id_banco, motivo, usuario_logado):
        return self.repo.excluir_e_logar(id_banco, tipo_relatorio, motivo, usuario_logado)

    def abrir_arquivo(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return False, "O documento non se atopou na rede ou foi movido."
        try:
            if os.name == 'nt':
                os.startfile(caminho)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.Popen([opener, caminho])
            return True, ""
        except Exception as e:
            return False, f"Non foi posíbel abrir: {str(e)}"