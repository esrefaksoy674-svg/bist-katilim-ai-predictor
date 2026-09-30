from __future__ import annotations

from .company_registry import CompanyInfo, CompanyRegistry
from .universe import fetch_katilim_universe


def build_company_registry(
    company_names: dict[str, str] | None = None,
    sectors: dict[str, str] | None = None,
    aliases: dict[str, list[str]] | None = None,
) -> CompanyRegistry:
    """
    Güncel Katılım evreninden şirket registry'si oluşturur.

    Şimdilik şirket adı/sektör/alias bilgileri dışarıdan alınabilir.
    Daha sonra bunlar kalıcı veritabanından beslenecektir.
    """

    symbols = fetch_katilim_universe()

    company_names = company_names or {}
    sectors = sectors or {}
    aliases = aliases or {}

    companies: list[CompanyInfo] = []

    for symbol in symbols:
        companies.append(
            CompanyInfo(
                symbol=symbol,
                name=company_names.get(
                    symbol,
                    symbol,
                ),
                sector=sectors.get(symbol),
                aliases=tuple(
                    aliases.get(symbol, [])
                ),
            )
        )

    return CompanyRegistry(companies)
