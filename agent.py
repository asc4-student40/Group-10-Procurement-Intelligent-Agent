from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic_ai import Agent

from models import ProcurementRecommendation
from tools.budget import check_budget
from tools.policy_compliance import check_policy_compliance
from tools.risk_assessment import assess_risk
from tools.vendor_duplication import check_vendor_duplication

load_dotenv()

MODEL_NAME = os.getenv("PROCUREMENT_AGENT_MODEL") or os.getenv("AI_MODEL") or "openai:gpt-5.4-mini"

if MODEL_NAME.startswith("openai") and not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is required for OpenAI models")

if MODEL_NAME.startswith("anthropic") and not os.getenv("ANTHROPIC_API_KEY"):
    raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic models")

SYSTEM_PROMPT = (
    "You are the FedEx Procurement Intelligence Agent. "
    "For every request, call all four tools exactly once: check_budget, "
    "check_vendor_duplication, check_policy_compliance, and assess_risk. "
    "Use tool outputs as the only source of decision evidence. "
    "If any tool returns an error, you must escalate the request and explicitly "
    "reference the error and data loading failure details in the rationale. "
    "Use this strict priority when multiple checks fire: deny > escalate > "
    "approve. "
    "Rationale template is mandatory. "
    "Write the rationale as one paragraph of 2 to 4 complete sentences and never use bullet points. "
    "Sentence 1 must state the decision and name the specific check or checks that drove it "
    "(budget, vendor duplication, policy compliance, risk assessment, or tool error). "
    "Sentence 2 must include concrete evidence, including at least one exact amount, the vendor name, "
    "and any applicable policy IDs such as POL-001 through POL-008. "
    "If no policy was triggered, explicitly state that no policy ID was triggered. "
    "Additional sentences may summarize supporting checks or residual risk. "
    "Return only a ProcurementRecommendation-compatible output with decision "
    "in {approve, deny, escalate} and a non-empty rationale that cites key "
    "findings from budget, duplication, policy, risk, and any tool errors."
)

agent: Agent[None, ProcurementRecommendation] = Agent(
    model=MODEL_NAME,
    output_type=ProcurementRecommendation,
    system_prompt=SYSTEM_PROMPT,
    tools=[check_budget, check_vendor_duplication, check_policy_compliance, assess_risk],
)
