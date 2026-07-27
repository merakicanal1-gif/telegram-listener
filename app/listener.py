from app.client import get_client, init_client
from app.handlers import register_handlers
from app.logger import logger

async def start_listener() -> None:
    """Orquestra a conexão, validação e execução do listener."""
    logger.info("✔ Configuração carregada")
    
    # Cria o cliente localmente
    client = get_client()
    
    # Conecta e valida a sessão
    await init_client(client)
    
    # Registra os handlers de eventos
    await register_handlers(client)
    
    logger.info("✔ Escutando mensagens...")
    
    # Mantém o processo rodando até desconectar
    await client.run_until_disconnected()
