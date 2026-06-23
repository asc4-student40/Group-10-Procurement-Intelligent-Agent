from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PurchaseRequest(BaseModel):
    """Validated input model for a procurement purchase request.

    Enforces required request fields, positive numeric amounts, strict typing,
    and consistency between total_amount and quantity multiplied by unit_price.
    """
    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    request_id: str
    requestor: str
    cost_center_id: str
    vendor_name: str
    vendor_id: str
    category: str
    item_description: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    total_amount: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_total_amount(self) -> PurchaseRequest:
        """Validate total_amount against quantity * unit_price within a 0.01 tolerance.

        Raises:
            ValueError: If total_amount differs from the computed amount by more than 0.01.
        """
        expected_total = self.quantity * self.unit_price
        if abs(self.total_amount - expected_total) > 0.01:
            raise ValueError("total_amount must equal quantity * unit_price within 0.01")
        return self


class ProcurementRecommendation(BaseModel):
    """Structured output model for procurement decision recommendations.

    Restricts decision to approve, deny, or escalate, and requires a
    non-empty rationale for every recommendation.
    """
    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    request_id: str
    decision: Literal["approve", "deny", "escalate"]
    rationale: str

    @field_validator("rationale")
    @classmethod
    def validate_rationale(cls, value: str) -> str:
        """Validate that rationale is non-empty after whitespace normalization.

        Raises:
            ValueError: If rationale is empty.
        """
        if not value:
            raise ValueError("rationale must be non-empty")
        return value