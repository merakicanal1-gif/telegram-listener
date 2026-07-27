import os
from telethon import TelegramClient
from app.config import SESSION_NAME, API_ID, API_HASH
from app.logger import logger

def get_client() -> TelegramClient:
    """Retorna uma nova instância do TelegramClient sem conectar, garantindo que o diretório pai existe."""
    session_dir = os.path.dirname(SESSION_NAME)
    if session_dir:
        os.makedirs(session_dir, exist_ok=True)
    return TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def init_client(client: TelegramClient) -> None:
    """
    Conecta o cliente e verifica se a sessão está autorizada.
    Se a sessão não existir ou não for válida, lança exceções simples para encerramento.
    """
    session_file = f"{SESSION_NAME}.session"
    
    # 1. Verifica se o arquivo de sessão existe
    if not os.path.exists(session_file):
        raise FileNotFoundError(f"Arquivo de sessão não encontrado em {session_file}")
        
    logger.info("✔ Sessão encontrada")
    logger.info("Conectando ao Telegram...")
    
    await client.connect()
    
    # 2. Verifica se a sessão está de fato autorizada
    if not await client.is_user_authorized():
        raise RuntimeError(
            f"Sessão em '{session_file}' não está autorizada no Telegram. Faça login localmente primeiro."
        )
        
    logger.info("✔ Conectado ao Telegram")
    me = await client.get_me()
    logger.info(f"✔ Conectado como: {me.first_name} ({me.id})")
