from __future__ import annotations

import re
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from data.loader import load_requests
from models import ProcurementRecommendation, PurchaseRequest
from tools.budget import check_budget
from tools.policy_compliance import check_policy_compliance
from tools.risk_assessment import assess_risk
from tools.vendor_duplication import check_vendor_duplication


def _load_request_by_id(request_id: str) -> PurchaseRequest | None:
    """Load a request fixture by ID and validate it."""
    for raw_request in load_requests():
        if raw_request.get("request_id") == request_id:
            return PurchaseRequest.model_validate(raw_request)
    return None


def _extract_request_id(messages: list[ModelMessage]) -> str | None:
    """Extract request_id from user text like: request_id='REQ-001'."""
    pattern = re.compile(r"request_id='([^']+)'")
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                content = getattr(part, "content", None)
                if isinstance(content, str):
                    match = pattern.search(content)
                    if match:
                        return match.group(1)
    return None


def _decision_from_tools(
    request: PurchaseRequest,
    tool_outputs: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    """Compute a deterministic decision and rationale from tool outputs."""
    errors: list[str] = []
    for tool_name, payload in tool_outputs.items():
        error_payload = payload.get("error")
        if isinstance(error_payload, dict):
            error_message = str(error_payload.get("message", "unknown tool error"))
            errors.append(f"{tool_name}: {error_message}")

    policy_result = tool_outputs.get("check_policy_compliance", {})
    policy_violations = policy_result.get("violations", [])
    policy_ids = {
        violation.get("policy_id")
        for violation in policy_violations
        if isinstance(violation, dict)
    }

    budget_result = tool_outputs.get("check_budget", {})
    outside_budget = budget_result.get("within_budget") is False or "POL-008" in policy_ids

    duplication_result = tool_outputs.get("check_vendor_duplication", {})
    duplication_forced_deny = (
        duplication_result.get("forced_decision") == "deny"
        or duplication_result.get("single_source_violation") is True
    )

    risk_result = tool_outputs.get("assess_risk", {})
    compliance_flagged = risk_result.get("compliance_flag") is True

    near_director_threshold = 47_500.0 <= request.total_amount < 50_000.0

    if errors:
        decision = "escalate"
        rationale = "Escalated due to tool failure: " + "; ".join(errors)
        return decision, rationale

    if compliance_flagged or "POL-006" in policy_ids:
        decision = "escalate"
    elif duplication_forced_deny or "POL-001" in policy_ids or "POL-004" in policy_ids or "POL-005" in policy_ids:
        decision = "deny"
    elif outside_budget:
        decision = "escalate" if near_director_threshold else "deny"
    elif "POL-003" in policy_ids or near_director_threshold:
        decision = "escalate"
    else:
        # POL-002 is treated as informational and does not force escalation.
        decision = "approve"

    policy_text = ", ".join(sorted(policy_ids)) if policy_ids else "none"
    rationale = (
        "Decision derived from budget, vendor duplication, policy compliance, and risk checks "
        f"for {request.request_id}. Triggered policy IDs: {policy_text}."
    )
    return decision, rationale


def _deterministic_model(messages: list[ModelMessage], agent_info: AgentInfo) -> ModelResponse:
    """Call all tools and emit a deterministic ProcurementRecommendation."""
    request_id = _extract_request_id(messages)
    request = _load_request_by_id(request_id) if request_id else None

    has_model_response = any(isinstance(message, ModelResponse) for message in messages)

    if request is None:
        output_tool = agent_info.output_tools[0]
        fallback_request_id = request_id or "UNKNOWN"
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name=output_tool.name,
                    args={
                        "request_id": fallback_request_id,
                        "decision": "escalate",
                        "rationale": (
                            "Escalated because the request payload could not be mapped to a known "
                            "request fixture for deterministic evaluation."
                        ),
                    },
                )
            ]
        )

    if not has_model_response:
        call_parts: list[ToolCallPart] = []
        for tool in agent_info.function_tools:
            if tool.name == "check_budget":
                call_parts.append(
                    ToolCallPart(
                        tool_name=tool.name,
                        args={
                            "cost_center_id": request.cost_center_id,
                            "total_amount": request.total_amount,
                        },
                    )
                )
            elif tool.name == "check_vendor_duplication":
                call_parts.append(
                    ToolCallPart(
                        tool_name=tool.name,
                        args={
                            "vendor_id": request.vendor_id,
                            "category": request.category,
                            "total_amount": request.total_amount,
                        },
                    )
                )
            elif tool.name == "check_policy_compliance":
                call_parts.append(
                    ToolCallPart(tool_name=tool.name, args={"request": request.model_dump()})
                )
            elif tool.name == "assess_risk":
                call_parts.append(
                    ToolCallPart(tool_name=tool.name, args={"vendor_id": request.vendor_id})
                )

        return ModelResponse(parts=call_parts)

    tool_outputs: dict[str, dict[str, Any]] = {}
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart) and isinstance(part.content, dict):
                    tool_outputs[part.tool_name] = part.content

    decision, rationale = _decision_from_tools(request, tool_outputs)

    output_tool = agent_info.output_tools[0]
    return ModelResponse(
        parts=[
            ToolCallPart(
                tool_name=output_tool.name,
                args={
                    "request_id": request.request_id,
                    "decision": decision,
                    "rationale": rationale,
                },
            )
        ]
    )


agent: Agent[None, ProcurementRecommendation] = Agent(
    model=FunctionModel(function=_deterministic_model),
    output_type=ProcurementRecommendation,
    system_prompt=(
        "Evaluate procurement requests using deterministic tool-first logic and produce "
        "a structured ProcurementRecommendation."
    ),
    tools=[check_budget, check_vendor_duplication, check_policy_compliance, assess_risk],
)
