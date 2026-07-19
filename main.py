import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

SEEN_FILE = Path("seen.json")

EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

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
    SEEN_FILE.write_text(json.dumps(list(seen)))


def fetch_all_from_api():
    print("Scarico TUTTI i concorsi dall'API INPA...")
    all_bandi = []

    for page in range(0, 50):  # 🔥 Scansiona 50 pagine dell'API
        url = f"https://www.inpa.gov.it/api/v1/public/concorsi?page={page}"
        print(f"Scarico pagina API {page}...")

        r = requests.get(url)
        if r.status_code != 200:
            print(f"Pagina API {page} non disponibile, interrompo.")
            break

        data = r.json()

        if "contenuto" not in data or not data["contenuto"]:
            print(f"Nessun concorso nella pagina API {page}, fine.")
            break

        for item in data["contenuto"]:
            bando = {
                "id": item.get("id", ""),
                "titolo": item.get("titolo", "").strip(),
                "amministrazione": item.get("amministrazione", "").strip(),
                "regione": item.get("regione", "").strip(),
                "urlDettaglio": f"https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id={item.get('id')}"
            }
            all_bandi.append(bando)

    print("Totale bandi trovati via API:", len(all_bandi))
    return all_bandi


def matches_profile(bando):
    titolo = bando["titolo"].lower()
    ente = bando["amministrazione"].lower()
    regione = bando["regione"].lower()

    keyword_ok = any(k in titolo for k in KEYWORDS)
    luogo_ok = ("liguria" in regione) or ("genova" in ente)

    return keyword_ok and luogo_ok


def send_email(new_bandi):
    if not (EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECIPIENT):
        print("Email non configurata")
        return

    body = ""
    for b in new_bandi:
        body += f"- {b['titolo']}\n  Ente: {b['amministrazione']}\n  Regione: {b['regione']}\n  Link: {b['urlDettaglio']}\n\n"

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
    bandi = fetch_all_from_api()

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
            testo += f"- {b['titolo']}\n  {b['amministrazione']}\n  Regione: {b['regione']}\n  {b['urlDettaglio']}\n\n"

        send_telegram(testo)
        save_seen(seen)
    else:
        print("Nessun nuovo bando.")

    send_telegram("Test Telegram: il bot funziona!")


if __name__ == "__main__":
    main()
