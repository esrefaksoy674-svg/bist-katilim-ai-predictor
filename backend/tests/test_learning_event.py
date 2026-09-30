from datetime import date

from app.services.learning_event import (
    calculate_change_percent,
    create_learning_event,
    is_learning_event,
)


def test_exactly_five_percent_is_not_learning():
    assert is_learning_event(5.0) is False


def test_above_five_percent_is_learning():
    assert is_learning_event(5.01) is True
    assert is_learning_event(8.0) is True


def test_below_five_percent_is_not_learning():
    assert is_learning_event(4.99) is False
    assert is_learning_event(-2.0) is False


def test_create_learning_event_rejects_five_percent():
    result = create_learning_event(
        symbol="THYAO",
        signal_date=date(2026, 9, 28),
        reference_date=date(2026, 9, 25),
        rise_percent=5.0,
    )

    assert result is None


def test_create_learning_event_accepts_above_five_percent():
    result = create_learning_event(
        symbol="THYAO",
        signal_date=date(2026, 9, 28),
        reference_date=date(2026, 9, 25),
        rise_percent=5.01,
    )

    assert result is not None
    assert result.symbol == "THYAO"
    assert result.rise_percent == 5.01


def test_calculate_change_percent():
    result = calculate_change_percent(
        previous_close=100.0,
        current_close=105.01,
    )

    assert round(result, 2) == 5.01
