import asyncio
from app.listener import start_listener
from app.logger import logger


async def main():
    while True:
        try:
            await start_listener()
        except Exception as e:
            logger.exception(f"Erro no listener: {e}")
            logger.info("Reconectando em 10 segundos...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
