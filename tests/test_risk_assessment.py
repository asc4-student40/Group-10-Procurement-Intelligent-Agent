from __future__ import annotations

from tools.risk_assessment import assess_risk


def test_assess_risk_returns_critical_for_compliance_flagged_vendor() -> None:
    """POL risk rule: compliance-flagged vendors are critical risk."""
    result = assess_risk("V-006")

    assert "error" not in result
    assert result["compliance_flag"] is True
    assert result["contract_status"] == "active"
    assert result["risk_level"] == "critical"


def test_assess_risk_returns_high_for_expired_contract_vendor() -> None:
    """Expired contracts should produce high risk when no compliance flag exists."""
    result = assess_risk("V-010")

    assert "error" not in result
    assert result["compliance_flag"] is False
    assert result["contract_status"] == "expired"
    assert result["risk_level"] == "high"


def test_assess_risk_returns_medium_for_vendor_with_no_contract() -> None:
    """Vendors with no contract should produce medium risk."""
    result = assess_risk("V-012")

    assert "error" not in result
    assert result["compliance_flag"] is False
    assert result["contract_status"] == "none"
    assert result["risk_level"] == "medium"


def test_assess_risk_returns_low_for_active_compliant_vendor() -> None:
    """Active compliant vendors should produce low risk."""
    result = assess_risk("V-002")

    assert "error" not in result
    assert result["compliance_flag"] is False
    assert result["contract_status"] == "active"
    assert result["risk_level"] == "low"


def test_assess_risk_returns_structured_error_for_unknown_vendor() -> None:
    """Unknown vendor IDs should return a structured unknown_vendor error."""
    result = assess_risk("V-999")

    assert "error" in result
    assert result["error"]["code"] == "unknown_vendor"
