from telethon import TelegramClient, events

from app.config import (
    API_ID,
    API_HASH,
    SESSION_NAME,
)

from app.logger import logger
from app.webhook import send_to_webhook
from app.payload import build_payload


client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH,
)


@client.on(events.NewMessage)
async def new_message(event):
    payload = await build_payload(client, event)

    logger.info(
        f"Nova mensagem recebida: chat={payload['chat']['id']} | sender={payload['sender']['id']}"
    )

    await send_to_webhook(payload)


async def start_listener():
    logger.info("Conectando ao Telegram...")

    await client.start()

    me = await client.get_me()

    logger.info(f"Conectado como: {me.first_name} ({me.id})")

    logger.info("Listener iniciado.")

    await client.run_until_disconnected()
