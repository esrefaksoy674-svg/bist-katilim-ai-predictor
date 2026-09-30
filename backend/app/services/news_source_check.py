from __future__ import annotations

from datetime import datetime, timezone

import requests


DEFAULT_TIMEOUT = 20


def check_source(
    name: str,
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Bir haber/RSS kaynağının erişilebilirliğini kontrol eder.

    Bu fonksiyon kaynağın gerçekten kullanılabilir olup olmadığını
    ölçer; kaynağı otomatik olarak güvenilir ilan etmez.
    """

    checked_at = datetime.now(timezone.utc)

    result = {
        "name": name,
        "url": url,
        "reachable": False,
        "status_code": None,
        "content_length": 0,
        "checked_at": checked_at,
        "error": None,
    }

    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": (
                    "BIST-Katilim-AI-Predictor/0.1"
                )
            },
        )

        result["status_code"] = response.status_code
        result["content_length"] = len(response.content)
        result["reachable"] = response.ok

        if not response.ok:
            result["error"] = (
                f"HTTP {response.status_code}"
            )

    except requests.RequestException as exc:
        result["error"] = str(exc)

    return result


def check_sources(sources: dict) -> dict:
    """
    Birden fazla haber kaynağını kontrol eder.
    """

    results = []

    for name, config in sources.items():
        if not config.get("enabled", False):
            continue

        for url in config.get("urls", []):
            results.append(
                check_source(
                    name=name,
                    url=url,
                )
            )

    reachable = sum(
        1
        for result in results
        if result["reachable"]
    )

    return {
        "checked": len(results),
        "reachable": reachable,
        "unreachable": len(results) - reachable,
        "results": results,
    }
