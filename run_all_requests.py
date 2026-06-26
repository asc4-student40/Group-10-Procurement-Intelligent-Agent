"""Run the agent against all 15 sample requests and compare to expected outcomes."""

from __future__ import annotations

import asyncio

from agent import agent
from data.loader import load_requests
from models import PurchaseRequest


async def main() -> None:
    requests_data = load_requests()

    results = {"approve": 0, "deny": 0, "escalate": 0, "mismatch": 0}

    for req_data in requests_data:
        expected = req_data["expected_outcome"]
        request = PurchaseRequest(
            **{k: v for k, v in req_data.items() if k not in {"expected_outcome", "outcome_reason"}}
        )
        result = await agent.run(str(request))

        recommendation = getattr(result, "data", None)
        if recommendation is None:
            recommendation = getattr(result, "output")

        decision = recommendation.decision
        match = "OK" if decision == expected else "X"

        if decision in results:
            results[decision] += 1
        else:
            results["mismatch"] += 1

        if decision != expected:
            results["mismatch"] += 1

        print(f"{match} {req_data['request_id']}: expected={expected}, got={decision}")
        print(f"  Rationale: {recommendation.rationale[:80]}...")
        print()

    print(
        "\nSummary: "
        f"approve={results['approve']} deny={results['deny']} "
        f"escalate={results['escalate']} mismatches={results['mismatch']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
