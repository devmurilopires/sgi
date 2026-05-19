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

    def obter_roteamento(self, setor, campo):
        """
        Roteador Sênior: Mapeia o Campo da Interface para a Tabela SGI v2.2.
        """
        c_key = campo.upper()
        s_key = setor.upper()

        # 1. ORIGENS
        if c_key in ["ORIGEM", "ORIGEM_DEMANDA"]:
            return {"tabela": "common.origens", "col_ctx": None, "val_ctx": None, "col_val": "nome"}

        # 2. TIPOS ESTRUTURAIS (Corrigido para mapear as chaves exatas do seu SQL)
        map_tipos = {
            "ACAO_OS": "ACAO_OS", 
            "ITEM_URBMIDIA": "ITEM_URBMIDIA",
            "ITEM_MCMENSAGEM": "ITEM_MCMENSAGEM",
            "EVENTO": "TIPO_EVENTO"
        }
        if c_key in map_tipos:
            return {"tabela": "common.tipos", "col_ctx": "contexto", "val_ctx": map_tipos[c_key], "col_val": "nome"}

        # 3. TEXTOS SIMPLES (Exceções inseridas via SQL)
        if c_key == "SOLICITANTE_PARECER":
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": "SOLICITANTE_PARECER", "col_val": "valor"}
        if c_key == "ASSUNTO_PARECER":
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": "ASSUNTO_PARECER", "col_val": "valor"}

        # Comportamento padrão (slug)
        slug_categoria = f"{s_key}_{c_key}".lower().replace(' ', '_')
        
        return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": slug_categoria, "col_val": "valor"}