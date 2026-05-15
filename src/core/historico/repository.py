from config.database import get_db_connection

class HistoricoRepository:
    def buscar_historico(self, filtros):
        # MODIFICAÇÃO CRÍTICA: 
        # Uso do LEFT JOIN com common.usuarios para converter 'excluido_por_id' no 'nome_completo'
        query = """
            SELECT l.modulo, 
                   l.numero, 
                   l.motivo, 
                   u.nome_completo AS excluido_por, 
                   TO_CHAR(l.data_exclusao, 'DD/MM/YYYY HH24:MI') AS data_formatada, 
                   l.dados 
            FROM common.lixeira l
            LEFT JOIN common.usuarios u ON l.excluido_por_id = u.id
            WHERE 1=1
        """
        params = []
        
        # O uso de ALIAS (l. e u.) impede ambiguidade no banco
        if filtros.get("modulo") and filtros["modulo"] != "Todos":
            query += " AND l.modulo = %s"
            params.append(filtros["modulo"].upper())
            
        if filtros.get("numero"):
            query += " AND l.numero = %s"
            params.append(int(filtros["numero"]))
            
        # MODIFICAÇÃO: A busca agora acontece no nome do usuário e não na lixeira diretamente
        if filtros.get("excluido_por"):
            query += " AND u.nome_completo ILIKE %s"
            params.append(f"%{filtros['excluido_por']}%")
            
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(l.data_exclusao) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])
            
        query += " ORDER BY l.data_exclusao DESC"
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    # Retornamos as tuplas exatamente na ordem que a View espera
                    return cur.fetchall()
        except Exception as e:
            print(f"[LOG DB] Erro na Auditoria/Lixeira: {e}")
            return []