import mimetypes

from app.upload import upload_bytes


async def extract_media(client, event):
    """
    Extrai a mídia da mensagem utilizando memória RAM.
    """

    if event.media is None:
        return {
            "exists": False,
            "type": None,
            "url": None,
            "file_name": None,
            "mime_type": None,
            "size": None,
        }

    file_bytes = await client.download_media(
        event.media,
        file=bytes,
    )

    if file_bytes is None:
        return {
            "exists": False,
            "type": None,
            "url": None,
            "file_name": None,
            "mime_type": None,
            "size": None,
        }

    filename = getattr(event.file, "name", None) or f"{event.id}"

    mime_type = (
        getattr(event.file, "mime_type", None)
        or mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )

    upload = await upload_bytes(
        file_bytes=file_bytes,
        filename=filename,
        mime_type=mime_type,
    )

    return {
        "exists": True,
        "type": type(event.media).__name__,
        "url": upload.get("url"),
        "file_name": upload.get("file_name"),
        "mime_type": mime_type,
        "size": len(file_bytes),
    }
