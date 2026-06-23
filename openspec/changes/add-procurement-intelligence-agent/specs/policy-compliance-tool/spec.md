## ADDED Requirements

### Requirement: Policy compliance input contract
The system SHALL provide a tool named check_policy_compliance that accepts a purchase request payload sufficient to evaluate every policy in mock_data/policies.json.

#### Scenario: Accept evaluable request
- **WHEN** request input includes fields required by policy rules (for example vendor, category, total_amount, cost_center_id, and quantity when applicable)
- **THEN** the tool evaluates the request against all policies

### Requirement: Evaluate all eight policies
The check_policy_compliance tool SHALL evaluate the request against all eight policies with policy IDs POL-001 through POL-008 from mock_data/policies.json.

#### Scenario: No policies violated
- **WHEN** request conditions do not violate any of POL-001 through POL-008
- **THEN** the tool returns an empty violations list

#### Scenario: Multiple policies violated
- **WHEN** request conditions violate one or more of POL-001 through POL-008
- **THEN** the tool returns one violation record per violated policy

### Requirement: Violation record structure
Each violation returned by check_policy_compliance SHALL include policy_id, violated_rule, and forced_decision.

#### Scenario: Return required fields for every violation
- **WHEN** a policy violation is detected
- **THEN** the violation record includes policy_id, violated_rule text describing the violated rule, and forced_decision

### Requirement: Forced decision constraints
The forced_decision field in each violation SHALL be either deny or escalate.

#### Scenario: Deny-only policy violation
- **WHEN** a violated policy mandates immediate rejection
- **THEN** forced_decision is deny

#### Scenario: Escalation-required policy violation
- **WHEN** a violated policy mandates review before approval
- **THEN** forced_decision is escalate

### Requirement: Policy-specific decision mapping
The tool SHALL apply the following minimum forced decision mapping for policy violations:
POL-001 deny, POL-002 escalate, POL-003 escalate, POL-004 deny, POL-005 deny, POL-006 escalate, POL-007 deny, POL-008 deny.

#### Scenario: Enforce policy mapping
- **WHEN** any listed policy is violated
- **THEN** forced_decision matches the policy-specific mapping above
