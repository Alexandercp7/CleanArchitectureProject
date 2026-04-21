from alerts.evaluation import EvaluationResult


def test_has_error_returns_true_when_error_present() -> None:
    result = EvaluationResult(alert_id="a1", condition_met=False, error="failure")
    assert result.has_error() is True


def test_has_error_returns_false_without_error() -> None:
    result = EvaluationResult(alert_id="a1", condition_met=True)
    assert result.has_error() is False
