## Why

The procurement agent needs a strict, shared data contract for request input and recommendation
output to ensure deterministic validation and reliable structured responses. Defining these
Pydantic v2 models now reduces schema drift between agent logic, tools, and tests as the project
moves toward review and release gates.

## What Changes

- Define a canonical `PurchaseRequest` input model with explicit required fields, types, and
  numeric validations.
- Define a canonical `ProcurementRecommendation` output model with constrained decision values
  and required rationale.
- Enforce allowed decision outcomes to exactly: `approve`, `deny`, `escalate`.
- Add cross-field validation guidance for request amount consistency (`total_amount` vs
  `quantity * unit_price`).
- Establish acceptance criteria for validation failures on malformed payloads.

## Capabilities

### New Capabilities
- `procurement-model-contracts`: Defines and validates the structured input/output schema for
  procurement agent interactions.

### Modified Capabilities
- None.

## Impact

- Affected code: model definitions in the canonical models module and tests validating model
  constraints.
- Affected APIs: agent input/output contract for request ingestion and structured recommendation
  output.
- Dependencies: Pydantic v2 validation primitives and typed literals for decision constraints.
- Systems: procurement agent runtime behavior, test harnesses, and tool-call interfaces that
  consume/emit these models.