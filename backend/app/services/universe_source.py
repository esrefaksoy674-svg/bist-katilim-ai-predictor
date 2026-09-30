from __future__ import annotations

import io

import pandas as pd
import requests


BIST_KATILIM_SOURCE_URL = (
    "https://borsaistanbul.com/datum/hisse_endeks_katilim_ds.csv"
)

TIMEOUT = 30


def fetch_official_katilim_data() -> pd.DataFrame:
    response = requests.get(
        BIST_KATILIM_SOURCE_URL,
        timeout=TIMEOUT,
        headers={
            "User-Agent": "BIST-Katilim-AI-Predictor/0.1"
        },
    )

    response.raise_for_status()

    if not response.content:
        raise RuntimeError(
            "Borsa İstanbul Katılım verisi boş döndü."
        )

    raw = response.content

    for encoding in ("utf-8-sig", "cp1254", "latin1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(
            "Katılım verisi çözümlenemedi."
        )

    separators = [";", ",", "\t"]

    best_df = None

    for separator in separators:
        try:
            df = pd.read_csv(
                io.StringIO(text),
                sep=separator,
                dtype=str,
            )

            if len(df.columns) > 1:
                best_df = df
                break

        except Exception:
            continue

    if best_df is None or best_df.empty:
        raise RuntimeError(
            "Katılım verisi tablo olarak okunamadı."
        )

    best_df.columns = [
        str(column).strip()
        for column in best_df.columns
    ]

    return best_df


def extract_symbols(df: pd.DataFrame) -> list[str]:
    """
    Veri tablosundan hisse sembollerini bulur.
    Sütun adı değişse bile sembol sütununu
    makul adaylar arasından belirlemeye çalışır.
    """

    candidates = [
        "Kod",
        "Kodu",
        "Sembol",
        "Symbol",
        "Hisse Kodu",
        "Pay Kodu",
        "Hisse",
    ]

    column = None

    for candidate in candidates:
        for actual in df.columns:
            if (
                str(actual).strip().lower()
                == candidate.lower()
            ):
                column = actual
                break

        if column is not None:
            break

    if column is None:
        raise RuntimeError(
            "Katılım verisinde hisse sembolü sütunu bulunamadı."
        )

    symbols = []

    for value in df[column].dropna():
        symbol = str(value).strip().upper()

        if (
            symbol
            and symbol.isalnum()
            and 2 <= len(symbol) <= 10
        ):
            symbols.append(symbol)

    symbols = sorted(set(symbols))

    if not symbols:
        raise RuntimeError(
            "Katılım verisinden hiç hisse sembolü çıkarılamadı."
        )

    return symbols


def fetch_katilim_symbols() -> list[str]:
    df = fetch_official_katilim_data()
    return extract_symbols(df)


def source_status() -> dict:
    try:
        df = fetch_official_katilim_data()
        symbols = extract_symbols(df)

        return {
            "available": True,
            "source": BIST_KATILIM_SOURCE_URL,
            "rows": len(df),
            "symbols": len(symbols),
            "sample": symbols[:10],
        }

    except Exception as exc:
        return {
            "available": False,
            "source": BIST_KATILIM_SOURCE_URL,
            "error": str(exc),
        }
