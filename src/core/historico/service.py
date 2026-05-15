from src.core.historico.repository import HistoricoRepository

class HistoricoService:
    def __init__(self):
        # Instancia a camada de dados
        self.repo = HistoricoRepository()

    def buscar_historico(self, filtros):
        """
        Orquestra a busca de registros na lixeira repassando os filtros da tela 
        para o repositório.
        """
        if not isinstance(filtros, dict):
            return []
            
        return self.repo.buscar_historico(filtros)