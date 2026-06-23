from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from data.loader import load_vendors


class VendorRecord(BaseModel):
    """Normalized vendor record used for risk assessment."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    vendor_id: str
    name: str
    contract_status: Literal["active", "expired", "none"]
    compliance_flag: bool
    compliance_notes: str = ""


class RiskAssessmentError(BaseModel):
    """Structured error contract for risk assessment."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    code: Literal["unknown_vendor", "invalid_vendor_data", "data_access_error"]
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class RiskAssessmentResult(BaseModel):
    """Structured output for vendor risk evaluation."""

    model_config = ConfigDict(strict=True)

    vendor_id: str
    compliance_flag: bool
    contract_status: Literal["active", "expired", "none"]
    risk_level: Literal["low", "medium", "high", "critical"]


def assess_risk(vendor_id: str) -> dict[str, Any]:
    """Compute vendor risk level using compliance flag and contract status.

    Args:
        vendor_id: The vendor identifier from the request.

    Returns:
        A structured dictionary.

        Success shape:
            {
                "vendor_id": str,
                "compliance_flag": bool,
                "contract_status": "active" | "expired" | "none",
                "risk_level": "low" | "medium" | "high" | "critical",
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
    try:
        raw_vendors = load_vendors()
    except Exception as exc:
        error = RiskAssessmentError(
            code="data_access_error",
            message=f"Failed to load vendor data: {exc}",
            context={"vendor_id": vendor_id},
        )
        return {"error": error.model_dump()}

    target_vendor: VendorRecord | None = None
    for raw_vendor in raw_vendors:
        try:
            vendor = VendorRecord.model_validate(raw_vendor)
        except ValidationError as exc:
            error = RiskAssessmentError(
                code="invalid_vendor_data",
                message=f"Invalid vendor record encountered: {exc}",
                context={"vendor_id": vendor_id},
            )
            return {"error": error.model_dump()}

        if vendor.vendor_id == vendor_id:
            target_vendor = vendor
            break

    if target_vendor is None:
        error = RiskAssessmentError(
            code="unknown_vendor",
            message="Unknown vendor_id",
            context={"vendor_id": vendor_id},
        )
        return {"error": error.model_dump()}

    if target_vendor.compliance_flag:
        risk_level: Literal["critical", "high", "medium", "low"] = "critical"
    elif target_vendor.contract_status == "expired":
        risk_level = "high"
    elif target_vendor.contract_status == "none":
        risk_level = "medium"
    else:
        risk_level = "low"

    result = RiskAssessmentResult(
        vendor_id=target_vendor.vendor_id,
        compliance_flag=target_vendor.compliance_flag,
        contract_status=target_vendor.contract_status,
        risk_level=risk_level,
    )
    return result.model_dump()