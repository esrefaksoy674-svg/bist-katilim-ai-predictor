from datetime import date
from unittest.mock import patch

from app.services.scheduled_training import run_scheduled_training


def test_scheduled_training_uses_istanbul_date():
    class FixedDateTime:
        @classmethod
        def now(cls, tz=None):
            return __import__("datetime").datetime(
                2026, 10, 2, 1, 30, tzinfo=__import__("datetime").timezone.utc
            ).astimezone(tz)

    fake_result = object()
    registry = type(
        "Registry",
        (),
        {"active": lambda self: None},
    )()

    with patch(
        "app.services.scheduled_training.datetime",
        FixedDateTime,
    ), patch(
        "app.services.scheduled_training.ModelRegistry",
        return_value=registry,
    ), patch(
        "app.services.scheduled_training.restore_models",
    ) as restore, patch(
        "app.services.scheduled_training.get_model_version_repository",
        return_value="VERSIONS",
    ), patch(
        "app.services.scheduled_training.get_model_artifact_repository",
        return_value="ARTIFACTS",
    ), patch(
        "app.services.scheduled_training.train_and_persist_market_model",
        return_value=fake_result,
    ) as train:
        result = run_scheduled_training()

    assert result["date"] == "2026-10-02"
    assert result["timezone"] == "Europe/Istanbul"
    assert result["status"] == "ok"
    assert result["result"] is fake_result
    assert result["active_model"] is None
    restore.assert_called_once_with(
        registry,
        "VERSIONS",
        "ARTIFACTS",
    )
    train.assert_called_once()
    assert train.call_args.kwargs["cutoff_date"] == date(2026, 10, 2)
