import os
import subprocess
import sys
from src.modulos.itinerario.relatorios.repository import RelatorioItinerarioRepository

class RelatorioItinerarioService:
    def __init__(self):
        self.repo = RelatorioItinerarioRepository()

    def buscar_dados(self, tipo_relatorio, filtros):
        if tipo_relatorio == "OS":
            return self.repo.buscar_ordens_servico(filtros)
        elif tipo_relatorio == "PARECER":
            return self.repo.buscar_pareceres(filtros)
        return []

    def buscar_detalhes(self, tipo_relatorio, id_banco):
        if tipo_relatorio == "OS":
            return self.repo.buscar_detalhes_os(id_banco)
        return self.repo.buscar_detalhes_parecer(id_banco)

    def excluir_registro(self, tipo_relatorio, id_banco, motivo, usuario_logado):
        return self.repo.excluir_e_logar(id_banco, tipo_relatorio, motivo, usuario_logado)

    def abrir_arquivo(self, caminho):
        if not caminho or not os.path.exists(caminho):
            return False, "O arquivo não foi encontrado na rede ou foi movido."
        try:
            if os.name == 'nt':
                os.startfile(caminho)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.Popen([opener, caminho])
            return True, ""
        except Exception as e:
            return False, f"Não foi possível abrir: {str(e)}"