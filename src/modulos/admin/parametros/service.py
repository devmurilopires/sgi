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

        # No método obter_roteamento da classe ParametrosService...
        map_tipos = {
            "ACAO_OS": "ACAO_OS", 
            "MODELO_OS": "MODELO_OS",
            "ITEM_URBMIDIA": "ITEM_URBMIDIA",
            "ITEM_MCMENSAGEM": "ITEM_MCMENSAGEM",
            "ITEM_MOBILIARIO": "ITEM_MOBILIARIO",  
            "PESQUISA": "PESQUISA",                
            "TIPO_OS": "TIPO_OS",
            "TIPO_EVENTO_OS": "TIPO_EVENTO_OS",
            "STATUS_OS": "STATUS_OS",              
            "DECISAO_PARECER": "PARECER"
        }
        
        if c_key in map_tipos:
            return {"tabela": "common.tipos", "col_ctx": "contexto", "val_ctx": map_tipos[c_key], "col_val": "nome"}
        if c_key == "ITEM_GLOBAL":
            return {"tabela": "common.tipos", "col_ctx": "contexto IN ('ITEM_URBMIDIA', 'ITEM_MCMENSAGEM', 'ITEM_MOBILIARIO') AND is_ativo", "val_ctx": True, "col_val": "nome"}
        if c_key in map_tipos:
            return {"tabela": "common.tipos", "col_ctx": "contexto", "val_ctx": map_tipos[c_key], "col_val": "nome"}
        if c_key == "SOLICITANTE_PARECER":
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": "SOLICITANTE_PARECER", "col_val": "valor"}
        if c_key == "ASSUNTO_PARECER":
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": "ASSUNTO_PARECER", "col_val": "valor"}
        if c_key == "ASSUNTO_ITINERARIO":
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": "ASSUNTO_ITINERARIO", "col_val": "valor"}
        if c_key == "ASSUNTO_QUADRO_HORARIO":
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": "ASSUNTO_QUADRO_HORARIO", "col_val": "valor"}
        if c_key == "EVENTO":
            # Agora a busca de Eventos cai aqui (tabela correta!)
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": "EVENTO", "col_val": "valor"}
        if c_key == "ASSUNTO_PROJETOS_MOBILIDADE": # <-- NOVA LINHA AQUI
            return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": "ASSUNTO_PROJETOS_MOBILIDADE", "col_val": "valor"}

        # Comportamento padrão (slug)
        slug_categoria = f"{s_key}_{c_key}".lower().replace(' ', '_')
        return {"tabela": "common.parametros_sistema", "col_ctx": "categoria", "val_ctx": slug_categoria, "col_val": "valor"}
    
    def reordenar_parametros(self, routing, lista_ids):
        if not lista_ids: return False, "Nenhum dado para ordenar."
        return self.repository.atualizar_ordem_lote(routing, lista_ids)