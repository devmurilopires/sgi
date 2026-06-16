import pandas as pd
from tkinter import filedialog
from src.modulos.ponto_parada.enderecos.repository import EnderecoRepository

class EnderecoService:
    def __init__(self):
        self.repo = EnderecoRepository()

    def salvar_endereco(self, dados: dict, usuario_logado: dict):
        id_ponto = dados.get('id_ponto', '').strip().upper()
        endereco = dados.get('endereco', '').strip().upper()
        if not id_ponto or not endereco: return False, "Os campos 'ID do Ponto' e 'Endereço' são obrigatórios!"

        numero = dados.get('numero', '').strip() or 'S/N'
        bairro = dados.get('bairro', '').strip().upper()
        complemento = dados.get('complemento', '').strip().upper()
        status = dados.get('status', 'ATIVO').strip().upper()
        criado_por = usuario_logado.get('nome_completo', 'Sistema')

        return self.repo.salvar_ou_atualizar(id_ponto, endereco, numero, bairro, complemento, status, criado_por)

    def excluir_endereco(self, id_ponto):
        if not id_ponto: return False, "ID do Ponto é obrigatório para realizar a exclusão."
        return self.repo.excluir(id_ponto)

    # Conectores da Paginação
    def contar_enderecos(self, termo=""):
        return self.repo.contar_enderecos(termo)

    def listar_enderecos_paginados(self, termo="", limit=50, offset=0):
        return self.repo.listar_enderecos_paginados(termo, limit, offset)

    def obter_valores_unicos(self, campo):
        return self.repo.obter_valores_unicos(campo)

    def padronizar_valores(self, campo: str, valores_antigos: list, novo_valor: str):
        if not valores_antigos: return False, f"Selecione ao menos um {campo.lower()} na lista para padronizar."
        if not novo_valor or not novo_valor.strip(): return False, f"O novo nome do {campo.lower()} não pode ficar em branco."
        return self.repo.padronizar_valores(campo, valores_antigos, novo_valor.strip().upper())

    def exportar_excel(self):
        df = self.repo.listar_todos()
        if df.empty: return False, "Não há dados para exportar."

        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Planilha Excel", "*.xlsx")], title="Salvar Banco de Endereços")
        if not filepath: return False, "Exportação cancelada pelo usuário."

        try:
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%d/%m/%Y %H:%M')

            df.columns = ["ID", "ENDEREÇO", "NÚMERO", "BAIRRO", "COMPLEMENTO", "STATUS", "ÚLTIMA ATUALIZAÇÃO POR", "DATA ATUALIZAÇÃO"]
            
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Endereços', index=False)
                worksheet = writer.sheets['Endereços']
                worksheet.set_column('A:A', 15)
                worksheet.set_column('B:B', 40)
                worksheet.set_column('C:E', 20)
                worksheet.set_column('F:H', 25)

            return True, "Planilha exportada com sucesso!"
        except Exception as e:
            return False, f"Erro ao exportar: {e}"
        
    def contar_valores_unicos(self, campo, termo=""):
        return self.repo.contar_valores_unicos(campo, termo)

    def listar_valores_unicos_paginados(self, campo, termo="", limit=50, offset=0):
        return self.repo.listar_valores_unicos_paginados(campo, termo, limit, offset)