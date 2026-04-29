import customtkinter as ctk
from src.modulos.admin.parametros.service import ParametrosService

class CtkParametrosComboBox(ctk.CTkComboBox):
    """
    Componente customizado que carrega automaticamente opções da tabela
    common.parametros_sistema baseada em uma categoria.
    """
    def __init__(self, master, setor, campo, **kwargs):
        # Gera o slug da categoria seguindo o padrão definido no Admin
        self.categoria_slug = f"{setor.upper().replace(' ', '_')}_{campo.upper()}"
        self.service = ParametrosService()
        
        # Inicializa com lista vazia, os dados serão carregados no reload
        super().__init__(master, values=[], **kwargs)
        
        self.atualizar_opcoes()

    def atualizar_opcoes(self):
        """Busca os dados atualizados no banco e recarrega o ComboBox."""
        try:
            # Busca os parâmetros da categoria
            dados = self.service.listar_por_categoria(self.categoria_slug)
            
            # Extrai apenas os valores
            opcoes = [item['valor'] for item in dados]
            
            # Se não houver opções, adiciona um placeholder ou lista vazia
            if not opcoes:
                opcoes = ["Nenhuma opção cadastrada"]
            
            self.configure(values=opcoes)
            if opcoes:
                self.set(opcoes[0]) # Seleciona o primeiro por padrão
        except Exception as e:
            print(f"Erro ao carregar opções para {self.categoria_slug}: {e}")
            self.configure(values=["Erro ao carregar"])
