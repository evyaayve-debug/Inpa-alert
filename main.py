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
            "amministrazione": ente,
            "urlDettaglio": "https://www.inpa.gov.it" + link,
            "id": link.split("/")[-1]
        })

    print(f"Trovati {len(bandi)} bandi totali.")
    return bandi


# ---------------------------
# Filtri
# ---------------------------

def matches_profile(bando):
    titolo = bando["titolo"].lower()
    ente = bando["amministrazione"].lower()

    return (
        any(k in titolo for k in KEYWORDS)
        and ("liguria" in ente or "genova" in ente)
    )


# ---------------------------
# Invio email
# ---------------------------

def send_email(new_bandi):
    if not (EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECIPIENT):
        print("Variabili email non configurate")
        return

    body = ""
    for b in new_bandi:
        body += f"- {b['titolo']}\n  Ente: {b['amministrazione']}\n  Link: {b['urlDettaglio']}\n\n"

    msg = MIMEText(body)
    msg["Subject"] = "Nuovi concorsi INPA per Funzionario Tecnico / Architetto"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT

    print("Invio email...")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    print("Email inviata.")


# ---------------------------
# Invio Telegram
# ---------------------------

def send_telegram(message):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram non configurato")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    print("Invio messaggio Telegram...")
    r = requests.post(url, json=payload
