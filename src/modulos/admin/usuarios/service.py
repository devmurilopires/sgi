from src.modulos.admin.usuarios.repository import UsuariosRepository

class UsuariosService:
    def __init__(self):
        self.repository = UsuariosRepository()

    def listar_usuarios(self):
        """Retorna a lista de todos os usuários."""
        return self.repository.get_all_usuarios()

    def atualizar_perfil_acesso(self, usuario_id, perfil):
        """Valida e atualiza o perfil do usuário."""
        if not usuario_id or not perfil:
            return False, "ID do usuário e Perfil são obrigatórios."
        return self.repository.atualizar_perfil(usuario_id, perfil)

    def alterar_status_admin(self, usuario_id, e_admin):
        """Define se o usuário é administrador ou não."""
        if not usuario_id:
            return False, "ID do usuário é obrigatório."
        return self.repository.toggle_admin(usuario_id, e_admin)

    def alterar_status_ativo(self, usuario_id, e_ativo):
        """Ativa ou desativa o acesso do usuário ao sistema."""
        if not usuario_id:
            return False, "ID do usuário é obrigatório."
        return self.repository.toggle_ativo(usuario_id, e_ativo)