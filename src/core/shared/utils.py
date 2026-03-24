# shared/utils.py
import sys
import os
import unicodedata

def resource_path(relative_path):
    """
    Retorna o caminho absoluto do recurso, funcionando tanto no desenvolvimento
    quanto no executável criado pelo PyInstaller.
    """
    try:
        # Se estiver rodando como .exe do PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        # Se estiver rodando como script normal (dev)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def normalizar_texto(texto):
    """
    Remove acentos e deixa em caixa alta. 
    Excelente para padronizar textos antes de salvar no banco de dados ou 
    para cruzar dados em gráficos no Dashboard.
    """
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).upper().strip()