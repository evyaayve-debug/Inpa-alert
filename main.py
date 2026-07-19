import os
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from playwright.sync_api import sync_playwright

SEEN_FILE = Path("seen.json")

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

KEYWORDS = [
    "funzionario tecnico",
    "architetto",
    "area tecnica",
    "urbanistica",
    "edilizia",
    "appalti",
    "lavori pubblici"
]

URL = "https://www.inpa.gov.it/bandi-e-avvisi/?text=&categoriaId=&regioneId=8&status=&settoreId=bcfb35babe934ef89a0d&periodo=&ral=&ente=&page_num=0"


def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except:
            return set()
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(list(seen)))


def fetch_bandi():
    print("Apro INPA con Playwright...")

    bandi = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)

        # aspetta che React carichi i bandi
        page.wait_for_selector(".card-bando-avviso", timeout=15000)

        cards = page.query_selector_all(".card-bando-avviso")

        for card in cards:
            titolo = card.query_selector(".titolo-bando-avviso").inner_text().strip()
            ente = card.query_selector(".amministrazione-bando-avviso").inner_text().strip()
