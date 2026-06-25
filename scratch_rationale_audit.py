from __future__ import annotations

import re

from agent import agent
from data.loader import load_requests

CHECK_KEYWORDS = [
    "budget",
    "vendor duplication",
    "policy",
    "risk",
    "tool error",
    "check_budget",
    "check_vendor_duplication",
    "check_policy_compliance",
    "assess_risk",
]


def _sentence_count(text: str) -> int:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return len([p for p in parts if p.strip()])


def _has_bullet_style(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return any(line.startswith("-") or line.startswith("*") or re.match(r"^\d+[.)]\s", line) for line in lines)


def _mentions_driving_check(text: str) -> bool:
    lower = text.lower()
    return any(keyword in lower for keyword in CHECK_KEYWORDS)


def _has_required_context(text: str, vendor_name: str) -> bool:
    has_amount = bool(re.search(r"\$\s?\d[\d,]*(?:\.\d{1,2})?", text))
    has_vendor = vendor_name.lower() in text.lower()
    has_policy_or_none = bool(re.search(r"POL-\d{3}", text)) or "no policy id" in text.lower()
    return has_amount and has_vendor and has_policy_or_none


def evaluate_rationale(rationale: str, vendor_name: str) -> list[str]:
    failures: list[str] = []

    if _has_bullet_style(rationale):
        failures.append("uses bullet/list formatting")

    sentence_count = _sentence_count(rationale)
    if sentence_count < 2 or sentence_count > 4:
        failures.append(f"sentence count is {sentence_count}, expected 2-4")

    if not _mentions_driving_check(rationale):
        failures.append("does not name specific driving check")

    if not _has_required_context(rationale, vendor_name):
        failures.append("missing amount/vendor/policy context")

    return failures


def main() -> int:
    requests = load_requests()
    failures_by_request: list[tuple[str, str, list[str], str]] = []

    for request in requests:
        result = agent.run_sync(str(request))
        recommendation = getattr(result, "output", None)
        if recommendation is None:
            recommendation = getattr(result, "data")

        rationale = recommendation.rationale
        failures = evaluate_rationale(rationale, request["vendor_name"])
        if failures:
            failures_by_request.append(
                (request["request_id"], recommendation.decision, failures, rationale)
            )

    print("Rationale Audit Summary")
    print("=" * 80)
    print(f"Total requests: {len(requests)}")
    print(f"Passing: {len(requests) - len(failures_by_request)}")
    print(f"Failing: {len(failures_by_request)}")

    if failures_by_request:
        print("\nFailures")
        print("-" * 80)
        for request_id, decision, failures, rationale in failures_by_request:
            print(f"{request_id} ({decision}): {', '.join(failures)}")
            print(f"Rationale: {rationale}")
            print("-" * 80)
        return 1

    print("\nAll rationales meet the template criteria.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
