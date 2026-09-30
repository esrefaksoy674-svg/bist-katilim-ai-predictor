from datetime import datetime, timezone


def validate_news_item(item: dict) -> tuple[bool, list[str]]:
    """
    Tek bir haber kaydının kullanılabilir olup olmadığını kontrol eder.
    """

    errors: list[str] = []

    title = str(item.get("title", "")).strip()
    url = str(item.get("url", "")).strip()
    source = str(item.get("source", "")).strip()
    published_at = item.get("published_at")

    if not title:
        errors.append("title_missing")

    if not url:
        errors.append("url_missing")

    if not source:
        errors.append("source_missing")

    if not isinstance(published_at, datetime):
        errors.append("published_at_invalid")

    elif published_at > datetime.now(timezone.utc):
        errors.append("published_at_in_future")

    return len(errors) == 0, errors


def validate_news_batch(items: list[dict]) -> dict:
    """
    Haber listesini toplu olarak kontrol eder.
    """

    valid_items: list[dict] = []
    invalid_items: list[dict] = []

    for item in items:
        is_valid, errors = validate_news_item(item)

        if is_valid:
            valid_items.append(item)
        else:
            invalid_items.append(
                {
                    "item": item,
                    "errors": errors,
                }
            )

    return {
        "total": len(items),
        "valid": len(valid_items),
        "invalid": len(invalid_items),
        "valid_items": valid_items,
        "invalid_items": invalid_items,
    }
