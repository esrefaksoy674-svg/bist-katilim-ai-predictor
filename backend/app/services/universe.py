from datetime import date

from .universe_source import fetch_katilim_symbols


def fetch_katilim_universe() -> list[str]:
    """
    Güncel Katılım evrenini veri kaynağından alır.

    Veri alınamazsa boş liste döndürmez.
    Böylece eksik evrenle tarama yapılması engellenir.
    """

    symbols = fetch_katilim_symbols()

    if not symbols:
        raise RuntimeError(
            "Katılım evreninden hisse bulunamadı."
        )

    return sorted(set(symbols))


def get_universe_metadata() -> dict:
    symbols = fetch_katilim_universe()

    return {
        "trading_date": date.today().isoformat(),
        "count": len(symbols),
        "symbols": symbols,
        "source": "Borsa Istanbul Katilim",
    }
