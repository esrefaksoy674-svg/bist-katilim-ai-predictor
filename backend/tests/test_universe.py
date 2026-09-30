from unittest.mock import patch

from app.services.universe import fetch_katilim_universe


def test_katilim_universe_returns_symbols():
    fake_symbols = [
        "THYAO",
        "TUPRS",
        "ASELS",
    ]

    with patch(
        "app.services.universe.fetch_katilim_symbols",
        return_value=fake_symbols,
    ):
        symbols = fetch_katilim_universe()

    assert symbols
    assert symbols == sorted(set(fake_symbols))


def test_katilim_universe_rejects_empty_source():
    with patch(
        "app.services.universe.fetch_katilim_symbols",
        return_value=[],
    ):
        try:
            fetch_katilim_universe()
        except RuntimeError:
            return

    raise AssertionError(
        "Boş Katılım evreni kabul edilmemeliydi."
    )
