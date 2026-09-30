from __future__ import annotations

import requests


BIST_KATILIM_SOURCE_URL = (
    "https://borsaistanbul.com/"
    "datum/hisse_endeks_katilim_ds.csv"
)


def fetch_official_katilim_data() -> str:
    """
    Borsa İstanbul Katılım veri kaynağını indirir.

    Kaynak erişilemiyorsa hata verir.
    Eksik veriyle evren oluşturulmasına izin verilmez.
    """

    response = requests.get(
        BIST_KATILIM_SOURCE_URL,
        timeout=30,
        headers={
            "User-Agent": (
                "BIST-Katilim-AI-Predictor/0.1"
            )
        },
    )

    response.raise_for_status()

    if not response.content:
        raise RuntimeError(
            "Borsa İstanbul Katılım kaynağı boş döndü."
        )

    return response.content.decode(
        "utf-8-sig",
        errors="replace",
    )


def source_status() -> dict:
    """
    Kaynağın erişilebilirlik durumunu kontrol eder.
    """

    try:
        data = fetch_official_katilim_data()

        return {
            "available": True,
            "source": BIST_KATILIM_SOURCE_URL,
            "bytes": len(data.encode("utf-8")),
        }

    except Exception as exc:
        return {
            "available": False,
            "source": BIST_KATILIM_SOURCE_URL,
            "error": str(exc),
        }
