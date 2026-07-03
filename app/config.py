import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

SESSION_NAME = os.getenv("SESSION_NAME", "telegram_session")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 10))

MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))

RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))
