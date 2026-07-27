from telethon import events
from app.logger import logger
from app.payload import build_payload
from app.webhook import send_to_webhook

async def register_handlers(client) -> None:
    """Registra os manipuladores de eventos no cliente do Telethon."""
    
    @client.on(events.NewMessage)
    async def new_message(event):
        try:
            payload = await build_payload(client, event)
            
            logger.info(
                f"✔ Nova mensagem recebida: chat={payload['chat']['id']} | sender={payload['sender']['id']}"
            )
            
            send_to_webhook(payload)
        except Exception as e:
            logger.error(f"Erro ao processar ou enviar mensagem: {e}")
