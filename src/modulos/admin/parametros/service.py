from src.modulos.admin.parametros.repository import ParametrosRepository

class ParametrosService:
    def __init__(self):
        self.repository = ParametrosRepository()

    def adicionar_parametro(self, categoria, valor):
        """Regra de negócio para adicionar um novo parâmetro."""
        if not categoria or not valor:
            raise ValueError("Categoria e Valor são campos obrigatórios.")
        
        categoria_limpa = categoria.strip()
        valor_limpo = valor.strip()
        return self.repository.inserir_parametro(categoria_limpa, valor_limpo)

    def inativar_parametro(self, parametro_id):
        """Regra de negócio para inativar um parâmetro."""
        if not parametro_id:
            raise ValueError("ID do parâmetro é obrigatório para inativação.")
        return self.repository.inativar_parametro(parametro_id)

    def editar_parametro(self, parametro_id, novo_valor):
        """Regra de negócio para editar o valor de um parâmetro."""
        if not parametro_id or not novo_valor:
            raise ValueError("ID e Novo Valor são obrigatórios.")
        valor_limpo = novo_valor.strip()
        return self.repository.atualizar_valor(parametro_id, valor_limpo)

    def listar_por_categoria(self, categoria):
        """Regra de negócio para listar parâmetros por categoria."""
        if not categoria:
            return []
        categoria_limpa = categoria.strip()
        return self.repository.get_parametros_by_categoria(categoria_limpa)

    def get_slug(self, setor, campo):
        """Mapeia o setor e campo para o slug exato do banco de dados."""
        if campo.upper() in ["ORIGEM", "ORIGEM_DEMANDA"]:
            return "geral_origem"

        mapping = {
            "PONTO DE PARADA": {
                "TIPO_ITEM": "ponto_parada_tipo_item",
                "ACAO_OS": "ponto_parada_acao",
                "SOLICITANTE": "ponto_parada_solicitante"
            },
            "ITINERÁRIO": {
                "EVENTO": "itinerario_evento",
                "SOLICITANTE": "itinerario_solicitante",
                "ASSUNTO": "itinerario_assunto"
            },
            "QUADRO DE HORÁRIO": {
                "SOLICITANTE": "qh_solicitante",
                "ASSUNTO": "qh_assunto",
                "EVENTO": "qh_evento"
            }
        }

        s_key = setor.upper()
        c_key = campo.upper()

        if s_key in mapping and c_key in mapping[s_key]:
            return mapping[s_key][c_key]
        
        return f"{s_key}_{c_key}".lower().replace(' ', '_')
