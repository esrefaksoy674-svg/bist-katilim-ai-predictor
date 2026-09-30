from datetime import date

import requests

BIST_KATILIM_CSV_URL = (
    "https://borsaistanbul.com/datum/hisse_endeks_katilim_ds.csv"
)


def fetch_katilim_universe() -> list[str]:
    """
    Borsa İstanbul'dan güncel Katılım paylarını almaya çalışır.

    Dönen liste yalnızca sembollerden oluşur.
    Veri alınamazsa sessizce boş liste dönmek yerine hata verir;
    böylece sistem eksik evrenle yanlış tahmin üretmez.
    """
    response = requests.get(
        BIST_KATILIM_CSV_URL,
        timeout=30,
        headers={
            "User-Agent": "BIST-Katilim-AI-Predictor/1.0"
        },
    )
    response.raise_for_status()

    text = response.content.decode("utf-8-sig", errors="replace")

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        raise RuntimeError("Borsa İstanbul Katılım verisi boş döndü.")

    symbols: list[str] = []

    for line in lines[1:]:
        parts = [part.strip() for part in line.split(";")]

        if not parts:
            continue

        symbol = parts[0].upper()

        if symbol and symbol.isalnum():
            symbols.append(symbol)

    symbols = sorted(set(symbols))

    if not symbols:
        raise RuntimeError(
            "Borsa İstanbul verisinden Katılım hissesi bulunamadı."
        )

    return symbols


def get_universe_metadata() -> dict:
    symbols = fetch_katilim_universe()

    return {
        "trading_date": date.today().isoformat(),
        "count": len(symbols),
        "symbols": symbols,
        "source": BIST_KATILIM_CSV_URL,
    }
