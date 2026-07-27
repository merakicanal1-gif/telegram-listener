import requests

from app.config import WEBHOOK_URL
from app.logger import logger


def send_to_webhook(payload):
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        return True

    except Exception as e:
        logger.error(f"Erro ao enviar webhook: {e}")
        return False
