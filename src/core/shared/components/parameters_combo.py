import customtkinter as ctk
from src.modulos.admin.parametros.service import ParametrosService

class CtkParametrosComboBox(ctk.CTkComboBox):
    """
    Componente customizado que carrega opções da tabela common.parametros_sistema
    e se atualiza automaticamente em tempo real em todas as telas.
    """
    def __init__(self, master, setor, campo, incluir_todos=False, **kwargs):
        # 1. Configurações Iniciais
        self.service = ParametrosService()
        self.categoria_slug = self.service.get_slug(setor, campo)
        self.incluir_todos = incluir_todos
        
        # Inicializa com lista vazia[cite: 14]
        super().__init__(master, values=[], **kwargs)
        
        # 2. Carrega os dados pela primeira vez[cite: 14]
        self.atualizar_opcoes()
        
        # 3. O Pulo do Gato (Dica Senior): O próprio componente escuta o evento global!
        # Usamos o 'after' de 100ms para garantir que a janela principal já foi desenhada pelo Tkinter
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
            # Guarda o valor que o usuário tem selecionado atualmente
            valor_atual = self.get()
            
            # Busca os parâmetros atualizados no banco[cite: 14]
            dados = self.service.listar_por_categoria(self.categoria_slug)
            opcoes = [item['valor'] for item in dados]
            
            # Fallback caso o banco não retorne nada[cite: 14]
            if not opcoes:
                opcoes = ["Nenhuma opção cadastrada"]
                
            # Mágica para Telas de Filtros: Adiciona "Todos" automaticamente
            if self.incluir_todos:
                opcoes.insert(0, "Todos")
            
            # Atualiza a interface gráfica do componente[cite: 14]
            self.configure(values=opcoes)
            
            # Restaura a seleção inteligente
            if valor_atual in opcoes:
                self.set(valor_atual) # Mantém o que estava selecionado
            else:
                self.set(opcoes[0])   # Seleciona o primeiro (ou "Todos")

        except Exception as e:
            print(f"Erro ao carregar opções para {self.categoria_slug}: {e}")
            self.configure(values=["Erro ao carregar"])
            self.set("Erro ao carregar")