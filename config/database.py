# config/database.py
import psycopg2
from config import config_db  # Importa diretamente as configurações mapeadas

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=config_db.DB_HOST,
            database=config_db.DB_NAME,
            user=config_db.DB_USER,
            password=config_db.DB_PASS,
            port=config_db.DB_PORT
        )
        return conn
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha ao conectar ao banco de dados: {e}")
        raise e