from src.modulos.admin.parametros.repository import ParametrosRepository

class ParametrosService:
    def __init__(self):
        self.repository = ParametrosRepository()

    def adicionar_parametro(self, routing, valor):
        if not valor: return False, "O Valor é obrigatório."
        return self.repository.inserir_parametro(routing, valor.strip())

    def inativar_parametro(self, routing, parametro_id):
        if not parametro_id: return False, "ID é obrigatório."
        return self.repository.inativar_parametro(routing, parametro_id)

    def editar_parametro(self, routing, parametro_id, novo_valor):
        if not parametro_id or not novo_valor: return False, "Todos os campos são obrigatórios."
        return self.repository.atualizar_valor(routing, parametro_id, novo_valor.strip())

    def listar_parametros(self, routing):
        if not routing: return []
        return self.repository.listar_parametros(routing)

    def obter_roteamento(self, setor, campo=None):
        """
        Roteador Inteligente e Híbrido:
        Suporta os dois padrões de chamada do sistema para manter retrocompatibilidade:
        1. obter_roteamento(campo) -> Vindo da View do Admin
        2. obter_roteamento(setor, campo) -> Vindo do componente compartilhado CtkParametrosComboBox
        """
        # Se 'campo' for None, significa que a função foi chamada com apenas 1 argumento,
        # portanto o argumento recebido na variável 'setor' é, na verdade, o próprio campo.
        if campo is None:
            c_key = str(setor).upper()
        else:
            c_key = str(campo).upper()

        # 1. ORIGENS
        if c_key == "ORIGEM":
            return {"tabela": "common.origens", "col_ctx": None, "val_ctx": None, "col_val": "nome"}

        # 2. TABELA DE TIPOS E AÇÕES
        map_tipos = {
            "ACAO_OS": "ACAO_OS", 
            "MODELO_OS": "MODELO_OS",
            "STATUS_OS": "STATUS_OS",              
            "DECISAO_PARECER": "DECISAO_PARECER",
            "ITEM_URBMIDIA": "ITEM_URBMIDIA",
            "ITEM_MCMENSAGEM": "ITEM_MCMENSAGEM",
            "ITENS": "ITENS",
            "TIPO_OS": "TIPO_OS",
            "PESQUISA": "PESQUISA",
            "NATUREZA_MANIFESTACAO": "NATUREZA_MANIFESTACAO" # <--- ADICIONE ESTA LINHA AQUI
        }
        
        if c_key in map_tipos:
            return {"tabela": "common.tipos", "col_ctx": "contexto", "val_ctx": map_tipos[c_key], "col_val": "nome"}
        
        # 3. TABELA DE PARÂMETROS GERAIS
        map_parametros = {
            "SOLICITANTE_PARECER": "SOLICITANTE_PARECER",
            "ASSUNTO_PARECER": "ASSUNTO_PARECER",
            "ASSUNTO_ITINERARIO": "ASSUNTO_ITINERARIO",
            "ASSUNTO_QUADRO_HORARIO": "ASSUNTO_QUADRO_HORARIO",
            "ASSUNTO_PROJETOS_MOBILIDADE": "ASSUNTO_PROJETOS_MOBILIDADE",
            "EVENTO": "EVENTO"
        }

        if c_key in map_parametros:
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": map_parametros[c_key], "col_val": "valor"}

        return None # Proteção contra crashes se o mapeamento falhar
    
    def reordenar_parametros(self, routing, lista_ids):
        if not lista_ids: return False, "Nenhum dado para ordenar."
        return self.repository.atualizar_ordem_lote(routing, lista_ids)