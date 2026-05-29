from src.modulos.admin.linhas.repository import LinhasRepository

class LinhasService:
    def __init__(self):
        self.repo = LinhasRepository()

    def listar_linhas(self):
        return self.repo.get_all_linhas()

    def salvar_linha(self, linha_id, codigo, nome):
        if not codigo or not nome:
            return False, "O Código e o Nome da linha são obrigatórios."
        
        if linha_id:
            return self.repo.atualizar_linha(linha_id, codigo, nome)
        else:
            return self.repo.adicionar_linha(codigo, nome)

    def alterar_status(self, linha_id, is_ativo):
        if not linha_id:
            return False, "ID da linha é obrigatório."
        return self.repo.toggle_ativo(linha_id, is_ativo)