from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from data.loader import load_vendors

POL001_THRESHOLD = 25_000.0


class VendorRecord(BaseModel):
    """Normalized vendor record loaded from mock vendor data."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    vendor_id: str
    name: str
    category: str
    contract_status: Literal["active", "expired", "none"]
    contract_id: str


class VendorDuplicationError(BaseModel):
    """Structured error contract for vendor duplication checks."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    code: Literal["invalid_total_amount", "invalid_vendor_data", "data_access_error"]
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class ConflictingContract(BaseModel):
    """Contract details for each conflicting active vendor."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    vendor_id: str
    contract_id: str
    contract_status: Literal["active"]


class VendorDuplicationResult(BaseModel):
    """Structured output for a successful vendor duplication evaluation."""

    model_config = ConfigDict(strict=True)

    duplication_conflict: bool
    policy_reference: str
    pol001_threshold: float = Field(ge=0)
    total_amount: float = Field(ge=0)
    single_source_violation: bool
    forced_decision: Literal["deny"] | None
    conflicting_vendor_ids: list[str]
    conflicting_contracts: list[ConflictingContract]


def check_vendor_duplication(
    vendor_id: str,
    category: str,
    total_amount: float,
) -> dict[str, Any]:
    """Check POL-001 single-source conflict conditions for a vendor/category request.

    POL-001 deny logic is activated only when:
    - the request total_amount exceeds $25,000, and
    - at least one different vendor has an active contract in the same category.

    Args:
        vendor_id: The requested vendor identifier.
        category: The request category to evaluate.
        total_amount: The total request amount in USD.

    Returns:
        A structured dictionary.

        Success shape includes:
            {
                "duplication_conflict": bool,
                "policy_reference": "POL-001",
                "pol001_threshold": 25000.0,
                "total_amount": float,
                "single_source_violation": bool,
                "forced_decision": "deny" | None,
                "conflicting_vendor_ids": list[str],
                "conflicting_contracts": list[{
                    "vendor_id": str,
                    "contract_id": str,
                    "contract_status": "active",
                }],
            }

        Error shape:
            {
                "error": {
                    "code": str,
                    "message": str,
                    "context": dict[str, Any],
                }
            }
    """
    if total_amount < 0:
        error = VendorDuplicationError(
            code="invalid_total_amount",
            message="total_amount must be non-negative",
            context={
                "vendor_id": vendor_id,
                "category": category,
                "total_amount": total_amount,
            },
        )
        return {"error": error.model_dump()}

    try:
        raw_vendors = load_vendors()
    except Exception as exc:
        error = VendorDuplicationError(
            code="data_access_error",
            message=f"Failed to load vendor data: {exc}",
            context={"vendor_id": vendor_id, "category": category},
        )
        return {"error": error.model_dump()}

    conflicts: list[ConflictingContract] = []
    for raw_vendor in raw_vendors:
        try:
            vendor = VendorRecord.model_validate(raw_vendor)
        except ValidationError as exc:
            error = VendorDuplicationError(
                code="invalid_vendor_data",
                message=f"Invalid vendor record encountered: {exc}",
                context={"vendor_id": vendor_id, "category": category},
            )
            return {"error": error.model_dump()}

        is_conflict = (
            vendor.vendor_id != vendor_id
            and vendor.category == category
            and vendor.contract_status == "active"
        )
        if is_conflict:
            conflicts.append(
                ConflictingContract(
                    vendor_id=vendor.vendor_id,
                    contract_id=vendor.contract_id,
                    contract_status="active",
                )
            )

    duplication_conflict = len(conflicts) > 0
    threshold_exceeded = total_amount > POL001_THRESHOLD
    single_source_violation = duplication_conflict and threshold_exceeded

    result = VendorDuplicationResult(
        duplication_conflict=duplication_conflict,
        policy_reference="POL-001",
        pol001_threshold=POL001_THRESHOLD,
        total_amount=total_amount,
        single_source_violation=single_source_violation,
        forced_decision="deny" if single_source_violation else None,
        conflicting_vendor_ids=[conflict.vendor_id for conflict in conflicts],
        conflicting_contracts=conflicts,
    )
    return result.model_dump()
