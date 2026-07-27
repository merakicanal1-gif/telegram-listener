import asyncio
import sys
from app.listener import start_listener
from app.client import get_client, init_client
from app.logger import logger

async def check_session():
    """Valida se a configuração e a sessão estão corretas sem iniciar o listener."""
    try:
        client = get_client()
        await init_client(client)
        await client.disconnect()
        logger.info("✔ Verificação concluída: configuração e sessão estão válidas.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"✘ Erro na verificação: {e}")
        logger.error("✘ Encerrando aplicação")
        sys.exit(1)

async def run_listener():
    """Inicia o listener e encerra com código 1 em caso de qualquer falha."""
    try:
        await start_listener()
    except Exception as e:
        logger.error(f"✘ Erro fatal: {e}")
        logger.error("✘ Encerrando aplicação")
        sys.exit(1)

def main():
    if "--check" in sys.argv:
        asyncio.run(check_session())
    else:
        asyncio.run(run_listener())

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Aplicação encerrada pelo usuário.")
