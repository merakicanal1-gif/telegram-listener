import asyncio
import datetime
import logging
import os
import sqlite3
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Carrega configurações do .env se existir
load_dotenv()

# Configurações do Servidor de Upload
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
DB_PATH = os.getenv("DB_PATH", "media.db")
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}")
DEFAULT_TTL = int(os.getenv("DEFAULT_TTL", "86400"))  # 24 horas padrão
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", "300"))  # 5 minutos padrão
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configura logs
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("upload-server")

# Garante que o diretório de uploads existe
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    """Inicializa a tabela SQLite de controle das mídias temporárias."""
    logger.info(f"Inicializando banco de dados SQLite: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT UNIQUE,
                file_path TEXT,
                mime_type TEXT,
                size INTEGER,
                created_at TEXT,
                expires_at TEXT,
                ttl INTEGER
            )
        """)
        conn.commit()

async def cleanup_worker():
    """Loop em segundo plano para limpar arquivos expirados."""
    logger.info(f"Worker de limpeza iniciado. Verificações a cada {CLEANUP_INTERVAL} segundos.")
    while True:
        try:
            now_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Seleciona arquivos expirados
                cursor.execute(
                    "SELECT file_name, file_path FROM media WHERE expires_at < ?",
                    (now_str,)
                )
                expired_files = cursor.fetchall()
                
                if expired_files:
                    logger.info(f"Limpeza: {len(expired_files)} arquivos expirados encontrados.")
                    for file in expired_files:
                        path = file["file_path"]
                        name = file["file_name"]
                        
                        # Remove o arquivo do disco
                        try:
                            if os.path.exists(path):
                                os.remove(path)
                                logger.info(f"Arquivo deletado do disco: {path}")
                            else:
                                logger.warning(f"Arquivo físico não encontrado para deletar: {path}")
                        except Exception as file_err:
                            logger.error(f"Falha ao apagar arquivo físico {path}: {file_err}")
                        
                        # Remove o registro do banco
                        cursor.execute("DELETE FROM media WHERE file_name = ?", (name,))
                    
                    conn.commit()
                    logger.info("Limpeza de expirados concluída com sucesso.")
                    
        except Exception as err:
            logger.exception(f"Erro no ciclo do worker de limpeza: {err}")
            
        await asyncio.sleep(CLEANUP_INTERVAL)

app = FastAPI(title="Servidor de Upload de Mídias Temporárias")

@app.on_event("startup")
async def startup_event():
    init_db()
    # Inicia o worker de limpeza em segundo plano
    asyncio.create_task(cleanup_worker())

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), ttl: int = None):
    """
    Recebe um arquivo via POST multipart/form-data.
    Opcionalmente recebe um TTL específico em segundos (passado como parâmetro da query).
    """
    try:
        ttl_seconds = ttl if ttl is not None else DEFAULT_TTL
        
        # Gera nome único para o arquivo
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Salva o arquivo no disco
        size = 0
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(65536):
                buffer.write(chunk)
                size += len(chunk)
                
        # Datas de criação e expiração no formato ISO 8601 UTC (terminando com Z)
        now = datetime.datetime.now(datetime.timezone.utc)
        created_at = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        expires_at = (now + datetime.timedelta(seconds=ttl_seconds)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Registra no banco
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO media (file_name, file_path, mime_type, size, created_at, expires_at, ttl)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (unique_filename, file_path, file.content_type, size, created_at, expires_at, ttl_seconds)
            )
            conn.commit()
            
        public_url = f"{BASE_URL.rstrip('/')}/uploads/{unique_filename}"
        
        logger.info(f"Arquivo recebido: {unique_filename} ({size} bytes) | TTL: {ttl_seconds}s")
        
        return {
            "url": public_url,
            "file_name": unique_filename,
            "mime_type": file.content_type,
            "size": size,
            "created_at": created_at,
            "expires_at": expires_at,
            "ttl": ttl_seconds
        }
        
    except Exception as e:
        logger.exception(f"Erro no processamento do upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento de mídia: {str(e)}")

# Monta o diretório estático para servir os uploads publicamente
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
