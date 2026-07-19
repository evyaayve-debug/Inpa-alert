import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

SEEN_FILE = Path("seen.json")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

RSS_URL = "https://www.gazzettaufficiale.it/rss/concorsi"

KEYWORDS = [
    "funzionario",
    "tecnico",
    "architetto",
    "ingegnere",
    "urbanistica",
    "edilizia",
    "lavori pubblici",
    "appalti"
]

LUOGHI = [
    "liguria",
    "genova"
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


def fetch_concorsi():
    print("Scarico concorsi da Gazzetta Ufficiale RSS...")

    r = requests.get(RSS_URL)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "xml")

    items = soup.find_all("item")
    concorsi = []

    for item in items:
        title = item.title.get_text(strip=True) if item.title else ""
        description = item.description.get_text(strip=True) if item.description else ""
        link = item.link.get_text(strip=True) if item.link else ""

        # ID univoco = link
        concorso_id = link

        concorso = {
            "id": concorso_id,
            "titolo": title,
            "descrizione": description,
            "url": link
        }

        concorsi.append(concorso)

    print("Concorsi trovati nel feed:", len(concorsi))
    return concorsi


def matches_profile(concorso):
    testo = (concorso["titolo"] + " " + concorso["descrizione"]).lower()

    keyword_ok = any(k in testo for k in KEYWORDS)
    luogo_ok = any(l in testo for l in LUOGHI)

    return keyword_ok and luogo_ok


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
    print("Avvio controllo concorsi Gazzetta Ufficiale...")

    seen = load_seen()
    concorsi = fetch_concorsi()

    nuovi = []

    for c in concorsi:
        if c["id"] not in seen and matches_profile(c):
            nuovi.append(c)
            seen.add(c["id"])

    if nuovi:
        testo = "Nuovi concorsi tecnici Liguria/Genova (Gazzetta Ufficiale):\n\n"
        for c in nuovi:
            testo += f"- {c['titolo']}\n  {c['url']}\n\n"

        send_telegram(testo)
        save_seen(seen)
    else:
        print("Nessun nuovo concorso tecnico per Liguria/Genova.")

    send_telegram("Test RSS Gazzetta: il bot funziona!")


if __name__ == "__main__":
    main()
