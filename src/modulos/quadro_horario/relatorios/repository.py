import psycopg2
import json
from config.database import get_db_connection

class RelatorioQuadroHorarioRepository:
    def buscar_linhas(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT nome FROM common.linhas ORDER BY nome;")
                    return [r[0] for r in cur.fetchall()]
        except Exception as e: return []

    # --- PARECERES ---
    def buscar_pareceres(self, filtros):
        query = """
            SELECT p.id, b.numero_parecer_ano, b.tipo_parecer, p.processo, p.assunto, 
                   p.solicitante, p.evento, p.linhas_afetadas, p.data_evento, u.nome_completo, 
                   b.created_at, p.caminho_arquivo
            FROM spr.pareceres p
            JOIN common.pareceres_base b ON p.id = b.id
            LEFT JOIN common.usuarios u ON b.criado_por_id = u.id 
            WHERE 1=1
        """
        params = []
        if filtros.get('numero_parecer'):
            query += " AND b.numero_parecer_ano::text ILIKE %s"; params.append(f"%{filtros['numero_parecer']}%")
        if filtros.get('processo'):
            query += " AND p.processo ILIKE %s"; params.append(f"%{filtros['processo']}%")
        if filtros.get('tipo') and filtros['tipo'] != "Todos":
            query += " AND b.tipo_parecer ILIKE %s"; params.append(f"%{filtros['tipo']}%")
        if filtros.get('assunto') and filtros['assunto'] != "Todos":
            query += " AND p.assunto ILIKE %s"; params.append(f"%{filtros['assunto']}%")
        if filtros.get('evento') and filtros['evento'] != "Todos":
            query += " AND p.evento ILIKE %s"; params.append(f"%{filtros['evento']}%")
        if filtros.get('solicitante') and filtros['solicitante'] != "Todos":
            query += " AND p.solicitante ILIKE %s"; params.append(f"%{filtros['solicitante']}%")
        if filtros.get('linha'):
            query += " AND p.linhas_afetadas ILIKE %s"; params.append(f"%{filtros['linha']}%")
        if filtros.get('responsavel'):
            query += " AND u.nome_completo ILIKE %s"; params.append(f"%{filtros['responsavel']}%")
            
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(b.created_at) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])

        query += " ORDER BY b.created_at DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchall()
        except Exception as e: return []

    def excluir_e_logar_parecer(self, id_banco, motivo, excluido_por):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT b.numero_parecer_ano, p.caminho_arquivo, row_to_json(p) FROM spr.pareceres p JOIN common.pareceres_base b ON p.id = b.id WHERE p.id = %s", (id_banco,))
                    linha = cur.fetchone()
                    if not linha: return False, "Parecer não encontrado."
                    numero, caminho, dados_json = linha
                    cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por, data_exclusao) VALUES ('PARECER_SPR', %s, %s, %s, %s, %s, NOW())", (numero, json.dumps(dados_json), caminho, motivo, excluido_por))
                    cur.execute("DELETE FROM spr.pareceres WHERE id = %s", (id_banco,))
                    cur.execute("DELETE FROM common.pareceres_base WHERE id = %s", (id_banco,))
            return True, "Parecer excluído com sucesso!"
        except Exception as e: return False, f"Erro ao excluir Parecer: {e}"

    # --- PESQUISAS ---
    def buscar_pesquisas(self, filtros):
        query = """
            SELECT id, titulo, tipo_pesquisa, criado_por, created_at, resultado_json
            FROM spr.pesquisas WHERE 1=1
        """
        params = []
        if filtros.get('id'):
            query += " AND id::text ILIKE %s"; params.append(f"%{filtros['id']}%")
        if filtros.get('linha'):
            query += " AND titulo ILIKE %s"; params.append(f"%{filtros['linha']}%")
        if filtros.get('tipo') and filtros['tipo'] != "Todos":
            tipo_bd = "tempo" if "Tempo" in filtros['tipo'] else "demanda"
            query += " AND tipo_pesquisa ILIKE %s"; params.append(f"%{tipo_bd}%")
        if filtros.get('responsavel'):
            query += " AND criado_por ILIKE %s"; params.append(f"%{filtros['responsavel']}%")
            
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(created_at) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])

        query += " ORDER BY created_at DESC"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchall()
        except Exception as e: return []

    def excluir_e_logar_pesquisa(self, id_banco, motivo, excluido_por):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, row_to_json(p) FROM spr.pesquisas p WHERE id = %s", (id_banco,))
                    linha = cur.fetchone()
                    if not linha: return False, "Pesquisa não encontrada."
                    numero, dados_json = linha
                    cur.execute("INSERT INTO common.lixeira (modulo, numero, dados, caminho_original, motivo, excluido_por, data_exclusao) VALUES ('PESQUISA_SPR', %s, %s, %s, %s, %s, NOW())", (numero, json.dumps(dados_json), None, motivo, excluido_por))
                    cur.execute("DELETE FROM spr.pesquisas WHERE id = %s", (id_banco,))
            return True, "Pesquisa excluída com sucesso!"
        except Exception as e: return False, f"Erro ao excluir Pesquisa: {e}"