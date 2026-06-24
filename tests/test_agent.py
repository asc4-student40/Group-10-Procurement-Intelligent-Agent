from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from data.loader import load_requests
from models import ProcurementRecommendation, PurchaseRequest
from tools.budget import check_budget
from tools.policy_compliance import check_policy_compliance
from tools.risk_assessment import assess_risk
from tools.vendor_duplication import check_vendor_duplication


def _get_request_by_id(request_id: str) -> PurchaseRequest:
    """Load and validate one request fixture by request_id."""
    for raw_request in load_requests():
        if raw_request.get("request_id") == request_id:
            return PurchaseRequest.model_validate(raw_request)

    raise AssertionError(f"Request fixture not found: {request_id}")


def _make_scripted_model(request: PurchaseRequest):
    """Create a deterministic model that calls tools then emits structured output."""

    def _scripted_model(messages: list[ModelMessage], agent_info: AgentInfo) -> ModelResponse:
        has_model_response = any(isinstance(message, ModelResponse) for message in messages)

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
                        ToolCallPart(
                            tool_name=tool.name,
                            args={"request": request.model_dump()},
                        )
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

        has_tool_error = any(
            isinstance(payload.get("error"), dict) for payload in tool_outputs.values()
        )

        policy_result = tool_outputs.get("check_policy_compliance", {})
        policy_violations = policy_result.get("violations", [])
        triggered_policy_ids = {
            violation.get("policy_id")
            for violation in policy_violations
            if isinstance(violation, dict)
        }

        budget_result = tool_outputs.get("check_budget", {})
        outside_budget = budget_result.get("within_budget") is False

        duplication_result = tool_outputs.get("check_vendor_duplication", {})
        duplication_deny = duplication_result.get("forced_decision") == "deny"

        risk_result = tool_outputs.get("assess_risk", {})
        compliance_flagged = risk_result.get("compliance_flag") is True

        if has_tool_error or compliance_flagged or "POL-006" in triggered_policy_ids:
            decision = "escalate"
        elif (
            "POL-004" in triggered_policy_ids
            or "POL-005" in triggered_policy_ids
            or "POL-008" in triggered_policy_ids
            or duplication_deny
            or outside_budget
        ):
            decision = "deny"
        elif "POL-003" in triggered_policy_ids:
            decision = "escalate"
        else:
            decision = "approve"

        rationale = (
            "Decision derived from budget, vendor duplication, policy compliance, and risk checks "
            f"for {request.request_id}."
        )

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

    return _scripted_model


async def _run_fixture_case(request_id: str):
    """Run one request fixture through a deterministic, tool-calling agent."""
    request = _get_request_by_id(request_id)

    test_agent: Agent[None, ProcurementRecommendation] = Agent(
        model=FunctionModel(function=_make_scripted_model(request)),
        output_type=ProcurementRecommendation,
        system_prompt="Evaluate procurement requests using the four tools.",
        tools=[check_budget, check_vendor_duplication, check_policy_compliance, assess_risk],
    )

    raw_result = await test_agent.run(f"Evaluate request {request.request_id}")
    recommendation = getattr(raw_result, "data", None)
    if recommendation is None:
        recommendation = getattr(raw_result, "output")

    # Ensure callers can consistently assert result.data across SDK versions.
    return SimpleNamespace(data=recommendation)


@pytest.mark.asyncio
async def test_agent_approve_req_001() -> None:
    """REQ-001 should be approved."""
    result = await _run_fixture_case("REQ-001")

    assert result.data.decision == "approve"
    assert result.data.rationale.strip()


@pytest.mark.asyncio
async def test_agent_deny_req_006_budget_overage() -> None:
    """REQ-006 should be denied due to budget overage on CC-003."""
    result = await _run_fixture_case("REQ-006")

    assert result.data.decision == "deny"
    assert result.data.rationale.strip()


@pytest.mark.asyncio
async def test_agent_policy_deny_req_009_catering_prohibition() -> None:
    """REQ-009 should be denied due to POL-004 catering prohibition."""
    result = await _run_fixture_case("REQ-009")

    assert result.data.decision == "deny"
    assert result.data.rationale.strip()


@pytest.mark.asyncio
async def test_agent_escalate_req_011_compliance_flagged_vendor() -> None:
    """REQ-011 should escalate for compliance-flagged vendor Vertex Consulting."""
    result = await _run_fixture_case("REQ-011")

    assert result.data.decision == "escalate"
    assert result.data.rationale.strip()