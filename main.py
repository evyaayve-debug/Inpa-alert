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

KEYWORDS = [
    "funzionario tecnico",
    "architetto",
    "area tecnica",
    "urbanistica",
    "edilizia",
    "appalti",
    "lavori pubblici"
]

SECTIONS = [
    "https://www.inpa.gov.it/bandi-e-avvisi/?page_num=",
    "https://www.inpa.gov.it/avvisi?page=",
    "https://www.inpa.gov.it/incarichi?page="
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


def scrape_section(base_url):
    bandi = []

    for page in range(0, 20):
        url = base_url + str(page)
        print(f"Scarico {url}...")

        r = requests.get(url)
        if r.status_code != 200:
            print(f"Pagina {page} non disponibile.")
            break

        soup = BeautifulSoup(r.text, "html.parser")

        # 🔥 Nuove classi INPA
        cards = soup.select(".card-bando-avviso")

        if not cards:
            print(f"Nessun bando nella pagina {page}.")
            break

        for card in cards:
            titolo_tag = card.select_one(".titolo-bando-avviso")
            ente_tag = card.select_one(".amministrazione-bando-avviso")
            link_tag = card.select_one(".vai-al-bando")

            if not link_tag:
                continue

            titolo = titolo_tag.get_text(strip=True) if titolo_tag else ""
            ente = ente_tag.get_text(strip=True) if ente_tag else ""
            link = link_tag["href"]

            bando = {
                "titolo": titolo,
                "amministrazione": ente,
                "urlDettaglio": "https://www.inpa.gov.it" + link,
                "id": link.split("=")[-1]
            }

            bandi.append(bando)

    return bandi


def fetch_all():
    all_bandi = []
    for section in SECTIONS:
        all_bandi.extend(scrape_section(section))
    print("Totale bandi trovati:", len(all_bandi))
    return all_bandi


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

    body = ""
    for b in new_bandi:
        body += f"- {b['titolo']}\n  Ente: {b['amministrazione']}\n  Link: {b['urlDettaglio']}\n\n"

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
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram non configurato")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    print("Invio Telegram...")
    r = requests.post(url, json=payload)
    print("Risposta Telegram:", r.text)


def main():
    print("Avvio controllo INPA...")

    seen = load_seen()
    bandi = fetch_all()

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
            testo += f"- {b['titolo']}\n  {b['amministrazione']}\n  {b['urlDettaglio']}\n\n"

        send_telegram(testo)
        save_seen(seen)
    else:
        print("Nessun nuovo bando.")

    send_telegram("Test Telegram: il bot funziona!")


if __name__ == "__main__":
    main()
