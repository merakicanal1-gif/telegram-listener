from telethon.tl.types import Channel, Chat, User


async def build_payload(client, event):
    sender = await event.get_sender()
    chat = await event.get_chat()

    # Descobre o tipo do chat
    chat_type = "unknown"

    if isinstance(chat, Channel):
        if getattr(chat, "broadcast", False):
            chat_type = "channel"
        elif getattr(chat, "megagroup", False):
            chat_type = "supergroup"
        else:
            chat_type = "group"

    elif isinstance(chat, Chat):
        chat_type = "group"

    elif isinstance(chat, User):
        chat_type = "private"

    payload = {
        "message": {
            "id": event.id,
            "text": event.raw_text,
            "date": event.date.isoformat(),
            "edit_date": event.edit_date.isoformat() if event.edit_date else None,
            "has_text": bool(event.raw_text),
            "has_media": event.media is not None,
        },

        "chat": {
            "id": event.chat_id,
            "title": getattr(chat, "title", None),
            "username": getattr(chat, "username", None),
            "type": chat_type,
            "is_private": chat_type == "private",
            "is_group": chat_type == "group",
            "is_supergroup": chat_type == "supergroup",
            "is_channel": chat_type == "channel",
        },

        "sender": {
            "id": getattr(sender, "id", None),
            "first_name": getattr(sender, "first_name", None),
            "last_name": getattr(sender, "last_name", None),
            "username": getattr(sender, "username", None),
            "phone": getattr(sender, "phone", None),
            "is_bot": getattr(sender, "bot", False),
            "is_verified": getattr(sender, "verified", False),
            "is_premium": getattr(sender, "premium", False),
        }
    }

    return payload
