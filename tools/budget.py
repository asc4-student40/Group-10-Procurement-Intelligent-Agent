from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from data.loader import load_budgets


class BudgetRecord(BaseModel):
    """Normalized budget record loaded from mock budget data."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    cost_center_id: str
    name: str
    quarterly_budget: float = Field(ge=0)
    spent_to_date: float = Field(ge=0)
    remaining: float = Field(ge=0)


class BudgetError(BaseModel):
    """Structured, machine-readable budget tool error contract."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    code: Literal[
        "invalid_requested_amount",
        "unknown_cost_center",
        "invalid_budget_data",
        "data_file_not_found",
        "missing_data_key",
        "unexpected_error",
    ]
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class BudgetCheckResult(BaseModel):
    """Structured output for a successful budget evaluation."""

    model_config = ConfigDict(strict=True)

    within_budget: bool
    remaining_budget: float = Field(ge=0)
    overage: float = Field(ge=0)


def check_budget(
    cost_center_id: str,
    total_amount: float | None = None,
    requested_amount: float | None = None,
) -> dict[str, Any]:
    """Evaluate a request amount against the remaining budget for a cost center.

    This function enforces POL-008 budget overage logic by comparing
    requested_amount to the matched cost center's remaining budget from
    data loaded via data.loader.load_budgets.

    Args:
        cost_center_id: The cost center identifier to evaluate.
        total_amount: The total amount requested for the purchase.
        requested_amount: Backward-compatible alias for total_amount.

    Returns:
        A structured dictionary.

        Success shape:
            {
                "within_budget": bool,
                "remaining_budget": float,
                "overage": float,
            }

        Error shape:
            {
                "error": {
                    "code": str,
                    "message": str,
                    "context": dict[str, Any],
                }
            }

        Error codes include:
        - invalid_requested_amount: request amount was not greater than zero.
        - unknown_cost_center: no matching cost_center_id was found in budget data.
        - invalid_budget_data: a loaded budget record failed expected schema checks.
        - data_access_error: budget data could not be loaded or another runtime
          issue occurred while evaluating the request.
    """
    amount = total_amount if total_amount is not None else requested_amount

    if amount is None or amount <= 0:
        error = BudgetError(
            code="invalid_requested_amount",
            message="total_amount must be greater than zero",
            context={
                "cost_center_id": cost_center_id,
                "total_amount": amount,
            },
        )
        return {"error": error.model_dump()}

    try:
        raw_budgets = load_budgets()
    except FileNotFoundError as exc:
        error = BudgetError(
            code="data_file_not_found",
            message=f"Budget data file not found: {exc}",
            context={"cost_center_id": cost_center_id},
        )
        return {"error": error.model_dump()}
    except KeyError as exc:
        error = BudgetError(
            code="missing_data_key",
            message=f"Missing expected key in budget data: {exc}",
            context={"cost_center_id": cost_center_id},
        )
        return {"error": error.model_dump()}
    except Exception as exc:
        error = BudgetError(
            code="unexpected_error",
            message=f"Unexpected budget tool error: {exc}",
            context={"cost_center_id": cost_center_id},
        )
        return {"error": error.model_dump()}

    matched_budget: BudgetRecord | None = None
    for raw_budget in raw_budgets:
        try:
            budget = BudgetRecord.model_validate(raw_budget)
        except ValidationError as exc:
            error = BudgetError(
                code="invalid_budget_data",
                message=f"Invalid budget record encountered: {exc}",
                context={"cost_center_id": cost_center_id},
            )
            return {"error": error.model_dump()}

        if budget.cost_center_id == cost_center_id:
            matched_budget = budget
            break

    if matched_budget is None:
        error = BudgetError(
            code="unknown_cost_center",
            message="Unknown cost_center_id",
            context={"cost_center_id": cost_center_id},
        )
        return {"error": error.model_dump()}

    remaining_budget = matched_budget.remaining
    overage = max(amount - remaining_budget, 0.0)
    result = BudgetCheckResult(
        within_budget=amount <= remaining_budget,
        remaining_budget=remaining_budget,
        overage=overage,
    )
    return result.model_dump()
