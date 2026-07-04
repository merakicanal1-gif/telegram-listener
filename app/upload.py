from app.config import UPLOAD_URL
from app.http_client import client


async def upload_file(file_path: str):
    """
    Faz upload de um arquivo existente em disco para a API
    e retorna os dados da mídia enviada.

    Mantido por compatibilidade com implementações antigas.
    """

    with open(file_path, "rb") as file:

        response = await client.post(
            UPLOAD_URL,
            files={
                "image": file,
            },
        )

    response.raise_for_status()

    data = response.json()

    return {
        "url": data.get("url"),
        "file_name": data.get("fileName"),
    }


async def upload_bytes(
    file_bytes: bytes,
    filename: str,
    mime_type: str,
):
    """
    Faz upload de um arquivo que já está carregado em memória (RAM),
    sem necessidade de gravá-lo temporariamente em disco.

    Esta função será utilizada pelo novo pipeline assíncrono de mídia.
    """

    response = await client.post(
        UPLOAD_URL,
        files={
            "image": (
                filename,
                file_bytes,
                mime_type,
            ),
        },
    )

    response.raise_for_status()

    data = response.json()

    return {
        "url": data.get("url"),
        "file_name": data.get("fileName"),
    }
