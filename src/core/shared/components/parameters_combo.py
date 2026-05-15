import customtkinter as ctk
from src.modulos.admin.parametros.service import ParametrosService

class CtkParametrosComboBox(ctk.CTkComboBox):
    """
    Componente customizado que carrega opções dinâmicas do banco SGI v2.2
    e se atualiza automaticamente em tempo real em todas as telas.
    """
    def __init__(self, master, setor, campo, incluir_todos=False, **kwargs):
        # 1. Configurações Iniciais
        self.service = ParametrosService()
        # MODIFICAÇÃO: Utilizando o Roteador Inteligente do Admin
        self.routing = self.service.obter_roteamento(setor, campo)
        self.incluir_todos = incluir_todos
        
        super().__init__(master, values=[], **kwargs)
        
        # 2. Carrega os dados pela primeira vez
        self.atualizar_opcoes()
        
        # 3. Ouve as atualizações do painel Admin
        self.after(100, self._registrar_ouvinte)

    def _registrar_ouvinte(self):
        """Registra o componente para ouvir as atualizações do painel Admin."""
        try:
            toplevel = self.winfo_toplevel()
            toplevel.bind("<<ParametrosAtualizados>>", self._on_atualizacao, add="+")
        except Exception as e:
            print(f"Aviso: Não foi possível registrar o ouvinte no componente: {e}")

    def _on_atualizacao(self, event=None):
        """Método acionado silenciosamente quando o evento global é disparado."""
        self.atualizar_opcoes()

    def atualizar_opcoes(self):
        """Busca os dados atualizados no banco e recarrega o ComboBox com segurança."""
        try:
            valor_atual = self.get()
            
            # MODIFICAÇÃO: Passando o dicionário de roteamento em vez do slug
            dados = self.service.listar_parametros(self.routing)
            opcoes = [item['valor'] for item in dados]
            
            # Fallback caso o banco não retorne nada
            if not opcoes:
                opcoes = ["Nenhuma opção cadastrada"]
                
            # Mágica para Telas de Filtros: Adiciona "Todos" automaticamente
            if self.incluir_todos:
                opcoes.insert(0, "Todos")
            
            self.configure(values=opcoes)
            
            # Restaura a seleção inteligente
            if valor_atual in opcoes:
                self.set(valor_atual)
            else:
                self.set(opcoes[0])

        except Exception as e:
            print(f"Erro ao carregar opções dinâmicas: {e}")
            self.configure(values=["Erro ao carregar"])
            self.set("Erro ao carregar")