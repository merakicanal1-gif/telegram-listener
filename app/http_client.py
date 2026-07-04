import httpx

from app.config import REQUEST_TIMEOUT

client = httpx.AsyncClient(
    timeout=REQUEST_TIMEOUT
)
