from telethon.sync import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

with TelegramClient("telegram_session", api_id, api_hash) as client:
    print("\nSessão criada com sucesso!")
    print("Usuário:", client.get_me().first_name)
