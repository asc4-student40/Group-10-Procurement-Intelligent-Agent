# Request Traceability Reference (Current Baseline)

This reference maps each sample request in mock_data/requests.json to current implementation
behavior in agent.py and the expected fixture outcome.

## Conventions

- All four tools are called for every request.
- check_budget returns within_budget, remaining_budget, and overage for valid cost centers.
- check_vendor_duplication returns deny trigger details for POL-001 conditions.
- check_policy_compliance returns violations for POL-001 through POL-008.
- assess_risk returns vendor compliance and contract risk.
- Deterministic tie-breaking is implementation-aligned:
  - tool error -> escalate
  - compliance flag or POL-006 -> escalate
  - POL-001/POL-004/POL-005 or duplication deny trigger -> deny
  - budget overage -> deny, except near director threshold band ($47,500 to <$50,000) -> escalate
  - POL-003 or near director threshold band -> escalate
  - POL-002 is informational for final decision tie-breaking
  - otherwise -> approve

## Traceability Matrix

| Request | Fixture Expected Outcome | Agent Baseline Decision | Primary Drivers |
| --- | --- | --- | --- |
| REQ-001 | approve | approve | Within budget, no deny trigger, POL-002 informational only |
| REQ-002 | approve | approve | Requested vendor is contracted, no POL-001 deny, POL-002 informational |
| REQ-003 | approve | approve | Within budget, no blocking policy/risk/duplication findings |
| REQ-004 | approve | approve | Within budget, no blocking findings |
| REQ-005 | approve | approve | Within budget, no deny trigger, POL-002 informational |
| REQ-006 | deny | deny | Budget overage with POL-008, below near-threshold escalation band |
| REQ-007 | deny | deny | Expired contract vendor triggers POL-005 deny |
| REQ-008 | deny | deny | POL-001 single-source deny trigger in office_supplies |
| REQ-009 | deny | deny | Catering prohibition triggers POL-004 deny |
| REQ-010 | escalate | escalate | Budget overage plus near-threshold escalation band |
| REQ-011 | escalate | escalate | Compliance flag and POL-006 escalation |
| REQ-012 | approve | approve | Within budget, no blocking findings |
| REQ-013 | approve | approve | Within budget, POL-002 informational only |
| REQ-014 | escalate | escalate | Near director threshold escalation band |
| REQ-015 | ambiguous | approve (current baseline) | No blocking policy/risk trigger; fixture marks scenario ambiguous by design |

## Session 4 / Session 5 Assertion Guidance

- Assert all four tools are invoked for every request.
- Assert known deny pathways: POL-001, POL-004, POL-005, and non-near-threshold budget overage.
- Assert known escalate pathways: tool errors, POL-006, and near-threshold cases.
- Assert POL-002 is treated as informational in final decision logic.
- Call out REQ-015 explicitly as ambiguous in fixture metadata but approve in the current baseline.
