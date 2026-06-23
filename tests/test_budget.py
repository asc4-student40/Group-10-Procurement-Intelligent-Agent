from __future__ import annotations

from tools.budget import check_budget


def test_check_budget_cc003_within_and_over_budget() -> None:
    """check_budget should classify CC-003 requests as within or over budget correctly."""
    within_result = check_budget(cost_center_id="CC-003", total_amount=6900.0)
    over_result = check_budget(cost_center_id="CC-003", total_amount=7000.0)

    assert "error" not in within_result
    assert within_result["within_budget"] is True
    assert within_result["remaining_budget"] == 6900.0
    assert within_result["overage"] == 0.0

    assert "error" not in over_result
    assert over_result["within_budget"] is False
    assert over_result["remaining_budget"] == 6900.0
    assert over_result["overage"] == 100.0

