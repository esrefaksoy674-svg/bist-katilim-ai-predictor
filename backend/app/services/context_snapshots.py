from __future__ import annotations

import pandas as pd


def build_context_snapshots(
    candidates: pd.DataFrame,
    available_date,
    news_features_by_symbol: dict[str, dict] | None = None,
    sector_by_symbol: dict[str, str] | None = None,
) -> list[dict]:
    """Build numeric, dated context records without changing predictions."""
    if candidates is None or candidates.empty or "symbol" not in candidates:
        return []
    news_by_symbol = {
        str(symbol).upper(): values
        for symbol, values in (news_features_by_symbol or {}).items()
    }
    sectors = {
        str(symbol).upper(): str(sector).strip().upper()
        for symbol, sector in (sector_by_symbol or {}).items()
        if str(sector).strip()
    }
    working = candidates.copy()
    working["symbol"] = working["symbol"].astype(str).str.upper()
    if "momentum" in working:
        working["momentum"] = pd.to_numeric(working["momentum"], errors="coerce")
    momenta = working.set_index("symbol")["momentum"].to_dict() if "momentum" in working else {}
    valid_momentum = [float(value) for value in momenta.values() if pd.notna(value)]
    market_features = {
        "universe_size": int(len(working)),
        "momentum_mean_10d": (
            float(sum(valid_momentum) / len(valid_momentum)) if valid_momentum else None
        ),
        "positive_momentum_share": (
            float(sum(value > 0 for value in valid_momentum) / len(valid_momentum))
            if valid_momentum else None
        ),
    }

    sector_values: dict[str, list[float]] = {}
    for symbol, momentum in momenta.items():
        sector = sectors.get(symbol)
        if sector and pd.notna(momentum):
            sector_values.setdefault(sector, []).append(float(momentum))

    records = []
    for _, row in working.iterrows():
        symbol = row["symbol"]
        technical = {
            name: float(value)
            for name, value in row.items()
            if name != "symbol" and pd.notna(value) and pd.api.types.is_number(value)
        }
        peer_values = sector_values.get(sectors.get(symbol, ""), [])
        sector_features = {
            "peer_count": len(peer_values),
            "peer_momentum_mean_10d": (
                float(sum(peer_values) / len(peer_values)) if peer_values else None
            ),
            "peer_positive_momentum_share": (
                float(sum(value > 0 for value in peer_values) / len(peer_values))
                if peer_values else None
            ),
        } if symbol in sectors else {}
        records.append({
            "symbol": symbol,
            "available_date": available_date.isoformat(),
            "technical_features": technical,
            "news_features": news_by_symbol.get(symbol, {
                "article_count": 0,
                "source_count": 0,
                "kap_article_count": 0,
                "rss_article_count": 0,
            }),
            "market_features": market_features,
            "sector_features": sector_features,
        })
    return records


def aggregate_news_features(items: list[dict]) -> dict[str, dict[str, int]]:
    """Summarize matched daily headlines as conservative count features."""
    counts: dict[str, dict[str, set]] = {}
    for item in items or []:
        symbol = str(item.get("symbol", "")).upper().strip()
        if not symbol:
            continue
        row = counts.setdefault(symbol, {"hashes": set(), "sources": set(), "kap": 0, "rss": 0})
        identity = item.get("content_hash") or item.get("url") or item.get("title")
        if identity in row["hashes"]:
            continue
        row["hashes"].add(identity)
        source = str(item.get("source", "unknown"))
        row["sources"].add(source)
        if source.lower().startswith("kap"):
            row["kap"] += 1
        else:
            row["rss"] += 1
    return {
        symbol: {
            "article_count": len(row["hashes"]),
            "source_count": len(row["sources"]),
            "kap_article_count": row["kap"],
            "rss_article_count": row["rss"],
        }
        for symbol, row in counts.items()
    }


def parse_sector_map(value: str) -> dict[str, str]:
    """Parse an optional comma-separated SYMBOL:SECTOR mapping."""
    sectors = {}
    for item in value.split(","):
        if ":" not in item:
            continue
        symbol, sector = item.split(":", 1)
        symbol, sector = symbol.strip().upper(), sector.strip().upper()
        if symbol and sector:
            sectors[symbol] = sector
    return sectors
