import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
import httpx
from playwright.sync_api import sync_playwright, Page


def get_base_url() -> str:
    # The runner sets BASE_URL. When a student runs pytest by hand inside the skeleton,
    # there is no BASE_URL, so default to localhost.
    return os.environ.get("BASE_URL", "http://localhost:3000").rstrip("/")


@pytest.fixture(scope="session")
def base_url() -> str:
    return get_base_url()


@pytest.fixture(scope="session")
def app_dir() -> Path:
    # APP_DIR is provided by the runner; fallback for student-local runs.
    return Path(os.environ.get("APP_DIR", os.getcwd()))


@pytest.fixture(scope="session")
def http_client(base_url: str) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=10.0, follow_redirects=True)


@pytest.fixture()
def page(base_url: str):
    # Create a fresh browser page per test to avoid state bleed.
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        pg = context.new_page()
        # Do not navigate here; tests choose their route
        try:
            yield pg
        finally:
            context.close()
            browser.close()


# ---------- Helpers for spec-aligned calculations ----------

# Ambiguity A2 (rounding): We take Reading one, per ambiguity.md suggestion:
# - Compute proportional shares in integer cents by flooring, then distribute
#   the leftover cents to participants with the largest fractional remainders,
#   tie-breaking by person name ascending for determinism.

def _distribute_remainders(total_cents: int, weights: List[Tuple[str, float]]) -> Dict[str, int]:
    total_w = sum(w for _, w in weights) or 1.0
    # Raw shares and floors
    raw = [(name, (total_cents * w) / total_w) for name, w in weights]
    floors = {name: int(v // 1) for name, v in raw}
    allocated = sum(floors.values())
    remainder = total_cents - allocated
    if remainder <= 0:
        return floors
    # Sort by fractional part desc, then name asc for determinism
    fracs = sorted(((name, (val - int(val))) for name, val in raw), key=lambda t: (-t[1], t[0]))
    i = 0
    out = dict(floors)
    while remainder > 0 and fracs:
        name, _ = fracs[i % len(fracs)]
        out[name] = out.get(name, 0) + 1
        remainder -= 1
        i += 1
    return out


def compute_balances_from_expenses(expenses: List[Dict[str, Any]], include: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Compute per-person net cents (positive means owed to them; negative means they owe)
    using integer math and the remainder-distribution rule above. This mirrors the spec's
    intent and pins A2's reading explicitly for determinism.

    If include is provided, implement Ambiguity A1 reading one: drop expenses paid by
    excluded people and remove excluded participants from remaining expenses, then
    renormalise weights to the included set before splitting.
    """
    included: Optional[set] = set(include) if include is not None else None
    balances: Dict[str, int] = {}

    def add(name: str, delta: int) -> None:
        balances[name] = balances.get(name, 0) + delta

    for exp in expenses:
        payer: str = exp.get("paidBy")
        amount: int = int(exp.get("amountCents", 0))
        parts: List[Dict[str, Any]] = exp.get("participants", [])

        # Filter by include set per A1 reading one
        if included is not None:
            if payer not in included:
                continue
            fparts = [p for p in parts if p.get("person") in included]
            if not fparts:
                # No included participants; skip this expense entirely
                continue
            parts = fparts

        # Credit the payer with the full amount
        add(payer, amount)

        # Weights default to 1
        weights: List[Tuple[str, float]] = [
            (p.get("person"), float(p.get("weight", 1))) for p in parts
        ]
        owed_each: Dict[str, int] = _distribute_remainders(amount, weights)
        for person, share in owed_each.items():
            add(person, -share)

    # If include was given, ensure we only keep included keys
    if included is not None:
        balances = {k: balances.get(k, 0) for k in sorted(included)}
    return balances


def transfers_apply_to_balances(transfers: List[Dict[str, Any]]) -> Dict[str, int]:
    net: Dict[str, int] = {}
    for t in transfers:
        frm = t.get("from")
        to = t.get("to")
        amt = int(t.get("amountCents", 0))
        net[frm] = net.get(frm, 0) - amt
        net[to] = net.get(to, 0) + amt
    return net


def parse_cents_from_text(text: str) -> int:
    """
    Parse either a raw integer-cents string (e.g. "1234") or a formatted currency like
    "$12.34" or "-$1.05" into integer cents, matching W5 reading one for sign/cents.
    We strip all characters except digits and a leading minus, then interpret the last two
    digits as cents if a decimal point was present; otherwise read as integer cents.
    """
    s = text.strip()
    negative = s.startswith("-") or s.startswith("- $") or ("-" in s and s.index("-") < s.index("$") if "$" in s else s.startswith("-"))
    # Normalise
    s = s.replace(",", "")
    if "." in s:
        # Expect dollars.cents
        try:
            dollars_part, cents_part = s.replace("$", "").replace("-", "").split(".")
            cents_part = (cents_part + "00")[:2]
            total = int(dollars_part or "0") * 100 + int(cents_part)
        except Exception:
            # Fallback: strip non-digits
            digits = "".join(ch for ch in s if ch.isdigit())
            total = int(digits or "0")
    else:
        # Raw integer cents
        digits = "".join(ch for ch in s if ch.isdigit())
        total = int(digits or "0")
    return -total if negative and total != 0 else total


def format_money(cents: int) -> str:
    """
    Format integer cents to a currency string like "$12.34" with a leading "-" for negatives.
    This adopts W5 reading one explicitly.
    """
    sign = "-" if cents < 0 else ""
    c = abs(int(cents))
    dollars, rem = divmod(c, 100)
    return f"{sign}${dollars}.{rem:02d}"


def testid_selector(prefix: str, name: str) -> str:
    # Build a CSS attribute selector for a data-testid that embeds a raw name.
    # We assume raw fixture names (W1 reading one).
    esc = name.replace("\\", "\\\\").replace("\"", "\\\"")
    return f"[data-testid=\"{prefix}{esc}\"]"
