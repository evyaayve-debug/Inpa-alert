import os
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from playwright.sync_api import sync_playwright
import requests

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

        for page_num in range(0, 20):  # scansiona fino a 20 pagine
            url = (
                "https://www.inpa.gov.it/bandi-e-avvisi/"
                "?text=&categoriaId=&regioneId=8&status=&settoreId=bcfb35babe934ef89a0d"
                "&periodo=&ral=&ente=&page_num=" + str(page_num)
            )
            print(f"Scarico pagina {page_num}: {url}")

            page.goto(url)

            try:
                page.wait_for_selector(".card-bando-avviso", timeout=10000)
            except:
                print(f"Pagina {page_num} vuota o senza card, mi fermo.")
                break

            cards = page.query_selector_all(".card-bando-avviso")

            if not cards:
                print(f"Nessun bando in pagina {page_num}, stop.")
                break

            for card in cards:
                titolo_el = card.query_selector(".titolo-bando-avviso")
                ente_el = card.query_selector(".amministrazione-bando-avviso")
                link_el = card.query_selector(".vai-al-bando")

                if not (titolo_el and ente_el and link_el):
                    continue

                titolo = titolo_el.inner_text().strip()
                ente = ente_el.inner_text().strip()
                link = link_el.get_attribute("href")

                bando = {
                    "titolo": titolo,
                    "amministrazione": ente,
                    "urlDettaglio": "https://www.inpa.gov.it" + link,
                    "id": link.split("=")[-1]
                }

                bandi.append(bando)

        browser.close()

    print("Totale bandi trovati:", len(bandi))
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
            testo += f"- {b['titolo']}\n  {b['amministrazione']}\n  {b['urlDettaglio']}\n\n"

        send_telegram(testo)
        save_seen(seen)
    else:
        print("Nessun nuovo bando.")

    send_telegram("Test Telegram: il bot funziona!")


if __name__ == "__main__":
    main()
