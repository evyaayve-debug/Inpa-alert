import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from bs4 import BeautifulSoup

SEEN_FILE = Path("seen.json")

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# 🔥 URL: tutti i bandi aperti della Liguria
INPA_URL = (
    "https://www.inpa.gov.it/bandi-e-avvisi/?"
    "text=&categoriaId=&regioneId=7&status=1&settoreId=&periodo=&ral=&ente=&page_num=0"
)

# 🔥 Parole chiave tecniche
KEYWORDS = [
    "funzionario tecnico",
    "architetto",
    "area tecnica",
    "urbanistica",
    "edilizia",
    "appalti",
    "lavori pubblici"
]


def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except:
            return set()
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(list(seen
