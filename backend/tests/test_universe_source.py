import pandas as pd
import pytest

from app.services.universe_source import extract_symbols


def test_extract_symbols_supports_official_component_code_column():
    frame = pd.DataFrame(
        {
            "Bileşen Kodu": ["TUPRS.E", "ASELS.E", None, "TUPRS.E"],
            "Bileşen Adı": ["TUPRAS", "ASELSAN", "", "TUPRAS"],
        }
    )

    assert extract_symbols(frame) == ["ASELS", "TUPRS"]


def test_extract_symbols_normalizes_legacy_headers():
    frame = pd.DataFrame({" HİSSE   KODU ": ["thyao", "EREGL"]})

    assert extract_symbols(frame) == ["EREGL", "THYAO"]


def test_extract_symbols_reports_unrecognized_source_columns():
    frame = pd.DataFrame({"Index Name": ["BIST Katılım"]})

    with pytest.raises(RuntimeError, match="Index Name"):
        extract_symbols(frame)


def test_extract_symbols_rejects_table_without_valid_tickers():
    frame = pd.DataFrame({"Bileşen Kodu": ["", "BIST-100", None]})

    with pytest.raises(RuntimeError, match="hiç hisse sembolü"):
        extract_symbols(frame)
