from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    """
    Haber ve şirket isimlerini karşılaştırılabilir hale getirir.
    """

    text = str(text).upper()

    replacements = {
        "İ": "I",
        "Ş": "S",
        "Ğ": "G",
        "Ü": "U",
        "Ö": "O",
        "Ç": "C",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def build_company_aliases(
    symbol: str,
    company_name: str | None = None,
    aliases: list[str] | None = None,
) -> list[str]:
    """
    Bir hisse için aranabilecek isimleri oluşturur.
    """

    values = [symbol]

    if company_name:
        values.append(company_name)

    if aliases:
        values.extend(aliases)

    normalized = []

    for value in values:
        value = normalize_text(value)

        if value and value not in normalized:
            normalized.append(value)

    return normalized


def match_news_to_company(
    title: str,
    symbol: str,
    company_name: str | None = None,
    aliases: list[str] | None = None,
) -> dict:
    """
    Bir haber başlığının belirli bir şirketle ilişkisini
    temel metin eşleşmesiyle belirler.

    Bu sonuç doğrudan 'haber kesinlikle bu şirket hakkında'
    anlamına gelmez. Daha sonraki aşamada içerik ve bağlam
    analizi yapılacaktır.
    """

    normalized_title = normalize_text(title)

    company_aliases = build_company_aliases(
        symbol=symbol,
        company_name=company_name,
        aliases=aliases,
    )

    matched_aliases = [
        alias
        for alias in company_aliases
        if _contains_phrase(
            normalized_title,
            alias,
        )
    ]

    return {
        "symbol": symbol.upper(),
        "matched": bool(matched_aliases),
        "matched_aliases": matched_aliases,
        "match_count": len(matched_aliases),
    }


def _contains_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Tam kelime/ifade eşleşmesine yakın güvenli arama.
    """

    if not phrase:
        return False

    pattern = (
        r"(?<![A-Z0-9])"
        + re.escape(phrase)
        + r"(?![A-Z0-9])"
    )

    return re.search(
        pattern,
        text,
    ) is not None
