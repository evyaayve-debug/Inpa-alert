import os
import requests
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from bs4 import BeautifulSoup

SEEN_FILE = Path("seen.json")

# Email secrets
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT")

# Telegram secrets
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# URL della pagina INPA (scraping)
INPA_URL = "https://www.inpa.gov.it/avvisi?parolaChiave=funzionario%20tecnico&regione=Liguria"

KEYWORDS = [
    "funzionario tecnico",
    "architetto",
    "area tecnica",
    "urbanistica",
    "edilizia",
    "appalti",
    "lavori pubblici",
]


# ---------------------------
# Gestione dei bandi già visti
# ---------------------------

def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except:
            return set()
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(list(seen)))


# ---------------------------
# Scraping INPA
# ---------------------------

def fetch_bandi():
    print("Scarico la pagina INPA...")
    r = requests.get(INPA_URL)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select(".card-avviso")

    bandi = []

    for card in cards:
        titolo = card.select_one(".titolo-avviso").get_text(strip=True)
        ente = card.select_one(".amministrazione").get_text(strip=True)
        link = card.select_one("a")["href"]

        bandi.append({
            "titolo": titolo,
