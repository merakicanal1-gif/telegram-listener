import requests

from app.config import WEBHOOK_URL


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
        print(f"Erro ao enviar webhook: {e}")
        return False
