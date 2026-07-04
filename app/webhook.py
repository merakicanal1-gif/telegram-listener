import httpx

from app.config import WEBHOOK_URL, REQUEST_TIMEOUT


async def send_to_webhook(payload):
    """
    Envia o payload para o webhook do n8n.
    """

    try:

        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT
        ) as client:

            response = await client.post(
                WEBHOOK_URL,
                json=payload,
            )

        response.raise_for_status()

        return True

    except Exception as e:

        print(f"Erro ao enviar webhook: {e}")

        return False
