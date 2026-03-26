import json
from config.database import get_db_connection

class RelatorioQuadroHorarioRepository:
    def buscar_pareceres(self, filtros):
        query = """
            SELECT p.id, b.numero_parecer_ano, p.processo, b.tipo_parecer, p.assunto, 
                   p.data_evento, p.solicitante, p.linhas_afetadas, u.nome_completo, p.caminho_arquivo
            FROM spr.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id WHERE 1=1
        """
        params = []
        if filtros.get('numero_parecer'):
            query += " AND b.numero_parecer_ano = %s"; params.append(int(filtros['numero_parecer']))
        if filtros.get('tipo') and filtros['tipo'] != "Todos":
            query += " AND b.tipo_parecer = %s"; params.append(filtros['tipo'].upper())
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

    def buscar_pesquisas(self, filtros):
        query = """
            SELECT id, titulo, tipo_pesquisa, TO_CHAR(created_at, 'DD/MM/YYYY HH24:MI'), 
                   criado_por, resultado_json
            FROM spr.pesquisas WHERE 1=1
        """
        params = []
        if filtros.get('titulo'):
            query += " AND titulo ILIKE %s"; params.append(f"%{filtros['titulo']}%")
        if filtros.get('tipo') and filtros['tipo'] != "Todos":
            query += " AND tipo_pesquisa ILIKE %s"; params.append(f"%{filtros['tipo']}%")
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(created_at) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])
            
        query += " ORDER BY created_at DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except: return []

    def buscar_detalhes_parecer(self, id_banco):
        query = """
            SELECT b.numero_parecer_ano, TO_CHAR(b.created_at, 'DD/MM/YYYY HH24:MI'), b.tipo_parecer, 
                   p.processo, p.assunto, p.solicitacao, p.evento, p.data_evento, p.solicitante, 
                   p.linhas_afetadas, p.motivo_indeferimento, u.nome_completo
            FROM spr.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id WHERE p.id = %s
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (id_banco,))
                    row = cursor.fetchone()
                    if row:
                        colunas = ["Nº Parecer", "Data Creación", "Decisión", "Proceso", "Asunto", 
                                   "Solicitude", "Evento", "Data Evento", "Solicitante", 
                                   "Liñas", "Motivo", "Creado por"]
                        return dict(zip(colunas, row))
        except: pass
        return None

    def excluir_e_logar(self, id_banco, tipo_relatorio, motivo, excluido_por):
        modulo = "PESQUISA_SPR" if tipo_relatorio == "PESQUISA" else "PARECER_SPR"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if tipo_relatorio == "PESQUISA":
                        cur.execute("SELECT titulo, '', row_to_json(p) FROM spr.pesquisas p WHERE id = %s", (id_banco,))
                        linha = cur.fetchone()
                        if not linha: return False, "Pescuda non atopada."
                        numero, caminho, dados_json = linha
                        cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por, data_exclusao) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (modulo, id_banco, json.dumps(dados_json), caminho, motivo, excluido_por))
                        cur.execute("DELETE FROM spr.pesquisas WHERE id = %s", (id_banco,))
                    else:
                        cur.execute("SELECT b.numero_parecer_ano, p.caminho_arquivo, row_to_json(p) FROM spr.pareceres p JOIN common.pareceres_base b ON p.id = b.id WHERE p.id = %s", (id_banco,))
                        linha = cur.fetchone()
                        if not linha: return False, "Ditame non atopado."
                        numero, caminho, dados_json = linha
                        cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por, data_exclusao) VALUES (%s, %s, %s, %s, %s, %s, NOW())", (modulo, numero, json.dumps(dados_json), caminho, motivo, excluido_por))
                        cur.execute("DELETE FROM spr.pareceres WHERE id = %s", (id_banco,))
                        cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (id_banco,))
            return True, f"{tipo_relatorio} eliminado con éxito!"
        except Exception as e: return False, f"Erro ao eliminar: {e}"