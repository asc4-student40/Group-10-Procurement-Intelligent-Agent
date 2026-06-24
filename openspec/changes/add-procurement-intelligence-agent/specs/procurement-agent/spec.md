## ADDED Requirements

### Requirement: Procurement agent input and output model contract
The system SHALL define the procurement agent interface in `agent.py` to accept a `PurchaseRequest`
input and produce a `ProcurementRecommendation` output, using the canonical model definitions in
`models.py`.

#### Scenario: Accept valid `PurchaseRequest` and return typed recommendation
- **WHEN** the agent receives a valid `PurchaseRequest`
- **THEN** it returns a `ProcurementRecommendation` with `request_id` copied from the input request

#### Scenario: Enforce allowed decision domain in output
- **WHEN** the agent produces a recommendation
- **THEN** `decision` is exactly one of `approve`, `deny`, or `escalate`

#### Scenario: Enforce non-empty recommendation rationale
- **WHEN** the agent returns a recommendation
- **THEN** `rationale` is non-empty after whitespace normalization

### Requirement: Procurement agent tool orchestration
The system SHALL orchestrate all four procurement tools for each evaluated request: `check_budget`,
`check_vendor_duplication`, `check_policy_compliance`, and `assess_risk`.

#### Scenario: Invoke all required tools per request
- **WHEN** the agent evaluates a request
- **THEN** it attempts all four tool calls before finalizing the recommendation

#### Scenario: Provide required tool inputs from request fields
- **WHEN** the agent calls each tool
- **THEN** it supplies `cost_center_id` and `total_amount` to `check_budget`, `vendor_id`, `category`,
  and `total_amount` to `check_vendor_duplication`, the full request payload to
  `check_policy_compliance`, and `vendor_id` to `assess_risk`

### Requirement: Decision priority order across combined check outcomes
The system SHALL resolve the final recommendation using deterministic priority when multiple checks
produce actionable signals.

#### Scenario: Deny has highest priority
- **WHEN** one or more tool outputs include a deny-triggering signal (for example a deny
  `forced_decision` from policy or vendor duplication)
- **THEN** the final recommendation decision is `deny`

#### Scenario: Escalate has second priority
- **WHEN** no deny-triggering signal is present and one or more tool outputs include an
  escalate-triggering signal
- **THEN** the final recommendation decision is `escalate`

#### Scenario: Approve only when no deny or escalate signals exist
- **WHEN** all tool outputs are non-blocking and contain no deny or escalate triggers
- **THEN** the final recommendation decision is `approve`

#### Scenario: Mixed deny and escalate signals resolve to deny
- **WHEN** deny and escalate signals are both present in the same evaluation
- **THEN** the final recommendation decision is `deny`

### Requirement: Error-aware recommendation behavior
The system SHALL handle tool errors explicitly and incorporate them into recommendation logic and
rationale.

#### Scenario: Structured tool error is captured
- **WHEN** a tool returns a structured `error` payload
- **THEN** the agent includes the error context in rationale evidence and treats the error as an
  escalation signal unless a deny decision is already required

#### Scenario: Unexpected tool exception is converted to controlled outcome
- **WHEN** a tool invocation raises an unexpected runtime exception
- **THEN** the agent catches the exception, records error details for rationale, and continues
  evaluation with remaining tools when possible

#### Scenario: Fail-safe behavior on error-only outcomes
- **WHEN** evaluation contains tool errors and no deny-triggering policy signal
- **THEN** the final recommendation decision is `escalate`

### Requirement: System prompt constraints for tool-driven structured output
The system SHALL define a system prompt that constrains the model to tool-driven, policy-aligned,
structured recommendation behavior.

#### Scenario: Prompt requires tool-first reasoning
- **WHEN** the model is generating a recommendation
- **THEN** the prompt instructs it to call and use all four tools before deciding

#### Scenario: Prompt enforces output contract discipline
- **WHEN** the model constructs output
- **THEN** the prompt instructs it to return only a `ProcurementRecommendation`-compatible result
  with valid decision values and non-empty rationale

#### Scenario: Prompt enforces evidence-based rationale
- **WHEN** the model writes rationale text
- **THEN** the prompt instructs it to summarize relevant findings from budget, vendor duplication,
  policy compliance, risk assessment, and any encountered errors

#### Scenario: Prompt enforces deterministic tie-breaking
- **WHEN** multiple tool findings conflict
- **THEN** the prompt instructs the model to apply priority order: `deny` before `escalate` before
  `approve`
