## 1. Model Contract Definition

- [x] 1.1 Define `PurchaseRequest` with required fields and declared field types in the canonical models module.
- [x] 1.2 Add numeric constraints for `quantity`, `unit_price`, and `total_amount` (`gt=0`).
- [x] 1.3 Add cross-field validation for `total_amount` consistency with `quantity * unit_price`.
- [x] 1.4 Define `ProcurementRecommendation` with required `request_id`, `decision`, and `rationale` fields.
- [x] 1.5 Restrict `decision` to the literals `approve`, `deny`, and `escalate`.
- [x] 1.6 Enforce non-empty `rationale` after whitespace normalization.

## 2. Validation and Agent Contract Alignment

- [x] 2.1 Ensure model-level string normalization is applied consistently for both models.
- [x] 2.2 Verify the agent output contract remains typed to `ProcurementRecommendation`.
- [x] 2.3 Ensure unsupported outcome values fail model validation before downstream use.

## 3. Test Coverage and Verification

- [x] 3.1 Add or update tests for valid `PurchaseRequest` payload parsing.
- [x] 3.2 Add or update tests for invalid `PurchaseRequest` cases (missing fields, bad types, non-positive values, mismatched total).
- [x] 3.3 Add or update tests for valid `ProcurementRecommendation` parsing.
- [x] 3.4 Add or update tests for invalid `ProcurementRecommendation` cases (invalid decision, blank rationale).
- [x] 3.5 Run the test suite and confirm all model-related tests pass.