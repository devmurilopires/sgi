from src.modulos.admin.parametros.repository import ParametrosRepository

class ParametrosService:
    def __init__(self):
        self.repository = ParametrosRepository()

    def adicionar_parametro(self, categoria, valor):
        """
        Regra de negócio para adicionar um novo parâmetro.
        Valida se os campos não estão vazios.
        """
        if not categoria or not valor:
            raise ValueError("Categoria e Valor são campos obrigatórios.")
        
        # Opcional: Converter categoria para uppercase para manter padrão
        categoria_limpa = categoria.strip().upper()
        valor_limpo = valor.strip()
        
        return self.repository.inserir_parametro(categoria_limpa, valor_limpo)

    def inativar_parametro(self, parametro_id):
        """
        Regra de negócio para inativar um parâmetro.
        """
        if not parametro_id:
            raise ValueError("ID do parâmetro é obrigatório para inativação.")
            
        return self.repository.inativar_parametro(parametro_id)

    def listar_por_categoria(self, categoria):
        """
        Regra de negócio para listar parâmetros por categoria.
        """
        if not categoria:
            return []
            
        categoria_limpa = categoria.strip().upper()
        return self.repository.get_parametros_by_categoria(categoria_limpa)
