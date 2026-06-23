from __future__ import annotations

from tools.vendor_duplication import check_vendor_duplication


def test_req_008_vendor_duplication_detects_expected_conflicts() -> None:
    """REQ-008: NovaPrint office_supplies request above threshold triggers POL-001 conflict."""
    result = check_vendor_duplication(
        vendor_id="V-012",
        category="office_supplies",
        total_amount=28_500.0,
    )

    assert "error" not in result
    assert result["duplication_conflict"] is True
    assert result["single_source_violation"] is True
    assert result["forced_decision"] == "deny"
    assert set(result["conflicting_vendor_ids"]) == {"V-001", "V-003"}


def test_vendor_duplication_threshold_boundary_does_not_trigger_deny() -> None:
    """Exactly at POL-001 threshold should not trigger deny recommendation."""
    result = check_vendor_duplication(
        vendor_id="V-012",
        category="office_supplies",
        total_amount=25_000.0,
    )

    assert "error" not in result
    assert result["duplication_conflict"] is True
    assert result["single_source_violation"] is False
    assert result["forced_decision"] is None


def test_vendor_duplication_rejects_negative_total_amount() -> None:
    """Negative amount should return structured invalid_total_amount error."""
    result = check_vendor_duplication(
        vendor_id="V-012",
        category="office_supplies",
        total_amount=-1.0,
    )

    assert "error" in result
    assert result["error"]["code"] == "invalid_total_amount"
