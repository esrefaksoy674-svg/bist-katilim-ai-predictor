from app.services.context_shadow_evaluation import run_context_shadow_evaluation


def test_shadow_evaluation_waits_until_minimum_context_history_exists():
    class Repository:
        def all(self):
            return [{"symbol": "AAA", "available_date": "2026-10-02"}]

    result = run_context_shadow_evaluation(
        repository=Repository(),
        minimum_context_dates=60,
    )

    assert result["status"] == "collecting_context"
    assert result["context_date_count"] == 1
    assert result["minimum_context_dates"] == 60
