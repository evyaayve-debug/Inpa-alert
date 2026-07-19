import os
import requests
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

SEEN_FILE = Path("seen.json")

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

API_URL = "https://www.inpa.gov.it/api/v1/avvisi/search"



KEYWORDS = [
    "funzionario tecnico",
    "architetto",
    "area tecnica",
    "urbanistica",
    "edilizia",
    "appalti",
    "lavori pubblici",
]

def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()

def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(list(seen)))

from bs4 import BeautifulSoup

def fetch_bandi():
    url = "https://www.inpa.gov.it/avvisi?parolaChiave=funzionario%20tecnico&regione=Liguria"
    r = requests.get(url)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    bandi = []
    cards = soup.select(".card-avviso")

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

    return bandi



def matches_profile(bando):
    titolo = bando.get("titolo", "").lower()
    ente = bando.get("amministrazione", "").lower()
    return (
        any(k in titolo for k in KEYWORDS)
        and ("liguria" in ente or "genova" in ente)
    )

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

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    seen = load_seen()
    bandi = fetch_bandi()

    nuovi = []
    for b in bandi:
        b_id = b["id"]
        if b_id not in seen and matches_profile(b):
            nuovi.append(b)
            seen.add(b_id)

    if nuovi:
        send_email(nuovi)
        save_seen(seen)
send_telegram("Test Telegram: il bot funziona!")

if __name__ == "__main__":
    main()
