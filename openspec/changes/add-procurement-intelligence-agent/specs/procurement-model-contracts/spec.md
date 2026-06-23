## ADDED Requirements

### Requirement: PurchaseRequest input schema
The system SHALL define a `PurchaseRequest` Pydantic v2 model for procurement request input with
the required fields: `request_id`, `requestor`, `cost_center_id`, `vendor_name`, `vendor_id`,
`category`, `item_description`, `quantity`, `unit_price`, and `total_amount`.

#### Scenario: Accept valid purchase request
- **WHEN** a request payload provides all required fields with valid values
- **THEN** the payload is parsed successfully into a `PurchaseRequest` instance

#### Scenario: Reject missing required field
- **WHEN** a request payload omits any required `PurchaseRequest` field
- **THEN** validation fails with a required-field error

### Requirement: PurchaseRequest field type and numeric validation
The system SHALL enforce `PurchaseRequest` field types as strings for identifier/description
fields, integer for `quantity`, and numeric for `unit_price` and `total_amount`. The system SHALL
require `quantity > 0`, `unit_price > 0`, and `total_amount > 0`.

#### Scenario: Reject non-positive numeric values
- **WHEN** `quantity`, `unit_price`, or `total_amount` is less than or equal to zero
- **THEN** validation fails for the corresponding field constraint

#### Scenario: Reject type-incompatible payload
- **WHEN** a payload provides values incompatible with required field types
- **THEN** validation fails with type-related errors

### Requirement: PurchaseRequest amount consistency
The system SHALL validate cross-field consistency such that `total_amount` equals
`quantity * unit_price` within an acceptable rounding tolerance.

#### Scenario: Reject inconsistent computed total
- **WHEN** `total_amount` differs from `quantity * unit_price` beyond tolerance
- **THEN** validation fails indicating amount inconsistency

### Requirement: ProcurementRecommendation output schema
The system SHALL define a `ProcurementRecommendation` Pydantic v2 model with required fields:
`request_id`, `decision`, and `rationale`.

#### Scenario: Accept valid recommendation payload
- **WHEN** a recommendation payload includes populated required fields with valid values
- **THEN** the payload is parsed successfully into a `ProcurementRecommendation` instance

#### Scenario: Reject missing recommendation field
- **WHEN** a recommendation payload omits `request_id`, `decision`, or `rationale`
- **THEN** validation fails with a required-field error

### Requirement: Allowed procurement decisions
The system SHALL restrict `ProcurementRecommendation.decision` to exactly one of the values
`approve`, `deny`, or `escalate`.

#### Scenario: Reject unsupported decision value
- **WHEN** `decision` is any value other than `approve`, `deny`, or `escalate`
- **THEN** validation fails with an allowed-values error

### Requirement: Non-empty recommendation rationale
The system SHALL require `ProcurementRecommendation.rationale` to be non-empty after whitespace
normalization.

#### Scenario: Reject blank rationale
- **WHEN** `rationale` is empty or whitespace-only
- **THEN** validation fails indicating rationale must be non-empty