from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyInfo:
    symbol: str
    name: str
    sector: str | None = None
    aliases: tuple[str, ...] = ()


class CompanyRegistry:
    """
    Katılım evrenindeki şirketlerin kimlik bilgilerini tutar.

    Bu yapı daha sonra veritabanından beslenecektir.
    Şimdilik servis katmanının sözleşmesini oluşturuyoruz.
    """

    def __init__(
        self,
        companies: list[CompanyInfo] | None = None,
    ):
        self._companies = {
            company.symbol.upper(): company
            for company in (companies or [])
        }

    def get(
        self,
        symbol: str,
    ) -> CompanyInfo | None:
        return self._companies.get(
            symbol.upper()
        )

    def all(self) -> list[CompanyInfo]:
        return list(
            self._companies.values()
        )

    def symbols(self) -> list[str]:
        return sorted(
            self._companies.keys()
        )

    def add(
        self,
        company: CompanyInfo,
    ) -> None:
        self._companies[
            company.symbol.upper()
        ] = company

    def count(self) -> int:
        return len(self._companies)
