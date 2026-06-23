from __future__ import annotations

from data.loader import load_requests
from models import PurchaseRequest
from tools.policy_compliance import check_policy_compliance


def _request_by_id(request_id: str) -> dict[str, object]:
    requests = load_requests()
    for request in requests:
        if request.get("request_id") == request_id:
            return request
    raise AssertionError(f"Request {request_id} not found in mock requests.")


def _get_violation(result: dict[str, object], policy_id: str) -> dict[str, str]:
    violations = result["violations"]
    assert isinstance(violations, list)
    for violation in violations:
        assert isinstance(violation, dict)
        if violation.get("policy_id") == policy_id:
            return violation
    raise AssertionError(f"Policy violation {policy_id} not found.")


def test_pol004_catering_prohibition_req009_denies() -> None:
    """REQ-009: Catering requests must be denied regardless of amount."""
    result = check_policy_compliance(
        PurchaseRequest(
            request_id="REQ-009",
            requestor="P. Harrington",
            cost_center_id="CC-005",
            vendor_name="Summit Catering Co.",
            vendor_id="V-017",
            category="catering",
            item_description="Executive leadership offsite lunch service (3 days)",
            quantity=1,
            unit_price=3200.0,
            total_amount=3200.0,
        )
    )

    assert "error" not in result
    violation = _get_violation(result, "POL-004")
    assert violation["forced_decision"] == "deny"
    assert isinstance(violation["violated_rule"], str)
    assert violation["violated_rule"]


def test_pol002_manager_approval_threshold_escalates() -> None:
    """POL-002: Any request from $10,000 to $49,999 must escalate for approval."""
    req_002 = PurchaseRequest.model_validate(_request_by_id("REQ-002"))

    result = check_policy_compliance(req_002)

    assert "error" not in result
    violation = _get_violation(result, "POL-002")
    assert violation["forced_decision"] == "escalate"
    assert isinstance(violation["violated_rule"], str)
    assert violation["violated_rule"]


def test_pol005_expired_contract_vendor_req007_denies() -> None:
    """REQ-007: Expired contract vendor Crestview Print must be denied."""
    req_007 = PurchaseRequest.model_validate(_request_by_id("REQ-007"))

    result = check_policy_compliance(req_007)

    assert "error" not in result
    violation = _get_violation(result, "POL-005")
    assert violation["forced_decision"] == "deny"
    assert isinstance(violation["violated_rule"], str)
    assert violation["violated_rule"]


def test_pol001_single_source_violation_denies() -> None:
    """REQ-008 includes a POL-001 single-source violation above threshold."""
    req_008 = PurchaseRequest.model_validate(_request_by_id("REQ-008"))

    result = check_policy_compliance(req_008)

    assert "error" not in result
    violation = _get_violation(result, "POL-001")
    assert violation["forced_decision"] == "deny"


def test_pol003_director_threshold_escalates() -> None:
    """POL-003 should escalate for requests at or above $50,000."""
    request = PurchaseRequest(
        request_id="REQ-900",
        requestor="A. Reviewer",
        cost_center_id="CC-004",
        vendor_name="Pinnacle Hardware",
        vendor_id="V-005",
        category="hardware",
        item_description="Director threshold validation",
        quantity=1,
        unit_price=50_000.0,
        total_amount=50_000.0,
    )

    result = check_policy_compliance(request)

    assert "error" not in result
    violation = _get_violation(result, "POL-003")
    assert violation["forced_decision"] == "escalate"


def test_pol006_compliance_flag_vendor_escalates() -> None:
    """REQ-011 includes a compliance-flagged vendor and should escalate via POL-006."""
    req_011 = PurchaseRequest.model_validate(_request_by_id("REQ-011"))

    result = check_policy_compliance(req_011)

    assert "error" not in result
    violation = _get_violation(result, "POL-006")
    assert violation["forced_decision"] == "escalate"


def test_pol007_staffing_non_contracted_over_40_hours_denies() -> None:
    """POL-007 denies staffing requests over 40 hours for non-contracted vendors."""
    request = PurchaseRequest(
        request_id="REQ-901",
        requestor="A. Reviewer",
        cost_center_id="CC-002",
        vendor_name="Clearpath Training Solutions",
        vendor_id="V-015",
        category="staffing",
        item_description="Staffing surge coverage",
        quantity=120,
        unit_price=38.5,
        total_amount=4_620.0,
    )

    result = check_policy_compliance(request)

    assert "error" not in result
    violation = _get_violation(result, "POL-007")
    assert violation["forced_decision"] == "deny"


def test_pol008_budget_overage_denies() -> None:
    """REQ-006 exceeds budget and should trigger POL-008 deny."""
    req_006 = PurchaseRequest.model_validate(_request_by_id("REQ-006"))

    result = check_policy_compliance(req_006)

    assert "error" not in result
    violation = _get_violation(result, "POL-008")
    assert violation["forced_decision"] == "deny"


def test_policy_compliance_returns_empty_violations_when_none_apply() -> None:
    """REQ-003 should produce no policy violations."""
    req_003 = PurchaseRequest.model_validate(_request_by_id("REQ-003"))

    result = check_policy_compliance(req_003)

    assert "error" not in result
    assert result["violations"] == []
    assert result["violation_count"] == 0


def test_policy_compliance_returns_structured_error_for_invalid_request() -> None:
    """Invalid request payloads should return invalid_request errors."""
    result = check_policy_compliance({"request_id": "REQ-404"})

    assert "error" in result
    assert result["error"]["code"] == "invalid_request"
