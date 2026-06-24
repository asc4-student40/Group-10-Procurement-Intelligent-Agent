from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from data.loader import load_budgets, load_policies, load_vendors
from models import PurchaseRequest


class PolicyRecord(BaseModel):
    """Normalized policy record loaded from mock policy data."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    policy_id: Literal[
        "POL-001",
        "POL-002",
        "POL-003",
        "POL-004",
        "POL-005",
        "POL-006",
        "POL-007",
        "POL-008",
    ]
    description: str
    threshold_amount: float = Field(ge=0)
    upper_threshold: float | None = Field(default=None, ge=0)
    affected_categories: list[str] = Field(default_factory=list)


class VendorRecord(BaseModel):
    """Normalized vendor record used for policy evaluation."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    vendor_id: str
    name: str
    category: str
    contract_status: Literal["active", "expired", "none"]
    contract_id: str
    compliance_flag: bool


class BudgetRecord(BaseModel):
    """Normalized budget record used for budget overage checks."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    cost_center_id: str
    remaining: float = Field(ge=0)


class PolicyViolation(BaseModel):
    """Structured policy violation output contract."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    policy_id: str
    violated_rule: str
    forced_decision: Literal["deny", "escalate"]


class PolicyComplianceError(BaseModel):
    """Structured error contract for policy compliance checks."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    code: Literal[
        "invalid_request",
        "invalid_policy_data",
        "invalid_vendor_data",
        "invalid_budget_data",
        "data_file_not_found",
        "missing_data_key",
        "unexpected_error",
    ]
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class PolicyComplianceResult(BaseModel):
    """Structured result containing policy violations for a purchase request."""

    model_config = ConfigDict(strict=True)

    violations: list[PolicyViolation]
    violation_count: int = Field(ge=0)
    evaluated_policy_ids: list[str]


def _violation(
    policy_id: str,
    violated_rule: str,
    forced_decision: Literal["deny", "escalate"],
) -> PolicyViolation:
    return PolicyViolation(
        policy_id=policy_id,
        violated_rule=violated_rule,
        forced_decision=forced_decision,
    )


def check_policy_compliance(
    request: PurchaseRequest | dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a purchase request against POL-001 through POL-008.

    Args:
        request: A PurchaseRequest instance or payload that can be validated as one.

    Returns:
        A structured dictionary.

        Success shape:
            {
                "violations": [
                    {
                        "policy_id": str,
                        "violated_rule": str,
                        "forced_decision": "deny" | "escalate",
                    }
                ],
                "violation_count": int,
                "evaluated_policy_ids": list[str],
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
        purchase_request = (
            request
            if isinstance(request, PurchaseRequest)
            else PurchaseRequest.model_validate(request)
        )
    except ValidationError as exc:
        error = PolicyComplianceError(
            code="invalid_request",
            message=f"Invalid request payload: {exc}",
            context={"request": request if isinstance(request, dict) else request.model_dump()},
        )
        return {"error": error.model_dump()}

    try:
        raw_policies = load_policies()
        raw_vendors = load_vendors()
        raw_budgets = load_budgets()
    except FileNotFoundError as exc:
        error = PolicyComplianceError(
            code="data_file_not_found",
            message=f"Policy dependency data file not found: {exc}",
            context={"request_id": purchase_request.request_id},
        )
        return {"error": error.model_dump()}
    except KeyError as exc:
        error = PolicyComplianceError(
            code="missing_data_key",
            message=f"Missing expected key in policy dependency data: {exc}",
            context={"request_id": purchase_request.request_id},
        )
        return {"error": error.model_dump()}
    except Exception as exc:
        error = PolicyComplianceError(
            code="unexpected_error",
            message=f"Unexpected policy compliance error: {exc}",
            context={"request_id": purchase_request.request_id},
        )
        return {"error": error.model_dump()}

    policies: list[PolicyRecord] = []
    for raw_policy in raw_policies:
        try:
            policies.append(PolicyRecord.model_validate(raw_policy))
        except ValidationError as exc:
            error = PolicyComplianceError(
                code="invalid_policy_data",
                message=f"Invalid policy record encountered: {exc}",
                context={"request_id": purchase_request.request_id},
            )
            return {"error": error.model_dump()}

    vendors: list[VendorRecord] = []
    for raw_vendor in raw_vendors:
        try:
            vendors.append(VendorRecord.model_validate(raw_vendor))
        except ValidationError as exc:
            error = PolicyComplianceError(
                code="invalid_vendor_data",
                message=f"Invalid vendor record encountered: {exc}",
                context={"request_id": purchase_request.request_id},
            )
            return {"error": error.model_dump()}

    budgets: list[BudgetRecord] = []
    for raw_budget in raw_budgets:
        try:
            budgets.append(BudgetRecord.model_validate(raw_budget))
        except ValidationError as exc:
            error = PolicyComplianceError(
                code="invalid_budget_data",
                message=f"Invalid budget record encountered: {exc}",
                context={"request_id": purchase_request.request_id},
            )
            return {"error": error.model_dump()}

    requested_vendor = next(
        (vendor for vendor in vendors if vendor.vendor_id == purchase_request.vendor_id),
        None,
    )

    violations: list[PolicyViolation] = []
    evaluated_policy_ids = [policy.policy_id for policy in policies]

    for policy in policies:
        if policy.policy_id == "POL-001":
            active_conflicts = [
                vendor
                for vendor in vendors
                if vendor.vendor_id != purchase_request.vendor_id
                and vendor.category == purchase_request.category
                and vendor.contract_status == "active"
            ]
            requested_vendor_is_contracted = (
                requested_vendor is not None
                and requested_vendor.category == purchase_request.category
                and requested_vendor.contract_status == "active"
            )
            if (
                purchase_request.total_amount > policy.threshold_amount
                and purchase_request.category in policy.affected_categories
                and active_conflicts
                and not requested_vendor_is_contracted
            ):
                violations.append(
                    _violation(
                        policy_id="POL-001",
                        violated_rule=(
                            f"{policy.description} Conflicting active vendors: "
                            + ", ".join(vendor.vendor_id for vendor in active_conflicts)
                            + "."
                        ),
                        forced_decision="deny",
                    )
                )

        elif policy.policy_id == "POL-002":
            if policy.upper_threshold is not None:
                upper = policy.upper_threshold
            else:
                upper = policy.threshold_amount
            if policy.threshold_amount <= purchase_request.total_amount <= upper:
                amount_text = f"${purchase_request.total_amount:,.2f}"
                violations.append(
                    _violation(
                        policy_id="POL-002",
                        violated_rule=(
                            f"{policy.description} Request amount {amount_text} "
                            f"is within the manager-approval range ${policy.threshold_amount:,.2f} "
                            f"to ${upper:,.2f}."
                        ),
                        forced_decision="escalate",
                    )
                )

        elif policy.policy_id == "POL-003":
            if purchase_request.total_amount >= policy.threshold_amount:
                amount_text = f"${purchase_request.total_amount:,.2f}"
                violations.append(
                    _violation(
                        policy_id="POL-003",
                        violated_rule=(
                            f"{policy.description} Request amount {amount_text} "
                            f"meets or exceeds ${policy.threshold_amount:,.2f}."
                        ),
                        forced_decision="escalate",
                    )
                )

        elif policy.policy_id == "POL-004":
            if purchase_request.category in policy.affected_categories:
                violations.append(
                    _violation(
                        policy_id="POL-004",
                        violated_rule=policy.description,
                        forced_decision="deny",
                    )
                )

        elif policy.policy_id == "POL-005":
            if requested_vendor is not None and requested_vendor.contract_status == "expired":
                violations.append(
                    _violation(
                        policy_id="POL-005",
                        violated_rule=(
                            f"{policy.description} Vendor {requested_vendor.vendor_id} has "
                            f"expired contract {requested_vendor.contract_id}."
                        ),
                        forced_decision="deny",
                    )
                )

        elif policy.policy_id == "POL-006":
            if requested_vendor is not None and requested_vendor.compliance_flag:
                violations.append(
                    _violation(
                        policy_id="POL-006",
                        violated_rule=policy.description,
                        forced_decision="escalate",
                    )
                )

        elif policy.policy_id == "POL-007":
            requested_vendor_is_active_staffing = (
                requested_vendor is not None
                and requested_vendor.category == "staffing"
                and requested_vendor.contract_status == "active"
            )
            if (
                purchase_request.category in policy.affected_categories
                and purchase_request.quantity > 40
                and not requested_vendor_is_active_staffing
            ):
                violations.append(
                    _violation(
                        policy_id="POL-007",
                        violated_rule=(
                            f"{policy.description} Quantity {purchase_request.quantity} exceeds 40."
                        ),
                        forced_decision="deny",
                    )
                )

        elif policy.policy_id == "POL-008":
            matched_budget = next(
                (
                    budget
                    for budget in budgets
                    if budget.cost_center_id == purchase_request.cost_center_id
                ),
                None,
            )
            if (
                matched_budget is not None
                and purchase_request.total_amount > matched_budget.remaining
            ):
                overage = purchase_request.total_amount - matched_budget.remaining
                remaining_text = f"${matched_budget.remaining:,.2f}"
                violations.append(
                    _violation(
                        policy_id="POL-008",
                        violated_rule=(
                            f"{policy.description} Remaining budget is {remaining_text}; "
                            f"request exceeds by ${overage:,.2f}."
                        ),
                        forced_decision="deny",
                    )
                )

    result = PolicyComplianceResult(
        violations=violations,
        violation_count=len(violations),
        evaluated_policy_ids=evaluated_policy_ids,
    )
    return result.model_dump()
