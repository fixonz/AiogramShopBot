from dotenv import load_dotenv
import os
from models.currency import Currency
from ngrok_executor import start_ngrok

load_dotenv()

WEBHOOK_HOST = start_ngrok()
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH")
WEBAPP_HOST = os.environ.get("WEBAPP_HOST")
WEBAPP_PORT = int(os.environ.get("WEBAPP_PORT"))
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
TOKEN = os.environ.get("TOKEN")
ADMIN_ID_LIST = os.environ.get("ADMIN_ID_LIST").split(',')
ADMIN_ID_LIST = [int(admin_id) for admin_id in ADMIN_ID_LIST]
SUPPORT_LINK = os.environ.get("SUPPORT_LINK")
DB_ENCRYPTION = os.environ.get("DB_ENCRYPTION", False) == 'true'
DB_NAME = os.environ.get("DB_NAME")
DB_PASS = os.environ.get("DB_PASS")
PAGE_ENTRIES = int(os.environ.get("PAGE_ENTRIES"))
BOT_LANGUAGE = os.environ.get("BOT_LANGUAGE")
MULTIBOT = os.environ.get("MULTIBOT", False) == 'true'
CURRENCY = Currency.from_string(os.environ.get("CURRENCY"))
GETGEOAPI_KEY = os.environ.get("GETGEOAPI_KEY")