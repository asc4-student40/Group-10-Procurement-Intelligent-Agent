from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from models import ProcurementRecommendation, PurchaseRequest
from tools.budget import check_budget
from tools.policy_compliance import check_policy_compliance
from tools.risk_assessment import assess_risk
from tools.vendor_duplication import check_vendor_duplication


def _make_error_aware_model(request: PurchaseRequest):
    """Create a deterministic model that escalates whenever any tool returns an error."""

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
                        ToolCallPart(tool_name=tool.name, args={"request": request.model_dump()})
                    )
                elif tool.name == "assess_risk":
                    call_parts.append(
                        ToolCallPart(tool_name=tool.name, args={"vendor_id": request.vendor_id})
                    )

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
            rationale = "Escalated due to tool failure: " + "; ".join(error_messages)
        else:
            decision = "approve"
            rationale = "Approved because no tool failures were returned."

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


def _run_error_case(request: PurchaseRequest) -> SimpleNamespace:
    """Run one request through the deterministic error-aware test agent."""
    test_agent: Agent[None, ProcurementRecommendation] = Agent(
        model=FunctionModel(function=_make_error_aware_model(request)),
        output_type=ProcurementRecommendation,
        system_prompt="If any tool fails, escalate and mention the failure in rationale.",
        tools=[check_budget, check_vendor_duplication, check_policy_compliance, assess_risk],
    )

    raw_result = test_agent.run_sync(f"Evaluate request {request.request_id}")
    recommendation = getattr(raw_result, "data", None)
    if recommendation is None:
        recommendation = getattr(raw_result, "output")

    return SimpleNamespace(data=recommendation)


def test_agent_handles_budget_loader_runtime_error_with_recommendation() -> None:
    """Budget loader RuntimeError should not crash; agent should escalate and mention failure."""
    request = PurchaseRequest(
        request_id="REQ-ERR-BUDGET-001",
        requestor="A. Tester",
        cost_center_id="CC-001",
        vendor_name="BlueSky Cloud Solutions",
        vendor_id="V-002",
        category="software_licenses",
        item_description="Error-path runtime failure test",
        quantity=1,
        unit_price=100.0,
        total_amount=100.0,
    )

    with patch("data.loader.load_budgets", side_effect=RuntimeError("budget loader failure")):
        with patch("tools.budget.load_budgets", side_effect=RuntimeError("budget loader failure")):
            with patch(
                "tools.policy_compliance.load_budgets",
                side_effect=RuntimeError("budget loader failure"),
            ):
                result = _run_error_case(request)

    assert result.data.decision == "escalate"
    assert result.data.rationale.strip()
    assert "failure" in result.data.rationale.lower()
    assert "budget" in result.data.rationale.lower()


def test_agent_escalates_for_unknown_vendor_id() -> None:
    """Unknown vendor_id should produce tool error and force escalation with clear rationale."""
    request = PurchaseRequest(
        request_id="REQ-ERR-VENDOR-001",
        requestor="A. Tester",
        cost_center_id="CC-001",
        vendor_name="Unknown Vendor LLC",
        vendor_id="V-999",
        category="software_licenses",
        item_description="Error-path unknown vendor test",
        quantity=1,
        unit_price=100.0,
        total_amount=100.0,
    )

    result = _run_error_case(request)

    assert result.data.decision == "escalate"
    assert result.data.rationale.strip()
    assert "unknown vendor" in result.data.rationale.lower()
