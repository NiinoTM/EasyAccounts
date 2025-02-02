import os
import sqlite3
from datetime import datetime
from config.settings import DATABASE_PATH

# Configurações
BACKUP_DIR = "data/backups"  # Pasta onde os backups serão armazenados
MAX_BACKUPS = 20  # Número máximo de backups a serem mantidos

def ensure_backup_dir():
    """Garante que a pasta de backups existe."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def get_backup_files():
    """Retorna a lista de arquivos de backup na pasta, ordenados por data de criação."""
    if not os.path.exists(BACKUP_DIR):
        return []
    files = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
    files.sort(key=os.path.getmtime)  # Ordena por data de modificação
    return files

def create_backup():
    """Cria um backup da database em formato SQLite .db."""
    ensure_backup_dir()
    
    # Nome do arquivo de backup com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.db")
    
    # Conecta ao banco de dados
    source_conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # Cria o arquivo de backup
        with sqlite3.connect(backup_file) as backup_conn:
            source_conn.backup(backup_conn)
        print(f"Backup criado com sucesso: {backup_file}")
    finally:
        source_conn.close()
    
    # Remove backups antigos se necessário
    manage_backups()

def manage_backups():
    """Remove backups antigos se o número de backups exceder MAX_BACKUPS."""
    backup_files = get_backup_files()
    while len(backup_files) > MAX_BACKUPS:
        oldest_file = backup_files.pop(0)  # Remove o arquivo mais antigo
        os.remove(oldest_file)
        print(f"Backup removido: {oldest_file}")

def import_from_backup(backup_file):
    """Substitui toda a database pelo backup contido no arquivo."""
    if not os.path.exists(backup_file):
        print(f"Arquivo de backup não encontrado: {backup_file}")
        return
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        # Cria o arquivo de backup como fonte
        with sqlite3.connect(backup_file) as backup_conn:
            backup_conn.backup(conn)
        print(f"Database restaurada com sucesso a partir de {backup_file}!")
    finally:
        conn.close()
