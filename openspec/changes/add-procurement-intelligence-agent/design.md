## Context

The procurement agent consumes request records and emits a structured recommendation used by
downstream tooling and tests. Current project conventions require Pydantic v2 models and strict
typed output from the agent. Without a formal model contract, validation behavior can drift and
produce inconsistent outcomes between runtime execution and test assertions.

## Goals / Non-Goals

**Goals:**
- Define deterministic schema contracts for request input and recommendation output.
- Standardize field-level validation for numeric, string, and enum-like constraints.
- Ensure decision output is restricted to policy-approved values only.
- Make validation behavior explicit enough to map directly to unit tests.

**Non-Goals:**
- Expanding procurement policy logic beyond the defined POL-001 through POL-008 tool checks.
- Modifying source fixture data in mock_data.
- Redesigning tool orchestration or agent prompt strategy.

## Decisions

1. Use two dedicated Pydantic v2 models as the contract surface.
   - Decision: `PurchaseRequest` for inbound payloads and `ProcurementRecommendation` for outbound
     agent responses.
   - Rationale: Keeps input/output concerns separated and testable.
   - Alternative considered: A single combined model with optional fields.
   - Why not alternative: Blurs boundaries, weakens validation clarity, and complicates consumers.

2. Enforce whitespace normalization for all string fields.
   - Decision: Use model-level string stripping via `ConfigDict(str_strip_whitespace=True)`.
   - Rationale: Prevents accidental blank strings and inconsistent values.
   - Alternative considered: Per-field manual trimming.
   - Why not alternative: Repetitive and more error-prone.

3. Constrain recommendation decisions with literals.
   - Decision: Restrict `decision` to `approve`, `deny`, or `escalate`.
   - Rationale: Matches governance constraints and prevents unsupported statuses.
   - Alternative considered: Open string with runtime post-validation.
   - Why not alternative: Defers errors and increases downstream risk.

4. Validate numeric amounts and amount consistency.
   - Decision: Require `quantity`, `unit_price`, and `total_amount` to be greater than zero, and
     validate `total_amount` against `quantity * unit_price` with tolerance.
   - Rationale: Catches malformed requests early while accommodating floating-point precision.
   - Alternative considered: Validate only positive numbers.
   - Why not alternative: Misses common data-quality errors in totals.

5. Require non-empty rationale in outputs.
   - Decision: Validate trimmed rationale to reject blank values.
   - Rationale: Ensures recommendation outputs are explainable and auditable.
   - Alternative considered: Allow empty rationale and rely on caller checks.
   - Why not alternative: Violates project behavior requirements and weakens traceability.

## Risks / Trade-offs

- [Risk] Strict validation could reject legacy or loosely formatted input payloads.
  -> Mitigation: Keep model requirements documented and add clear test fixtures for accepted format.
- [Risk] Cross-field amount checks may surface floating-point artifacts.
  -> Mitigation: Use a small tolerance threshold for amount comparison.
- [Trade-off] Strong schema constraints reduce flexibility for ad hoc fields.
  -> Mitigation: Treat schema evolution as explicit spec changes rather than permissive parsing.

## Migration Plan

1. Align model definitions with this spec in the canonical models module.
2. Add or update model tests to cover valid and invalid payload paths.
3. Ensure agent output typing remains bound to `ProcurementRecommendation`.
4. Run validation and test suite prior to review.

Rollback strategy:
- Revert model changes to prior stable definitions while preserving tests that capture the intended
  contract, then reintroduce constraints incrementally.

## Open Questions

- Should identifier fields enforce pattern checks (for example, `REQ-###`, `CC-###`, `V-###`) now,
  or remain free-form non-empty strings for this iteration?
- Should currency values move to fixed-point `Decimal` in a future change for stricter financial
  arithmetic?