import mimetypes
import os
import tempfile

import requests


UPLOAD_URL = "https://upload.mymaquina.online/upload"


async def extract_media(client, event):

    if event.media is None:
        return {
            "exists": False,
            "type": None,
            "url": None,
            "file_name": None,
            "mime_type": None,
            "size": None,
        }

    fd, temp_path = tempfile.mkstemp()
    os.close(fd)

    try:

        downloaded = await client.download_media(
            event.media,
            file=temp_path,
        )

        if downloaded is None:
            return {
                "exists": False,
                "type": None,
                "url": None,
                "file_name": None,
                "mime_type": None,
                "size": None,
            }

        mime_type = (
            mimetypes.guess_type(downloaded)[0]
            or "application/octet-stream"
        )

        with open(downloaded, "rb") as f:

            response = requests.post(
                UPLOAD_URL,
                files={
                    "image": (
                        os.path.basename(downloaded),
                        f,
                        mime_type,
                    )
                },
                timeout=60,
            )

        response.raise_for_status()

        result = response.json()

        return {
            "exists": True,
            "type": type(event.media).__name__,
            "url": result.get("url"),
            "file_name": result.get("fileName"),
            "mime_type": mime_type,
            "size": os.path.getsize(downloaded),
        }

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)
