import os
import sys
from telethon.sync import TelegramClient
from dotenv import load_dotenv

load_dotenv()

# Validar credenciais obrigatórias
api_id_raw = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

if not api_id_raw or not api_hash:
    print("Erro: API_ID e API_HASH devem estar definidos no arquivo .env!")
    sys.exit(1)

try:
    api_id = int(api_id_raw)
except ValueError:
    print("Erro: API_ID deve ser um número inteiro válido!")
    sys.exit(1)

# Caminho da sessão
session_name = os.getenv("SESSION_NAME", "sessions/telegram")
session_file = f"{session_name}.session"

# Garante que o diretório pai existe
session_dir = os.path.dirname(session_name)
if session_dir:
    os.makedirs(session_dir, exist_ok=True)

print(f"Iniciando login interativo para criar o arquivo de sessão em: {session_file}")
print("Siga as instruções do Telegram no terminal...\n")

try:
    with TelegramClient(session_name, api_id, api_hash) as client:
        me = client.get_me()
        if me:
            print("\n✔ Sessão criada com sucesso!")
            print(f"✔ Conectado como: {me.first_name} (@{me.username or ''})")
            print(f"✔ Arquivo de sessão salvo em: {session_file}")
            print("\nAgora você pode usar esta pasta 'sessions/' no Docker / EasyPanel.")
        else:
            print("\n✘ Falha ao obter informações do usuário.")
except Exception as e:
    print(f"\n✘ Erro ao criar a sessão: {e}")
    sys.exit(1)
