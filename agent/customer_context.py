"""
agent/customer_context.py — Customer Account Context Lookup.

Reads /data/customer_context.csv and returns customer plan, signup date,
and past ticket count for grounding triage decisions.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

DEFAULT_CSV_PATH = Path(os.getenv("CUSTOMER_CSV", "data/customer_context.csv"))


def get_customer_context(
    customer_id: str,
    csv_path: str | Path = DEFAULT_CSV_PATH,
) -> dict[str, Any] | None:
    """
    Look up customer profile metadata from the customer_context.csv file.

    Args:
        customer_id: Unique customer ID (e.g. "CUST-101").
        csv_path: Path to the customer context CSV file.

    Returns:
        Dict with keys: customer_id, plan, signup_date, past_ticket_count,
        or None if customer_id is not found.
    """
    path = Path(csv_path)
    if not path.exists():
        return None

    target_id = customer_id.strip().upper()

    with path.open(mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("customer_id", "").strip().upper() == target_id:
                try:
                    past_count = int(row.get("past_ticket_count", "0"))
                except ValueError:
                    past_count = 0

                return {
                    "customer_id": row.get("customer_id", target_id),
                    "plan": row.get("plan", "Free"),
                    "signup_date": row.get("signup_date", ""),
                    "past_ticket_count": past_count,
                }

    return None


# ---------------------------------------------------------------------------
# Self Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Testing Customer Context Lookup ===")

    # Test 1: Known Pro customer
    c101 = get_customer_context("CUST-101")
    print(f"CUST-101 lookup: {c101}")
    assert c101 is not None, "CUST-101 should exist"
    assert c101["plan"] == "Pro", "CUST-101 should be on Pro plan"
    assert c101["past_ticket_count"] == 2, "CUST-101 should have 2 past tickets"

    # Test 2: Known Team customer
    c104 = get_customer_context("CUST-104")
    print(f"CUST-104 lookup: {c104}")
    assert c104 is not None, "CUST-104 should exist"
    assert c104["plan"] == "Team", "CUST-104 should be on Team plan"
    assert c104["past_ticket_count"] == 4, "CUST-104 should have 4 past tickets"

    # Test 3: Known Free customer
    c105 = get_customer_context("CUST-105")
    print(f"CUST-105 lookup: {c105}")
    assert c105 is not None, "CUST-105 should exist"
    assert c105["plan"] == "Free", "CUST-105 should be on Free plan"

    # Test 4: Case-insensitive lookup
    c_lower = get_customer_context("cust-110")
    assert c_lower is not None and c_lower["customer_id"] == "CUST-110"

    # Test 5: Unknown customer
    unknown = get_customer_context("CUST-999")
    print(f"CUST-999 lookup: {unknown}")
    assert unknown is None, "CUST-999 should return None"

    print("All customer context tests passed successfully!")
