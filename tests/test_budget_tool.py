from __future__ import annotations

from tools.budget import check_budget


def test_check_budget_returns_success_shape_for_valid_cost_center() -> None:
    """check_budget returns required fields for a valid budget evaluation."""
    result = check_budget(cost_center_id="CC-001", total_amount=100.0)

    assert "error" not in result
    assert result["within_budget"] is True
    assert result["remaining_budget"] == 187550.0
    assert result["overage"] == 0.0


def test_check_budget_returns_structured_error_for_unknown_cost_center() -> None:
    """Unknown cost center should return structured error payload."""
    result = check_budget(cost_center_id="CC-999", total_amount=100.0)

    assert "error" in result
    assert result["error"]["code"] == "unknown_cost_center"


def test_check_budget_rejects_non_positive_amount() -> None:
    """Non-positive amount should return invalid_requested_amount error."""
    result = check_budget(cost_center_id="CC-001", total_amount=0.0)

    assert "error" in result
    assert result["error"]["code"] == "invalid_requested_amount"
