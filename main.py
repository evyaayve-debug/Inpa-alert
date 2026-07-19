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

INPA_URL = (
    "https://www.inpa.gov.it/avvisi?"
    "parolaChiave=funzionario%20tecnico&regione=Liguria"
)

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
    SEEN_FILE.write_text(json.dumps(list(seen)))


def fetch_bandi():
    print("Scarico INPA...")
    r = requests.get(INPA_URL)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select(".card-avviso")

    bandi = []

    for card in cards:
        titolo = card.select_one(".titolo-avviso").get_text(strip=True)
        ente = card.select_one(".amministrazione").get_text(strip=True)
        link = card.select_one("a")["href"]

        bando = {
            "titolo": titolo,
            "amministrazione": ente,
            "urlDettaglio": "https://www.inpa.gov.it" + link,
            "id": link.split("/")[-1]
        }

        bandi.append(bando)

    print("Bandi trovati:", len(bandi))
    return bandi


def matches_profile(bando):
    titolo = bando["titolo"].lower()
    ente = bando["amministrazione"].lower()

    keyword_ok = any(k in titolo for k in KEYWORDS)
    luogo_ok = ("liguria" in ente) or ("genova" in ente)

    return keyword_ok and luogo_ok


def send_email(new_bandi):
    if not (EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECIPIENT):
        print("Email non configurata")
        return

    body_lines = []

    for b in new_bandi:
        line = (
            "- " + b["titolo"] + "\n"
            "  Ente: " + b["amministrazione"] + "\n"
            "  Link: " + b["urlDettaglio"] + "\n"
        )
        body_lines.append(line)

    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg["Subject"] = "Nuovi bandi INPA"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT

    print("Invio email...")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    print("Email inviata.")


def send_telegram(message):
    print("DEBUG TOKEN:", TELEGRAM_TOKEN)
    print("DEBUG CHAT_ID:", TELEGRAM_CHAT_ID)

    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram non configurato")
        return

    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    print("Invio Telegram...")
    r = requests.post(url, json=payload)
    print("Risposta Telegram:", r.text)


def main():
    print("Avvio controllo INPA...")

    seen = load_seen()
    bandi = fetch_bandi()

    nuovi = []

    for b in bandi:
        if b["id"] not in seen and matches_profile(b):
            nuovi.append(b)
            seen.add(b["id"])

    if nuovi:
        print("Nuovi bandi:", len(nuovi))
        send_email(nuovi)

        testo = "Nuovi bandi INPA:\n\n"
        for b in nuovi:
            testo += "- " + b["titolo"] + "\n"
            testo += "  " + b["amministrazione"] + "\n"
            testo += "  " + b["urlDettaglio"] + "\n\n"

        send_telegram(testo)
        save_seen(seen)
    else:
        print("Nessun nuovo bando.")

    send_telegram("Test Telegram: il bot funziona!")


if __name__ == "__main__":
    main()
