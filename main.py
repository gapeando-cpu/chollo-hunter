import os
import re
import json
import hashlib
from pathlib import Path
from html import unescape

import feedparser
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
MIN_DISCOUNT = int(os.getenv("MIN_DISCOUNT", "60"))
FEEDS = [x.strip() for x in os.getenv(
    "RSS_FEEDS",
    "https://www.ofertitas.es/etiqueta/amazon-espana/feed/,https://chollometro.com/rss"
).split(",") if x.strip()]

# Ajusta estas palabras cuando quieras ampliar o reducir las categorías.
CATEGORY_KEYWORDS = {
    "tecnologia": [
        "smartphone", "móvil", "movil", "tablet", "smartwatch", "reloj",
        "auriculares", "altavoz", "televisor", "tv", "monitor", "router",
        "cámara", "camara", "gps", "garmin", "xiaomi", "samsung", "iphone"
    ],
    "informatica": [
        "portátil", "portatil", "ordenador", "ssd", "disco duro", "ram",
        "teclado", "ratón", "raton", "ratón", "impresora", "usb", "wifi",
        "pc", "laptop", "webcam", "tarjeta gráfica", "grafica"
    ],
    "hogar": [
        "aspirador", "robot aspirador", "cafetera", "sartén", "sarten",
        "olla", "freidora", "menaje", "colchón", "colchon", "lámpara",
        "lampara", "mueble", "sábanas", "sabanas", "cocina", "limpieza"
    ],
    "deporte_senderismo": [
        "senderismo", "trekking", "montaña", "montana", "zapatillas",
        "botas", "merrell", "salomon", "mochila", "bastones", "chaqueta",
        "impermeable", "deporte", "running", "garmin"
    ],
    "electrodomesticos": [
        "lavadora", "secadora", "frigorífico", "frigorifico", "nevera",
        "microondas", "lavavajillas", "horno", "vitrocerámica",
        "vitroceramica", "aire acondicionado", "deshumidificador"
    ],
}

DATA_FILE = Path("data/seen.json")
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_seen():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_seen(seen):
    DATA_FILE.write_text(
        json.dumps(seen, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(value)).strip()


def find_discount(text):
    # Detecta expresiones como "-60%", "60 % de descuento" o "rebaja del 60%".
    patterns = [
        r"[-−]\s*(\d{1,2})\s*%",
        r"(\d{1,2})\s*%\s*(?:de\s*)?(?:descuento|rebaja)",
        r"(?:descuento|rebaja)\s*(?:del|de)?\s*(\d{1,2})\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = int(match.group(1))
            if 1 <= value <= 99:
                return value
    return None


def detect_category(text):
    lowered = text.casefold()
    for category, words in CATEGORY_KEYWORDS.items():
        if any(word.casefold() in lowered for word in words):
            return category
    return None


def extract_amazon_link(entry, source_url):
    # Conserva el enlace del artículo de la fuente si no hay enlace Amazon explícito.
    candidates = [entry.get("link", "")]
    content = entry.get("summary", "")
    candidates += re.findall(r'https?://[^"\s<>]+', content)
    for link in candidates:
        if "amazon.es/" in link or "amzn.to/" in link:
            return link
    return entry.get("link") or source_url


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": False
        },
        timeout=25
    )
    response.raise_for_status()


def main():
    seen = load_seen()
    newly_seen = 0
    sent = 0

    for feed_url in FEEDS:
        feed = feedparser.parse(feed_url)
        if feed.bozo and not feed.entries:
            print(f"No se pudo leer el feed: {feed_url} — {feed.bozo_exception}")
            continue

        for entry in feed.entries:
            title = clean_text(entry.get("title", "Oferta"))
            summary = clean_text(entry.get("summary", ""))
            text = f"{title} {summary}"
            link = extract_amazon_link(entry, feed_url)

            # El primer feed es específicamente de ofertas Amazon España.
            is_amazon_feed = "ofertitas.es/etiqueta/amazon-espana" in feed_url
            mentions_amazon = (
                "amazon" in text.casefold()
                or "amazon.es" in link.casefold()
                or "amzn.to" in link.casefold()
            )
            if not (is_amazon_feed or mentions_amazon):
                continue

            discount = find_discount(text)
            category = detect_category(text)

            if discount is None or discount < MIN_DISCOUNT or category is None:
                continue

            item_id = entry.get("id") or entry.get("guid") or entry.get("link") or title
            fingerprint = hashlib.sha256(str(item_id).encode("utf-8")).hexdigest()

            if fingerprint in seen:
                continue

            message = (
                "🚨 CHOLLO HUNTER — POSIBLE CHOLLO\n\n"
                f"📂 Categoría: {category.replace('_', ' ').title()}\n"
                f"🔥 Descuento anunciado: {discount}%\n\n"
                f"📦 {title}\n\n"
                "⚠️ Descuento comunicado por la fuente; no está "
                "verificado contra un histórico independiente de precios.\n\n"
                f"🔗 {link}"
            )

            send_telegram(message)
            seen[fingerprint] = {
                "title": title,
                "link": link,
                "discount": discount,
                "category": category
            }
            newly_seen += 1
            sent += 1

    # Limita el archivo para que no crezca indefinidamente.
    if len(seen) > 5000:
        seen = dict(list(seen.items())[-4000:])

    save_seen(seen)
    print(f"Ofertas nuevas notificadas: {sent}; entradas guardadas: {len(seen)}")


if __name__ == "__main__":
    main()
