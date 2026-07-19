import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

SEEN_FILE = Path("seen.json")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

URL = "https://www.concorsi.it/concorsi/regione-liguria.htm"

KEYWORDS = [
    "tecnico",
    "funzionario",
    "urbanistica",
    "edilizia",
    "architetto",
    "ingegnere",
    "lavori pubblici",
    "appalti"
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
    print("Scarico concorsi Liguria da Concorsi.it...")

    r = requests.get(URL)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    bandi = []

    # ogni concorso è dentro <div class="box_concorso">
    boxes = soup.select("div.box_concorso")

    for box in boxes:
        titolo_tag = box.select_one("h2 a")
        ente_tag = box.select_one("p strong")
        link_tag = box.select_one("h2 a")

        if not titolo_tag or not link_tag:
            continue

        titolo = titolo_tag.get_text(strip=True)
        ente = ente_tag.get_text(strip=True) if ente_tag else ""
        link = link_tag["href"]

        bando_id = link  # URL = ID univoco

        bando = {
            "id": bando_id,
            "titolo": titolo,
            "ente": ente,
            "url": link
        }

        bandi.append(bando)

    print("Bandi trovati:", len(bandi))
    return bandi


def matches_profile(bando):
    titolo = bando["titolo"].lower()
    return any(k in titolo for k in KEYWORDS)


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
    print("Avvio controllo concorsi Liguria...")

    seen = load_seen()
    bandi = fetch_bandi()

    nuovi = []

    for b in bandi:
        if b["id"] not in seen and matches_profile(b):
            nuovi.append(b)
            seen.add(b["id"])

    if nuovi:
        testo = "Nuovi concorsi Liguria:\n\n"
        for b in nuovi:
            testo += f"- {b['titolo']}\n  Ente: {b['ente']}\n  Link: {b['url']}\n\n"

        send_telegram(testo)
        save_seen(seen)
    else:
        print("Nessun nuovo concorso tecnico.")

    send_telegram("Test Telegram: il bot funziona!")


if __name__ == "__main__":
    main()
