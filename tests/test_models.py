from __future__ import annotations

import pytest
from pydantic import ValidationError

from models import ProcurementRecommendation, PurchaseRequest


def test_purchase_request_parses_valid_payload() -> None:
    """A valid PurchaseRequest payload should parse successfully."""
    request = PurchaseRequest(
        request_id="REQ-100",
        requestor="A. Tester",
        cost_center_id="CC-001",
        vendor_name="BlueSky Cloud Solutions",
        vendor_id="V-002",
        category="software_licenses",
        item_description="License renewal",
        quantity=10,
        unit_price=25.0,
        total_amount=250.0,
    )

    assert request.request_id == "REQ-100"
    assert request.total_amount == 250.0


@pytest.mark.parametrize(
    "payload",
    [
        {
            "request_id": "REQ-101",
            "requestor": "A. Tester",
            "cost_center_id": "CC-001",
            "vendor_name": "BlueSky Cloud Solutions",
            "category": "software_licenses",
            "item_description": "License renewal",
            "quantity": 10,
            "unit_price": 25.0,
            "total_amount": 250.0,
        },
        {
            "request_id": "REQ-102",
            "requestor": "A. Tester",
            "cost_center_id": "CC-001",
            "vendor_name": "BlueSky Cloud Solutions",
            "vendor_id": "V-002",
            "category": "software_licenses",
            "item_description": "License renewal",
            "quantity": 0,
            "unit_price": 25.0,
            "total_amount": 0.0,
        },
        {
            "request_id": "REQ-103",
            "requestor": "A. Tester",
            "cost_center_id": "CC-001",
            "vendor_name": "BlueSky Cloud Solutions",
            "vendor_id": "V-002",
            "category": "software_licenses",
            "item_description": "License renewal",
            "quantity": 10,
            "unit_price": 25.0,
            "total_amount": 249.0,
        },
    ],
)
def test_purchase_request_rejects_invalid_payloads(payload: dict[str, object]) -> None:
    """Invalid PurchaseRequest payloads should fail validation."""
    with pytest.raises(ValidationError):
        PurchaseRequest.model_validate(payload)


def test_procurement_recommendation_parses_valid_payload() -> None:
    """A valid ProcurementRecommendation payload should parse successfully."""
    result = ProcurementRecommendation(
        request_id="REQ-100",
        decision="approve",
        rationale="All checks passed with no policy violations.",
    )

    assert result.decision == "approve"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "request_id": "REQ-100",
            "decision": "hold",
            "rationale": "Decision value is invalid.",
        },
        {
            "request_id": "REQ-100",
            "decision": "deny",
            "rationale": "   ",
        },
    ],
)
def test_procurement_recommendation_rejects_invalid_payloads(
    payload: dict[str, str],
) -> None:
    """Invalid recommendation payloads should fail validation."""
    with pytest.raises(ValidationError):
        ProcurementRecommendation.model_validate(payload)
