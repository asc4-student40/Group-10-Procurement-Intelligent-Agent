## ADDED Requirements

### Requirement: Budget check input contract
The system SHALL provide a tool named check_budget that accepts total_amount and cost_center_id from a purchase request.

#### Scenario: Accept valid check_budget input
- **WHEN** total_amount is a positive number and cost_center_id exists in budgets data
- **THEN** the tool evaluates the request against the matched cost center remaining amount

#### Scenario: Reject unknown cost center
- **WHEN** cost_center_id does not exist in budgets data
- **THEN** the tool reports a validation error indicating unknown cost center

### Requirement: POL-008 budget overage evaluation
The check_budget tool SHALL enforce POL-008 by comparing total_amount to the remaining field for the provided cost_center_id in mock_data/budgets.json.

#### Scenario: Request is within remaining budget
- **WHEN** total_amount is less than or equal to remaining for the matched cost center
- **THEN** the tool result is within_budget

#### Scenario: Request exceeds remaining budget
- **WHEN** total_amount is greater than remaining for the matched cost center
- **THEN** the tool result sets within_budget to false and includes a positive overage

### Requirement: Budget check structured output for valid cost center
The check_budget tool SHALL return a structured result for any valid cost_center_id including within_budget, remaining_budget, and overage.

#### Scenario: Return required output fields for valid cost center
- **WHEN** cost_center_id exists and check_budget completes evaluation
- **THEN** output includes within_budget, remaining_budget, and overage

#### Scenario: Within budget output shape
- **WHEN** total_amount is less than or equal to remaining_budget
- **THEN** within_budget is true and overage is 0

#### Scenario: Exceeding budget output shape
- **WHEN** total_amount is greater than remaining_budget
- **THEN** within_budget is false and overage equals total_amount minus remaining_budget

### Requirement: Structured error for unknown cost center
For unknown cost_center_id values, check_budget SHALL return a structured error response instead of a valid budget result.

#### Scenario: Unknown cost center returns structured error
- **WHEN** cost_center_id is not present in mock_data/budgets.json
- **THEN** output includes an error field with machine-readable context identifying the unknown cost center
