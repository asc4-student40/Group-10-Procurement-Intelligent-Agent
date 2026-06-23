"""Load mock procurement datasets from the repository's mock_data directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Project root is one level up from data/loader.py.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MOCK_DATA_DIR = _PROJECT_ROOT / "mock_data"


def _load_json_list(filename: str) -> list[Any]:
    """Read a JSON file from mock_data and return it as a list.

    Args:
        filename: Name of the JSON file in the mock_data directory.

    Returns:
        The parsed JSON content as a list.

    Raises:
        FileNotFoundError: If the target mock data file does not exist.
        ValueError: If the JSON content is not a list.
    """
    path = _MOCK_DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Mock data file not found: {path}")

    parsed_data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed_data, list):
        raise ValueError(f"Expected list in {path}, got {type(parsed_data).__name__}")

    return parsed_data


def load_budgets() -> list[Any]:
    """Load budget records from mock_data/budgets.json as a list."""
    return _load_json_list("budgets.json")


def load_vendors() -> list[Any]:
    """Load vendor records from mock_data/vendors.json as a list."""
    return _load_json_list("vendors.json")


def load_policies() -> list[Any]:
    """Load policy records from mock_data/policies.json as a list."""
    return _load_json_list("policies.json")


def load_requests() -> list[Any]:
    """Load purchase request records from mock_data/requests.json as a list."""
    return _load_json_list("requests.json")
