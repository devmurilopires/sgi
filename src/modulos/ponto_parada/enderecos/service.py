import pandas as pd
from tkinter import filedialog
from src.enderecos.repository import EnderecoRepository

class EnderecoService:
    def __init__(self):
        self.repo = EnderecoRepository()

    def salvar_endereco(self, dados: dict, usuario_logado: dict):
        # Validação Simples
        id_ponto = dados.get('id_ponto', '').strip().upper()
        endereco = dados.get('endereco', '').strip().upper()
        
        if not id_ponto or not endereco:
            return False, "Os campos 'ID do Ponto' e 'Endereço' são obrigatórios!"

        # Prepara os dados opcionais
        numero = dados.get('numero', '').strip() or 'S/N'
        bairro = dados.get('bairro', '').strip().upper()
        complemento = dados.get('complemento', '').strip().upper()
        status = dados.get('status', 'ATIVO').strip().upper()
        
        # O usuário logado assina automaticamente quem registrou a vistoria/ponto
        criado_por = usuario_logado.get('nome_completo', 'Sistema')

        # Manda para o repositório
        return self.repo.salvar_ou_atualizar(id_ponto, endereco, numero, bairro, complemento, status, criado_por)

    def listar_enderecos(self):
        return self.repo.listar_todos()

    def exportar_excel(self):
        df = self.listar_enderecos()
        if df.empty:
            return False, "Não há dados para exportar."

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Planilha Excel", "*.xlsx")], 
            title="Salvar Banco de Endereços"
        )
        
        if not filepath:
            return False, "Exportação cancelada pelo usuário."

        try:
            # Formata a data para ficar bonita no Excel
            if 'updated_at' in df.columns:
                df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%d/%m/%Y %H:%M')

            # Renomeia as colunas para o usuário final
            df.columns = ["ID", "ENDEREÇO", "NÚMERO", "BAIRRO", "COMPLEMENTO", "STATUS", "ÚLTIMA ATUALIZAÇÃO POR", "DATA ATUALIZAÇÃO"]
            
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Endereços', index=False)
                worksheet = writer.sheets['Endereços']
                # Ajusta a largura das colunas
                worksheet.set_column('A:A', 15)
                worksheet.set_column('B:B', 40)
                worksheet.set_column('C:E', 20)
                worksheet.set_column('F:H', 25)

            return True, "Planilha exportada com sucesso!"
        except Exception as e:
            return False, f"Erro ao exportar: {e}"