import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "9173258162:AAH1a8lIUzZj9PPYidWLrsyAJzpO5Ep7LH8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6I0OzRi1TIZ8btccXxBzyBHQoRBvK7ARn_qEkasy1EwIw")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5017047967"))
PROXY_URL = os.getenv("PROXY_URL", "") # Masalan: socks5://127.0.0.1:1080 yoki http://ip:port


DB_FILE = os.path.join(os.path.dirname(__file__), "hisobchi.db")
RECEIPTS_DIR = os.path.join(os.path.dirname(__file__), "receipts")
os.makedirs(RECEIPTS_DIR, exist_ok=True)
