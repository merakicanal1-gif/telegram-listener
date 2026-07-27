import asyncio
import datetime
import logging
import os
import sqlite3
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
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
    # Garante que o diretório pai do banco existe
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
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

@app.get("/")
async def read_root():
    return {"status": "online", "message": "Bananou Upload Online"}

@app.on_event("startup")
async def startup_event():
    init_db()
    # Inicia o worker de limpeza em segundo plano
    asyncio.create_task(cleanup_worker())

@app.post("/upload")
async def upload_file(
    image: UploadFile = File(None),
    file: UploadFile = File(None),
    ttl_seconds: str = Form(None),
    ttl: str = Form(None),
    ttl_seconds_query: str = Query(None, alias="ttl_seconds"),
    ttl_query: str = Query(None, alias="ttl"),
):
    """
    Recebe um arquivo via POST multipart/form-data.
    Suporta campos de arquivo 'image' e 'file'.
    Opcionalmente recebe um TTL específico em segundos (form-data ou query parameter).
    """
    try:
        # Determina qual arquivo foi enviado (priorizando 'image')
        uploaded_file = image if image is not None else file
        if uploaded_file is None or not uploaded_file.filename:
            raise HTTPException(
                status_code=400,
                detail="Nenhum arquivo enviado. Use o campo 'image' ou 'file' do multipart/form-data."
            )
            
        # Determina o valor do TTL a partir do form ou query params
        ttl_val = None
        if ttl_seconds is not None:
            ttl_val = ttl_seconds
        elif ttl_seconds_query is not None:
            ttl_val = ttl_seconds_query
        elif ttl is not None:
            ttl_val = ttl
        elif ttl_query is not None:
            ttl_val = ttl_query

        # Valida o TTL se fornecido
        actual_ttl = None
        if ttl_val is not None:
            try:
                if isinstance(ttl_val, str):
                    if not ttl_val.strip():
                        raise ValueError("TTL não pode ser vazio")
                    actual_ttl = int(ttl_val)
                else:
                    actual_ttl = int(ttl_val)
                
                if actual_ttl <= 0:
                    raise ValueError("TTL deve ser maior que zero")
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail="O valor de 'ttl_seconds' é inválido. Deve ser um número inteiro maior que zero."
                )

        # Gera nome único para o arquivo
        ext = os.path.splitext(uploaded_file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Salva o arquivo no disco
        size = 0
        with open(file_path, "wb") as buffer:
            while chunk := await uploaded_file.read(65536):
                buffer.write(chunk)
                size += len(chunk)
                
        # Datas de criação e expiração no formato ISO 8601 UTC (terminando com Z)
        now = datetime.datetime.now(datetime.timezone.utc)
        created_at = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        if actual_ttl is not None:
            expires_at = (now + datetime.timedelta(seconds=actual_ttl)).strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            expires_at = None
        
        # Registra no banco
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO media (file_name, file_path, mime_type, size, created_at, expires_at, ttl)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (unique_filename, file_path, uploaded_file.content_type, size, created_at, expires_at, actual_ttl)
            )
            conn.commit()
            
        # Constrói a URL pública usando a pasta de uploads de forma dinâmica
        upload_path_segment = UPLOAD_DIR.strip('/')
        public_url = f"{BASE_URL.rstrip('/')}/{upload_path_segment}/{unique_filename}"
        
        logger.info(f"Arquivo recebido: {unique_filename} ({size} bytes) | TTL: {actual_ttl}s")
        
        return {
            "url": public_url,
            "file_name": unique_filename,
            "fileName": unique_filename,  # Mantém compatibilidade com camelCase
            "mime_type": uploaded_file.content_type,
            "mimeType": uploaded_file.content_type,  # Mantém compatibilidade com camelCase
            "size": size,
            "created_at": created_at,
            "createdAt": created_at,  # Mantém compatibilidade com camelCase
            "expires_at": expires_at,
            "expiresAt": expires_at,  # Mantém compatibilidade com camelCase
            "ttl": actual_ttl
        }
        
    except HTTPException:
        # Repassa exceções HTTP declaradas diretamente (como o erro 400 do TTL ou arquivo)
        raise
    except Exception as e:
        logger.exception(f"Erro no processamento do upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento de mídia: {str(e)}")

# Monta o diretório estático de forma dinâmica com o nome da pasta de uploads
upload_path_segment = UPLOAD_DIR.strip('/')
app.mount(f"/{upload_path_segment}", StaticFiles(directory=UPLOAD_DIR), name=upload_path_segment)
