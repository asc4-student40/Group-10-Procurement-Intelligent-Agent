## ADDED Requirements

### Requirement: Risk assessment input contract
The system SHALL provide a tool named assess_risk that accepts vendor_id.

#### Scenario: Accept valid vendor identifier
- **WHEN** vendor_id is provided
- **THEN** the tool retrieves vendor attributes needed for risk evaluation

### Requirement: Risk profile output fields
The assess_risk tool SHALL return a risk profile containing compliance_flag status, contract_status, and computed risk_level.

#### Scenario: Return complete risk profile
- **WHEN** vendor data is available
- **THEN** output includes vendor_id, compliance_flag, contract_status, and risk_level

### Requirement: Risk level domain
The assess_risk tool SHALL restrict risk_level to one of low, medium, high, or critical.

#### Scenario: Enforce risk level value set
- **WHEN** risk_level is produced
- **THEN** value is exactly one of low, medium, high, or critical

### Requirement: Risk level computation rules
The assess_risk tool SHALL compute risk_level using vendor compliance flag status and contract status.

#### Scenario: Critical risk from compliance flag
- **WHEN** compliance_flag is true
- **THEN** risk_level is critical

#### Scenario: High risk from expired contract
- **WHEN** compliance_flag is false and contract_status is expired
- **THEN** risk_level is high

#### Scenario: Medium risk from no contract
- **WHEN** compliance_flag is false and contract_status is none
- **THEN** risk_level is medium

#### Scenario: Low risk from active compliant vendor
- **WHEN** compliance_flag is false and contract_status is active
- **THEN** risk_level is low
