import mimetypes
import os
import tempfile
import requests

from app.config import UPLOAD_URL, MEDIA_UPLOAD_TIMEOUT, DEFAULT_TTL
from app.logger import logger


async def extract_media(client, event):
    if event.media is None:
        return {
            "exists": False,
            "type": None,
            "url": None,
            "file_name": None,
            "mime_type": None,
            "size": None,
            "created_at": None,
            "expires_at": None,
            "ttl": None,
        }

    fd, temp_path = tempfile.mkstemp()
    os.close(fd)

    try:
        logger.info("Iniciando download da mídia do Telegram...")
        downloaded = await client.download_media(
            event.media,
            file=temp_path,
        )

        if downloaded is None:
            raise Exception("O cliente do Telegram retornou None ao baixar o arquivo.")

        # Tenta obter o MIME type diretamente do objeto de arquivo do Telethon
        mime_type = getattr(event.file, "mime_type", None)
        if not mime_type or mime_type == "application/octet-stream":
            mime_type = mimetypes.guess_type(downloaded)[0] or "application/octet-stream"

        # Se for do tipo foto (MessageMediaPhoto) e o mime for genérico, assume image/jpeg
        if "photo" in type(event.media).__name__.lower() and mime_type == "application/octet-stream":
            mime_type = "image/jpeg"

        # Obtém a extensão correta
        ext = getattr(event.file, "ext", None)
        if not ext:
            ext = mimetypes.guess_extension(mime_type) or ".jpg"
            
        filename_to_send = f"{os.path.basename(downloaded)}{ext}"

        logger.info(f"Fazendo upload para o servidor temporário: {UPLOAD_URL}")
        with open(downloaded, "rb") as f:
            response = requests.post(
                UPLOAD_URL,
                files={
                    "image": (
                        filename_to_send,
                        f,
                        mime_type,
                    )
                },
                data={
                    "ttl_seconds": DEFAULT_TTL
                },
                timeout=MEDIA_UPLOAD_TIMEOUT,
            )

        response.raise_for_status()
        result = response.json()

        return {
            "exists": True,
            "type": type(event.media).__name__,
            "url": result.get("url"),
            "file_name": result.get("file_name"),
            "mime_type": result.get("mime_type") or mime_type,
            "size": result.get("size") or os.path.getsize(downloaded),
            "created_at": result.get("created_at"),
            "expires_at": result.get("expires_at"),
            "ttl": result.get("ttl"),
        }

    except Exception as e:
        logger.error(f"Erro durante o processamento da mídia: {e}", exc_info=True)
        return {
            "exists": True,
            "type": type(event.media).__name__ if event.media else "UnknownMedia",
            "error": f"Falha no processamento/upload da mídia: {str(e)}",
            "url": None,
            "file_name": None,
            "mime_type": None,
            "size": None,
            "created_at": None,
            "expires_at": None,
            "ttl": None,
        }

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                logger.error(
                    f"Falha ao deletar arquivo temporário local {temp_path}: {cleanup_err}"
                )
