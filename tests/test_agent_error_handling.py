from __future__ import annotations

from typing import Any

import pytest
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from models import ProcurementRecommendation
from tools.budget import check_budget
from tools.policy_compliance import check_policy_compliance
from tools.risk_assessment import assess_risk
from tools.vendor_duplication import check_vendor_duplication


def _scripted_model(messages: list[ModelMessage], agent_info: AgentInfo) -> ModelResponse:
    """Deterministic test model that calls tools first, then emits final structured output."""
    has_model_response = any(isinstance(message, ModelResponse) for message in messages)

    if not has_model_response:
        call_parts: list[ToolCallPart] = []
        for tool in agent_info.function_tools:
            if tool.name == "check_budget":
                call_parts.append(
                    ToolCallPart(
                        tool_name=tool.name,
                        args={"cost_center_id": "CC-001", "total_amount": 100.0},
                    )
                )
            elif tool.name == "check_vendor_duplication":
                call_parts.append(
                    ToolCallPart(
                        tool_name=tool.name,
                        args={"vendor_id": "V-002", "category": "software_licenses", "total_amount": 100.0},
                    )
                )
            elif tool.name == "check_policy_compliance":
                call_parts.append(
                    ToolCallPart(
                        tool_name=tool.name,
                        args={
                            "request": {
                                "request_id": "REQ-ERR-001",
                                "requestor": "A. Tester",
                                "cost_center_id": "CC-001",
                                "vendor_name": "BlueSky Cloud Solutions",
                                "vendor_id": "V-002",
                                "category": "software_licenses",
                                "item_description": "Error handling regression request",
                                "quantity": 1,
                                "unit_price": 100.0,
                                "total_amount": 100.0,
                            }
                        },
                    )
                )
            elif tool.name == "assess_risk":
                call_parts.append(ToolCallPart(tool_name=tool.name, args={"vendor_id": "V-002"}))

        return ModelResponse(parts=call_parts)

    error_messages: list[str] = []
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart) and isinstance(part.content, dict):
                    error_payload = part.content.get("error")
                    if isinstance(error_payload, dict):
                        error_message = str(error_payload.get("message", "unknown tool error"))
                        error_messages.append(f"{part.tool_name}: {error_message}")

    if error_messages:
        decision = "escalate"
        rationale = (
            "Escalated due to tool error and data loading failure: " + "; ".join(error_messages)
        )
    else:
        decision = "approve"
        rationale = "Approved because no tool errors were returned."

    output_tool = agent_info.output_tools[0]
    return ModelResponse(
        parts=[
            ToolCallPart(
                tool_name=output_tool.name,
                args={
                    "request_id": "REQ-ERR-001",
                    "decision": decision,
                    "rationale": rationale,
                },
            )
        ]
    )


def test_agent_escalates_and_mentions_data_loading_failure_on_budget_file_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If budget data loading fails, agent output should escalate and mention the failure."""

    def _raise_file_not_found() -> list[Any]:
        raise FileNotFoundError("budgets.json not found")

    # Required patch target from the task request.
    monkeypatch.setattr("data.loader.load_budgets", _raise_file_not_found)
    # Tool module imports load_budgets directly, so patch this binding too.
    monkeypatch.setattr("tools.budget.load_budgets", _raise_file_not_found)

    test_agent: Agent[None, ProcurementRecommendation] = Agent(
        model=FunctionModel(function=_scripted_model),
        output_type=ProcurementRecommendation,
        system_prompt=(
            "If any tool returns an error, escalate the request and reference the error in rationale."
        ),
        tools=[check_budget, check_vendor_duplication, check_policy_compliance, assess_risk],
    )

    result = test_agent.run_sync("Evaluate REQ-ERR-001")
    recommendation = getattr(result, "output", None)
    if recommendation is None:
        recommendation = getattr(result, "data")

    assert recommendation.decision == "escalate"
    assert recommendation.rationale.strip()
    assert "data loading failure" in recommendation.rationale.lower() or "not found" in recommendation.rationale.lower()
