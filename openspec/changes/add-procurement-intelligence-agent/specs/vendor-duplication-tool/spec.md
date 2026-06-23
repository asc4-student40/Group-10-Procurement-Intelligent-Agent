## ADDED Requirements

### Requirement: Vendor duplication input contract
The system SHALL provide a tool named check_vendor_duplication that accepts vendor_id, category, and total_amount.

#### Scenario: Accept valid vendor duplication input
- **WHEN** vendor_id and category are present and total_amount is non-negative
- **THEN** the tool evaluates active-contract conflicts for the category

### Requirement: Active contract conflict detection
The check_vendor_duplication tool SHALL determine whether FedEx has at least one different vendor with an active contract in the same category as the request.

#### Scenario: Conflicting active vendors exist
- **WHEN** one or more vendors other than the requested vendor have contract_status active in the same category
- **THEN** the tool marks duplication conflict as true

#### Scenario: No conflicting active vendors exist
- **WHEN** no other vendor has contract_status active in the same category
- **THEN** the tool marks duplication conflict as false

### Requirement: Conflict details in output
When duplication conflict is true, the tool SHALL return a list of conflicting vendor IDs and contract details for each conflict.

#### Scenario: Return full conflict detail payload
- **WHEN** duplication conflict is true
- **THEN** output includes conflicting_vendor_ids and conflicting_contracts with contract_id and contract_status per conflicting vendor

### Requirement: POL-001 deny trigger
The check_vendor_duplication tool SHALL reference POL-001 and identify deny-triggering single-source violations for requests above the POL-001 threshold amount.

#### Scenario: POL-001 violation triggers deny recommendation
- **WHEN** total_amount is greater than the POL-001 threshold and duplication conflict is true
- **THEN** output indicates single-source policy violation with forced_decision set to deny

#### Scenario: Threshold not met
- **WHEN** total_amount is less than or equal to the POL-001 threshold
- **THEN** output indicates POL-001 deny trigger is not activated
