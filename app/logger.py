import logging
import os
from app.config import LOG_LEVEL, LOG_TO_FILE

# Define o nível de log
level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

handlers = [logging.StreamHandler()]

if LOG_TO_FILE:
    os.makedirs("logs", exist_ok=True)
    handlers.append(logging.FileHandler("logs/listener.log"))

logging.basicConfig(
    level=level,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=handlers
)

logger = logging.getLogger("telegram-listener")
