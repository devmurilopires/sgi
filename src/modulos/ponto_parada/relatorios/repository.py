import psycopg2
import json
from config.database import get_db_connection

class RelatorioRepository:

    # BUSCAS GERAIS (TABELA)
    def buscar_ordens_servico(self, filtros):
        query = """
            SELECT id, numero, data_criacao, ponto_principal_id, pontos_adicionais, 
                   acao_realizada, tipo_item, logradouro_completo, bairro, 
                   status_conclusao, data_conclusao, modelo_documento, responsavel, origem_demanda
            FROM sigp.ordens_servico WHERE 1=1
        """
        params = []
        if filtros.get('id'):
            query += " AND (ponto_principal_id ILIKE %s OR pontos_adicionais ILIKE %s)"
            params.extend([f"%{filtros['id']}%", f"%{filtros['id']}%"])
        
        if filtros.get('origem') and filtros['origem'] != "Todos":
            query += " AND origem_demanda = %s"
            params.append(filtros['origem'])
            
        if filtros.get('tipo_os') and filtros['tipo_os'] != "Todos":
            query += " AND acao_realizada ILIKE %s"
            params.append(f"%{filtros['tipo_os']}%")
        if filtros.get('tipo_item') and filtros['tipo_item'] != "Todos":
            query += " AND tipo_item ILIKE %s"
            params.append(f"%{filtros['tipo_item']}%")
        if filtros.get('bairro'):
            query += " AND bairro ILIKE %s"
            params.append(f"%{filtros['bairro']}%")
        if filtros.get('endereco'):
            query += " AND logradouro_completo ILIKE %s"
            params.append(f"%{filtros['endereco']}%")
        if filtros.get('concluida') and filtros['concluida'] != "Todos":
            query += " AND status_conclusao = %s"
            params.append(filtros['concluida'])
        if filtros.get('pasta') and filtros['pasta'] != "Todos":
            query += " AND modelo_documento = %s"
            params.append(filtros['pasta'])
        if filtros.get('numero_os'):
            query += " AND numero = %s"
            params.append(int(filtros['numero_os']))
        if filtros.get('criado_por'):
            query += " AND responsavel ILIKE %s"
            params.append(f"%{filtros['criado_por']}%")
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND data_criacao BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])

        query += " ORDER BY data_criacao DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar OS: {e}")
            return []

    def buscar_pareceres(self, filtros):
        # BUSCA DE PARECERES COM FILTROS DINÂMICOS
        query = """
            SELECT p.id, b.numero_parecer_ano, p.tipo_parecer, p.processo, p.assunto, 
                   p.ids_pontos, p.solicitante, p.endereco_vistoria, p.origem_demanda, 
                   b.created_at, u.nome_completo, p.caminho_arquivo_docx
            FROM sigp.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id WHERE 1=1
        """
        params = []
        
        if filtros.get('origem') and filtros['origem'] != "Todos":
            query += " AND p.origem_demanda = %s"
            params.append(filtros['origem'])
            
        if filtros.get('solicitante') and filtros['solicitante'] != "Todos":
            query += " AND p.solicitante = %s"
            params.append(filtros['solicitante'])
        if filtros.get('assunto') and filtros['assunto'] != "Todos":
            query += " AND p.assunto = %s"
            params.append(filtros['assunto'])
        if filtros.get('processo'):
            query += " AND p.processo ILIKE %s"
            params.append(f"%{filtros['processo']}%")
        if filtros.get('numero_parecer'):
            query += " AND b.numero_parecer_ano = %s"
            params.append(int(filtros['numero_parecer']))
        if filtros.get('id'):
            query += " AND p.ids_pontos ILIKE %s"
            params.append(f"%{filtros['id']}%")
        if filtros.get('tipo') and filtros['tipo'] != "Todos":
            query += " AND p.tipo_parecer = %s"
            params.append(filtros['tipo'].upper())
        if filtros.get('endereco'):
            query += " AND p.endereco_vistoria ILIKE %s"
            params.append(f"%{filtros['endereco']}%")
        if filtros.get('criado_por'):
            query += " AND u.nome_completo ILIKE %s"
            params.append(f"%{filtros['criado_por']}%")
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(b.created_at) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])

        # Ordenação por Data de Criação (Mais Recente Primeiro)
        query += " ORDER BY b.created_at DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar Pareceres: {e}")
            return []

    # BUSCA DE TODOS OS DETALHES E FUNÇÕES DE EXCLUSÃO
    def buscar_detalhes_os(self, id_banco):
        query = """
            SELECT numero, TO_CHAR(data_criacao, 'DD/MM/YYYY'), origem_demanda, ponto_principal_id, pontos_adicionais, 
                   acao_realizada, tipo_item, logradouro_completo, bairro, complemento,
                   descricao_tecnica, responsavel, modelo_documento, status_conclusao
            FROM sigp.ordens_servico WHERE id = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_banco,))
                    row = cursor.fetchone()
                    if row:
                        # ---> REMOVIDO "(Croqui)" da Descrição <---
                        colunas = ["Nº OS", "Data Criação", "Origem", "ID Principal", "IDs Adicionais", 
                                   "Ação Realizada", "Tipo Item", "Endereço", "Bairro", "Complemento",
                                   "Descrição", "Criado por", "Modelo", "Status Conclusão"]
                        return dict(zip(colunas, row))
        except Exception as e: pass
        return None

    def buscar_detalhes_parecer(self, id_banco):
        # BUSCA DE TODOS OS DETALHES DO PARECER PARA A TELA DE EDIÇÃO
        query = """
            SELECT b.numero_parecer_ano, TO_CHAR(b.created_at, 'DD/MM/YYYY'), p.origem_demanda, p.tipo_parecer, 
                   p.processo, p.assunto, p.solicitante, p.ids_pontos, p.tipo_execucao, 
                   p.item, p.endereco_vistoria, p.quantidade, p.motivo_indeferimento, u.nome_completo
            FROM sigp.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id
            WHERE p.id = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_banco,))
                    row = cursor.fetchone()
                    if row:
                        colunas = ["Nº Parecer", "Data Criação", "Origem", "Decisão", "Processo", 
                                   "Assunto", "Solicitante", "IDs dos Pontos", "Ação Recomendada", 
                                   "Item", "Endereço", "Quantidade", "Motivo", "Criado por"]
                        return dict(zip(colunas, row))
        except Exception as e: pass
        return None

    def atualizar_os(self, id_banco, dados):
        # ATUALIZAÇÃO DE ORDEM DE SERVIÇO (COM LÓGICA DE DATA DE CONCLUSÃO)
        query = """
            UPDATE sigp.ordens_servico 
            SET origem_demanda=%s, ponto_principal_id=%s, pontos_adicionais=%s, acao_realizada=%s, 
                tipo_item=%s, logradouro_completo=%s, bairro=%s, complemento=%s,
                descricao_tecnica=%s, status_conclusao=%s, responsavel=%s,
                data_conclusao = CASE 
                    WHEN %s IN ('SIM', 'NÃO AUTORIZADA') THEN COALESCE(data_conclusao, CURRENT_TIMESTAMP)
                    ELSE NULL 
                END
            WHERE id=%s
        """
        status = dados.get("Status Conclusão", "NÃO").strip().upper()
        acao_up = str(dados.get("Ação Realizada", "")).strip().upper()
        item_up = str(dados.get("Tipo Item", "")).strip().upper()
        origem_up = str(dados.get("Origem", "SPU")).strip().upper()
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        origem_up, dados.get("ID Principal"), dados.get("IDs Adicionais"), acao_up, item_up, 
                        dados.get("Endereço"), dados.get("Bairro"), dados.get("Complemento"), 
                        dados.get("Descrição"), status, dados.get("Criado por"), status, id_banco
                    ))
            return True, "Ordem de Serviço atualizada com sucesso!"
        except Exception as e: return False, f"Erro ao atualizar: {e}"

    def atualizar_parecer(self, id_banco, dados):
        # ATUALIZAÇÃO DE PARECER (COM LÓGICA PARA MOTIVO DE INDEFERIMENTO)
        query1 = """
            UPDATE sigp.pareceres 
            SET origem_demanda=%s, tipo_parecer=%s, processo=%s, assunto=%s, solicitante=%s, 
                ids_pontos=%s, tipo_execucao=%s, item=%s, endereco_vistoria=%s,
                quantidade=%s, motivo_indeferimento=%s
            WHERE id = %s
        """
        query2 = """
            UPDATE common.pareceres_base 
            SET criado_por_id = COALESCE(
                (SELECT id FROM common.usuarios WHERE nome_completo ILIKE %s LIMIT 1), 
                criado_por_id
            )
            WHERE id = %s
        """
        # Padronização dos campos (Maiúsculas e Tratamento de Nulos)
        origem_up = str(dados.get("Origem", "SPU")).strip().upper()
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Salva os dados do parecer
                    cursor.execute(query1, (
                        origem_up, dados.get("Decisão"), dados.get("Processo"), dados.get("Assunto"), 
                        dados.get("Solicitante"), dados.get("IDs dos Pontos"), dados.get("Ação Recomendada"), 
                        dados.get("Item"), dados.get("Endereço"), dados.get("Quantidade"), dados.get("Motivo"), id_banco
                    ))
                    # Salva o usuário Responsável
                    if dados.get("Criado por"):
                        cursor.execute(query2, (f"%{dados.get('Criado por').strip()}%", id_banco))
                        
            return True, "Parecer atualizado com sucesso!"
        except Exception as e: return False, f"Erro ao atualizar: {e}"

    def obter_dados_para_caminho_os(self, id_banco):
        # BUSCA DE DADOS ESSENCIAIS PARA MONTAR O CAMINHO DO ARQUIVO WORD DA OS
        query = "SELECT numero, data_criacao, ponto_principal_id, pontos_adicionais, modelo_documento FROM sigp.ordens_servico WHERE id = %s"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (id_banco,))
                    return cur.fetchone()
        except: return None

    def obter_caminho_parecer(self, id_banco):
        # BUSCA DO CAMINHO DO ARQUIVO WORD DO PARECER PARA DOWNLOAD
        query = "SELECT caminho_arquivo_docx FROM sigp.pareceres WHERE id = %s"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (id_banco,))
                    res = cur.fetchone()
                    return res[0] if res else None
        except: return None

    def excluir_e_logar_os(self, id_banco, dados_json, caminho_original, motivo, excluido_por):
        # EXCLUSÃO DE ORDEM DE SERVIÇO COM LOG NO HISTÓRICO
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT numero FROM sigp.ordens_servico WHERE id = %s", (id_banco,))
                    numero_real = cur.fetchone()[0]
                    cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por) VALUES ('OS_SIGP', %s, %s, %s, %s, %s)", (numero_real, json.dumps(dados_json, ensure_ascii=False), caminho_original, motivo, excluido_por))
                    cur.execute("DELETE FROM sigp.ordens_servico WHERE id = %s", (id_banco,))
            return True, "OS excluída e registrada no Histórico com sucesso!"
        except Exception as e: return False, f"Erro no banco ao excluir: {e}"

    def excluir_e_logar_parecer(self, id_banco, dados_json, caminho_original, motivo, excluido_por):
        # EXCLUSÃO DE PARECER COM LOG NO HISTÓRICO
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT numero_parecer_ano FROM common.pareceres_base WHERE id = %s", (id_banco,))
                    linha = cur.fetchone()
                    if not linha: return False, "Parecer não encontrado."
                    numero_real = linha[0]
                    cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por) VALUES ('PARECER_SIGP', %s, %s, %s, %s, %s)", (numero_real, json.dumps(dados_json, ensure_ascii=False), caminho_original, motivo, excluido_por))
                    cur.execute("DELETE FROM sigp.pareceres WHERE id = %s", (id_banco,))
                    cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (id_banco,))
            return True, "Parecer excluído e registrado no Histórico com sucesso!"
        except Exception as e: return False, f"Erro no banco ao excluir: {e}"