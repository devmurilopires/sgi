from config.database import get_db_connection

class HistoricoService:
    def buscar_historico(self, filtros):
        # Monta a query SQL com base nos filtros fornecidos
        query = "SELECT modulo, numero, motivo, excluido_por, TO_CHAR(data_exclusao, 'DD/MM/YYYY HH24:MI'), dados FROM common.lixeira WHERE 1=1"
        params = []
        
        if filtros.get("modulo") and filtros["modulo"] != "Todos":
            query += " AND modulo = %s"
            params.append(filtros["modulo"].upper())
        if filtros.get("numero"):
            query += " AND numero = %s"
            params.append(int(filtros["numero"]))
        if filtros.get("excluido_por"):
            query += " AND excluido_por ILIKE %s"
            params.append(f"%{filtros['excluido_por']}%")
        if filtros.get('data_inicio') and filtros.get('data_fim'):
            query += " AND DATE(data_exclusao) BETWEEN %s AND %s"
            params.extend([filtros['data_inicio'], filtros['data_fim']])
            
        query += " ORDER BY data_exclusao DESC"
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.fetchall()
        except Exception as e:
            print(f"Erro na Lixeira: {e}")
            return []