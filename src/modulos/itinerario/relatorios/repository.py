import json
from config.database import get_db_connection

class RelatorioItinerarioRepository:
    def buscar_ordens_servico(self, filtros):
        query = """
            SELECT id, numero, tipo_evento, solicitante, TO_CHAR(data_criacao, 'DD/MM/YYYY'), 
                   empresas_text, processo_adm, caminho_arquivo, responsavel
            FROM siga.ordens_servico WHERE 1=1
        """
        params = []
        if filtros.get('numero_os'):
            query += " AND numero = %s"; params.append(int(filtros['numero_os']))
        if filtros.get('tipo_os') and filtros['tipo_os'] != "Todos":
            query += " AND tipo_evento = %s"; params.append(filtros['tipo_os'].lower())
        if filtros.get('solicitante'):
            query += " AND solicitante ILIKE %s"; params.append(f"%{filtros['solicitante']}%")
        if filtros.get('empresa'):
            query += " AND empresas_text ILIKE %s"; params.append(f"%{filtros['empresa']}%")
        if filtros.get('processo'):
            query += " AND processo_adm ILIKE %s"; params.append(f"%{filtros['processo']}%")
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(data_criacao) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])

        query += " ORDER BY data_criacao DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except: return []

    def buscar_pareceres(self, filtros):
        query = """
            SELECT p.id, b.numero_parecer_ano, p.processo, p.tipo_parecer, p.assunto, 
                   p.data_evento, p.solicitante, p.linhas_afetadas, u.nome_completo, p.caminho_arquivo
            FROM siga.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id WHERE 1=1
        """
        params = []
        if filtros.get('numero_parecer'):
            query += " AND b.numero_parecer_ano = %s"; params.append(int(filtros['numero_parecer']))
        if filtros.get('tipo') and filtros['tipo'] != "Todos":
            query += " AND p.tipo_parecer = %s"; params.append(filtros['tipo'].upper())
        if filtros.get('solicitante'):
            query += " AND p.solicitante ILIKE %s"; params.append(f"%{filtros['solicitante']}%")
        if filtros.get('linha'):
            query += " AND p.linhas_afetadas ILIKE %s"; params.append(f"%{filtros['linha']}%")
        if filtros.get('processo'):
            query += " AND p.processo ILIKE %s"; params.append(f"%{filtros['processo']}%")
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(b.created_at) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])

        query += " ORDER BY b.created_at DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except: return []

    def buscar_detalhes_os(self, id_banco):
        query = """
            SELECT numero, TO_CHAR(data_criacao, 'DD/MM/YYYY HH24:MI'), tipo_evento, processo_adm, 
                   empresas_text, solicitante, endereco, 
                   horario_inicio, horario_fim, linhas_text, evento, 
                   nome_corrida, km_impactado, tipo_obra, responsavel
            FROM siga.ordens_servico WHERE id = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_banco,))
                    row = cursor.fetchone()
                    if row:
                        colunas = ["Nº OS", "Data Criação", "Tipo", "Processo", "Empresas", "Solicitante", 
                                   "Endereço", "Hr Início", "Hr Final", "Linhas", "Evento", 
                                   "Nome Corrida", "KM", "Tipo Obra", "Criado por"]
                        return dict(zip(colunas, row))
        except: pass
        return None

    def buscar_detalhes_parecer(self, id_banco):
        query = """
            SELECT b.numero_parecer_ano, TO_CHAR(b.created_at, 'DD/MM/YYYY HH24:MI'), p.tipo_parecer, 
                   p.processo, p.assunto, p.evento, p.data_evento, p.periodo, p.endereco, 
                   p.solicitante, p.linhas_afetadas, p.motivo_indeferimento, u.nome_completo
            FROM siga.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id WHERE p.id = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_banco,))
                    row = cursor.fetchone()
                    if row:
                        colunas = ["Nº Parecer", "Data Criação", "Decisão", "Processo", "Assunto", 
                                   "Evento", "Data Evento", "Período", "Endereço", "Solicitante", 
                                   "Linhas Desvio", "Motivo", "Criado por"]
                        return dict(zip(colunas, row))
        except: pass
        return None

    def excluir_e_logar(self, id_banco, tipo_relatorio, motivo, excluido_por):
        modulo = "OS_ITINERARIO" if tipo_relatorio == "OS" else "PARECER_ITINERARIO"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if tipo_relatorio == "OS":
                        cur.execute("SELECT numero, caminho_arquivo, row_to_json(s) FROM siga.ordens_servico s WHERE id = %s", (id_banco,))
                        linha = cur.fetchone()
                        if not linha: return False, "OS não encontrada."
                        numero, caminho, dados_json = linha
                        cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por, data_exclusao) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (modulo, numero, json.dumps(dados_json), caminho, motivo, excluido_por))
                        cur.execute("DELETE FROM siga.ordens_servico WHERE id = %s", (id_banco,))
                    else:
                        cur.execute("SELECT b.numero_parecer_ano, p.caminho_arquivo, row_to_json(p) FROM siga.pareceres p JOIN common.pareceres_base b ON p.id = b.id WHERE p.id = %s", (id_banco,))
                        linha = cur.fetchone()
                        if not linha: return False, "Parecer não encontrado."
                        numero, caminho, dados_json = linha
                        cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por, data_exclusao) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (modulo, numero, json.dumps(dados_json), caminho, motivo, excluido_por))
                        cur.execute("DELETE FROM siga.pareceres WHERE id = %s", (id_banco,))
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (id_banco,))
            return True, f"{tipo_relatorio} excluído com sucesso!"
        except Exception as e: return False, f"Erro ao excluir: {e}"