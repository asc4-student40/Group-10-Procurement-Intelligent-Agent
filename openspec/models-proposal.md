# OpenSpec Proposal: Pydantic v2 Procurement Models

## Change Summary
Define two Pydantic v2 models for the procurement agent contract:
- `PurchaseRequest` as the structured input payload
- `ProcurementRecommendation` as the structured output payload

This proposal establishes field-level schema requirements, validation constraints, and decision value restrictions for consistent agent behavior and testability.

## Why
- Enforces a stable typed interface between tools, agent logic, and tests.
- Prevents malformed requests (invalid quantities, prices, totals, or missing identifiers).
- Guarantees output decisions remain in policy-approved outcomes only.
- Aligns implementation with project conventions requiring Pydantic v2 structured models.

## Scope
- In scope: model definitions, field names, Python types, validation constraints, and allowed values for `decision`.
- Out of scope: changes to mock data files, procurement policy logic, and tool execution flow.

## Specification

### Model 1: `PurchaseRequest` (Input)

Purpose: Represents a single procurement request consumed by the agent.

Global model behavior:
- `str_strip_whitespace = True` (via Pydantic v2 `ConfigDict`) for all string fields.

Field contract:

| Field | Type | Required | Constraints | Notes |
| --- | --- | --- | --- | --- |
| `request_id` | `str` | Yes | Non-empty after whitespace stripping | Unique request identifier, e.g. `REQ-001` |
| `requestor` | `str` | Yes | Non-empty after whitespace stripping | Employee/requestor display name |
| `cost_center_id` | `str` | Yes | Non-empty after whitespace stripping | Cost center key, e.g. `CC-001` |
| `vendor_name` | `str` | Yes | Non-empty after whitespace stripping | Human-readable vendor name |
| `vendor_id` | `str` | Yes | Non-empty after whitespace stripping | Vendor identifier, e.g. `V-006` |
| `category` | `str` | Yes | Non-empty after whitespace stripping | Procurement category slug |
| `item_description` | `str` | Yes | Non-empty after whitespace stripping | Free-form purchase description |
| `quantity` | `int` | Yes | `gt=0` | Must be strictly positive |
| `unit_price` | `float` | Yes | `gt=0` | Unit cost in USD |
| `total_amount` | `float` | Yes | `gt=0` | Gross cost in USD |

Cross-field validation rules:
- `total_amount` must equal `quantity * unit_price` within a small floating-point tolerance (recommended tolerance: `abs(total_amount - quantity * unit_price) <= 0.01`).
- Reject payloads with any missing required field.

Data handling notes:
- Fields present in mock request records such as `expected_outcome` and `outcome_reason` are not part of the input model contract.

### Model 2: `ProcurementRecommendation` (Output)

Purpose: Represents the agent's final structured recommendation.

Global model behavior:
- `str_strip_whitespace = True` (via Pydantic v2 `ConfigDict`) for all string fields.

Field contract:

| Field | Type | Required | Constraints | Notes |
| --- | --- | --- | --- | --- |
| `request_id` | `str` | Yes | Non-empty after whitespace stripping | Must reference originating `PurchaseRequest.request_id` |
| `decision` | `Literal["approve", "deny", "escalate"]` | Yes | Must be exactly one allowed literal | Policy-allowed outcomes only |
| `rationale` | `str` | Yes | Non-empty after whitespace stripping | Human-readable explanation referencing checks/policies |

Allowed decision values:
- `approve`
- `deny`
- `escalate`

Validation rules:
- `rationale` must fail validation if blank after trimming whitespace.
- `decision` must fail validation for any value outside `approve`, `deny`, or `escalate`.
- `request_id` must be populated and traceable to the input request.

## Acceptance Criteria
1. A Pydantic v2 `PurchaseRequest` model exists with all listed fields, required status, and constraints.
2. A Pydantic v2 `ProcurementRecommendation` model exists with enforced `decision` literals and non-empty `rationale`.
3. Invalid payloads violating numeric or required-string constraints raise validation errors.
4. Output payloads with invalid `decision` values or blank `rationale` raise validation errors.
5. Model behavior is compatible with agent structured output requirements.

## Implementation Notes
- Use `pydantic.BaseModel`, `pydantic.Field`, `pydantic.ConfigDict`, and Pydantic v2 validators.
- Keep model definitions in the project's canonical models module.
- Add tests for success and failure paths for both models.