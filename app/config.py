import os
from dotenv import load_dotenv

load_dotenv()

# Validar credenciais obrigatórias do Telegram
api_id_raw = os.getenv("API_ID")
if not api_id_raw:
    raise ValueError("A variável de ambiente API_ID é obrigatória.")
try:
    API_ID = int(api_id_raw)
except ValueError:
    raise ValueError("A variável de ambiente API_ID deve ser um número inteiro válido.")

API_HASH = os.getenv("API_HASH")
if not API_HASH:
    raise ValueError("A variável de ambiente API_HASH é obrigatória.")

# Caminho da sessão (padrão: sessions/telegram)
SESSION_NAME = os.getenv("SESSION_NAME", "sessions/telegram")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

UPLOAD_URL = os.getenv("UPLOAD_URL", "http://localhost:8000/upload")
MEDIA_UPLOAD_TIMEOUT = int(os.getenv("MEDIA_UPLOAD_TIMEOUT", 60))
DEFAULT_TTL = int(os.getenv("DEFAULT_TTL", 86400))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() in ("true", "1", "yes")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 10))

MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))

RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))
